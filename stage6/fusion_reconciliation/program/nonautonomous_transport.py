"""Nonautonomous one-form jets on the actual full-coil 24D variable-mass ROM.

Only a known smooth collocated gain is varied. Its currents are actual inputs;
there is no arbitrary generalized-force actuator and no exact-flow oracle.
The autonomous stage5 Moser/cache implementations are reused unchanged.
"""
from pathlib import Path
import math
import hashlib
import json
import sys
import time
import numpy as np
import torch

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'stage5/program'))
from coil_rom import CoilROM
from transport_native import NativeTransport
from transport_cache import OneFormCache
from moser_chart import MoserChart


class TimeGainCoilTransport(NativeTransport):
    def __init__(self,base=None,*,amplitude=.25,frequency=200.):
        super().__init__(base=CoilROM() if base is None else base,kind='time_gain_fullcoil',ad_backend='inverse')
        if abs(amplitude)>=1 or frequency<0:raise ValueError('Positive gain and nonnegative frequency required')
        self.amplitude=float(amplitude);self.frequency=float(frequency)
        self._time_coefficients=[lambda z:torch.zeros_like(z)]

    def gain_factor(self,t):
        return 1+self.amplitude*torch.sin(self.frequency*torch.as_tensor(t,dtype=torch.float64))

    def gain_coefficient(self,k):
        if k==0:return 1.
        return self.amplitude*self.frequency**k*(0.,1.,0.,-1.)[k%4]/math.factorial(k)

    def drag_tensor(self,z,*,numeric=False):
        G=self.base.current_port_tensor(z[:self.n])
        velocity=(torch.func.grad(self.base.hamiltonian_tensor)(z) if numeric else self._gradH(z))[self.n:]
        return -self.base.collocated_gain*G@(G.T@velocity)

    def force_tensor(self,z):
        return self.drag_tensor(z)

    def force_coefficient(self,z,k):
        coefficient=self.gain_coefficient(k)
        return torch.zeros_like(z[:self.n]) if coefficient==0 else coefficient*self.drag_tensor(z)

    def field_coefficient_function(self,k):
        if k==0:return lambda z:self.J@self._gradH(z)+torch.cat((torch.zeros_like(z[:self.n]),self.drag_tensor(z)))
        return lambda z:self.J.new_zeros(self.d)+torch.cat((torch.zeros_like(z[:self.n]),self.force_coefficient(z,k)))

    def field_tensor_at(self,t,z):
        return self.J@self._gradH(z)+torch.cat((torch.zeros_like(z[:self.n]),self.gain_factor(t)*self.drag_tensor(z)))

    def field_tensor(self,z):
        return self.field_tensor_at(0.,z)

    @staticmethod
    def lie_with_field(alpha,field,z):
        value=field(z)
        tangent=torch.func.jvp(alpha,(z,),(value,))[1]
        _,pullback=torch.func.vjp(field,z)
        return tangent+pullback(alpha(z))[0]

    def source_coefficient_function(self,order):
        """b_(m+1)=-(R_m.dQ+sum_(r+s=m,r>=1) L_f_s b_r)/(m+1).

        Powers of time, with factorials already contained in f_s and b_r.
        Expansion origin is fixed at 0; no unproved per-step resetting.
        """
        while len(self._time_coefficients)<=order:
            k=len(self._time_coefficients);m=k-1
            previous=tuple(self._time_coefficients)
            def coefficient(z,k=k,m=m,previous=previous):
                value=torch.cat((self.force_coefficient(z,m),torch.zeros_like(z[:self.n])))
                for r in range(1,m+1):
                    value=value+self.lie_with_field(previous[r],self.field_coefficient_function(m-r),z)
                return -value/k
            self._time_coefficients.append(coefficient)
        return self._time_coefficients[order]

    def field(self,z,t=0.):
        gain=self.base.collocated_gain*float(self.gain_factor(t))
        return self.base.feedback_field(z,gain=gain)

    def field_and_jacobian_at(self,t,z):
        gain=self.base.collocated_gain*float(self.gain_factor(t))
        f=self.base.feedback_field(z,gain=gain)
        A=self.base.feedback_jacobian(z,gain=gain)
        force=float(self.gain_factor(t))*self.drag_tensor(torch.as_tensor(z),numeric=True).detach().numpy()
        return f,A,force

    def field_and_jacobian(self,z):
        return self.field_and_jacobian_at(0.,z)

    def currents(self,t,z):
        return self.base.collocated_current_tensor(torch.as_tensor(z),gain=self.base.collocated_gain*float(self.gain_factor(t))).detach().numpy()

    def metadata(self):
        return dict(base=self.base.metadata(),time_gain=dict(amplitude=self.amplitude,frequency_tau=self.frequency,
                    frequency_rad_per_second=self.frequency*self.base.rom.omega0,formula='kappa(tau)=kappa0*(1+a*sin(Omega*tau))'),
                    expansion_origin_tau=0.,coefficient_convention='time powers; derivatives divided by factorial',
                    exact_flow_used=False,mass_frozen=False,high_order_ad_backend=self.ad_backend,
                    boundary='Smooth feedback only; no limiter, sampled controller, blood-flow calibration or contact switching. Current/field bounds sampled separately.')


class TimeGainRepresentedField:
    """Use cached a(t,z) but exact full f(t,z), D_zf and fixed-bias H."""
    def __init__(self,native,cache,order):
        self.native,self.cache,self.order=native,cache,order
        self.calls=0;self.seconds=0.

    def evaluate(self,t,z,diagnostics=False):
        started=time.perf_counter();self.calls+=1
        f,A,R=self.native.field_and_jacobian_at(t,z);a=self.cache.data(z,t,self.order)
        source=a['bt']+a['Db']@f+A.T@a['b']+np.r_[R,np.zeros(self.native.n)]
        delta=np.linalg.solve(a['K'],source);fa=f+delta
        self.seconds+=time.perf_counter()-started
        if not diagnostics:return fa
        transport=a['Kt']+np.einsum('ijk,k->ij',a['DK'],f)+A.T@a['K']+a['K']@A
        closure=a['DK']+a['DK'].transpose(1,2,0)+a['DK'].transpose(2,0,1)
        return fa,dict(original_field_error_2=float(np.linalg.norm(delta)),representation_residual_2=float(np.linalg.norm(source)),
                       original_transport_compatibility_2=float(np.linalg.norm(transport,2)),closure_max=float(np.max(abs(closure))),
                       K_min_singular=float(np.linalg.svd(a['K'],compute_uv=False)[-1]),K_condition=float(np.linalg.cond(a['K'])),
                       field_error=delta.tolist(),e_B=(-source).tolist())

    __call__=evaluate

    def jacobian(self,t,z):
        a=self.cache.data(z,t,self.order);fa=self(t,z)
        def B(x):
            return self.native.high_order_hamiltonian(x)+torch.dot(self.cache.b_tensor(x,t,self.order),self.native.field_tensor_at(t,x))
        hessian=torch.func.jacfwd(torch.func.grad(B))(torch.as_tensor(z)).detach().numpy()
        return np.linalg.solve(a['K'],hessian+a['Dbt']-np.einsum('ijk,j->ik',a['DK'],fa))


def inherit_second_order_cache(native):
    """Reuse the independently verified stage5 autonomous spatial coefficients.

    At the fixed origin sin(0)=0, f0 and b1 are unchanged. Exactly
    b2_time=b2_autonomous+(a*Omega/2)*b1. Only value/Jacobian are retained
    for b2, as declared in the inherited [2,1] spatial Taylor truncation.
    Actual native coefficients are independently checked by the experiment.
    """
    folder=ROOT/'stage5/results/transport/fullcoil_collocated'
    report=json.loads((folder/'inverse_verified.json').read_text())
    if report['status']!='completed':raise ValueError('No accepted stage5 cache')
    source=next(folder.glob(f"cache_*_{report['cache_fingerprint'][:12]}.npz"))
    cache=OneFormCache.load(source)
    old=cache.metadata['fingerprint_payload']
    if old['sources']['coil_rom.py']!=hashlib.sha256((ROOT/'stage5/program/coil_rom.py').read_bytes()).hexdigest():
        raise ValueError('Coil source changed; reuse needs an independent revalidation')
    if abs(old['gain']-native.base.collocated_gain)>1e-13:
        raise ValueError('Different collocated gain')
    if np.max(abs(cache.center-native.base.initial_state(.01)))>1e-15:
        raise ValueError('Different cache origin')
    values=cache.values.copy();jac=cache.jacobians.copy()
    factor=native.amplitude*native.frequency/2
    values[1]+=factor*values[0];jac[1]+=factor*jac[0]
    result=OneFormCache(cache.center,values,jac,cache.hessians.copy(),dict(
        source_cache=str(source.relative_to(ROOT)),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        old_metadata=cache.metadata,spatial_degree=[2,1],new_model=native.metadata(),
        coefficient_identity='b1_new=b1_old; b2_new=b2_old+(amplitude*frequency/2)*b1_old',
        scope='Reused spatial one-form jets only. Exact full f(t,z), M(Q) and feedback are recomputed at all states.'))
    return result,cache
