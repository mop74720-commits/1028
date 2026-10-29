"""Spatial Taylor cache of one-form coefficients, NEVER of the physical field.

K=d(a0+b_cache), B=H_full+b_cache.f_full defines a different represented field.
The distinction from native time-jet truncation is measured separately. All
field/reference calls retain the original SO(3) mass and geometric inertia.
"""
from pathlib import Path
import json,time
import numpy as np
import torch


class OneFormCache:
    def __init__(self,center,values,jacobians,hessians,metadata=None):
        self.center=np.asarray(center)
        self.values=np.asarray(values)
        self.jacobians=np.asarray(jacobians)
        self.hessians=np.asarray(hessians)
        self.d=len(center);self.n=self.d//2;self.maximum_order=len(values)
        self.K0=np.block([[np.zeros((self.n,self.n)),-np.eye(self.n)],[np.eye(self.n),np.zeros((self.n,self.n))]])
        self.metadata=metadata or {}

    @classmethod
    def fit(cls,native,center,*,maximum_order=3,quadratic_through=2,progress=None):
        values=[];jac=[];hess=[];raw_hess=[];costs=[];x=torch.as_tensor(center,dtype=torch.float64)
        for k in range(1,maximum_order+1):
            fun=native.source_coefficient_function(k)
            for name,op in [('value',fun),('jacobian',torch.func.jacrev(fun))]+([('hessian',torch.func.jacfwd(torch.func.jacrev(fun)))] if k<=quadratic_through else []):
                if progress:progress(dict(status='running',order=k,derivative=name))
                start=time.perf_counter();a=op(x).detach().numpy();elapsed=time.perf_counter()-start
                costs.append(dict(order=k,derivative=name,seconds=elapsed,norm=float(np.linalg.norm(a))))
                if name=='value':values.append(a)
                elif name=='jacobian':jac.append(a)
                else:
                    raw_hess.append(a.copy())
                    absolute=float(np.max(np.abs(a-a.swapaxes(-1,-2))))
                    relative=float(np.linalg.norm(a-a.swapaxes(-1,-2))/max(np.linalg.norm(a),1e-300))
                    costs[-1].update(raw_hessian_antisymmetry_max=absolute,raw_hessian_antisymmetry_relative=relative)
                    if relative>1e-9:raise ValueError(f'Native coefficient Hessian is not symmetric: order={k}, relative={relative}')
                    hess.append((a+a.swapaxes(-1,-2))/2)
                if progress:progress(costs[-1])
            if k>quadratic_through:
                hess.append(np.zeros((native.d,native.d,native.d)));raw_hess.append(hess[-1].copy())
        result=cls(center,values,jac,hess,dict(spatial_degree=[2 if k<=quadratic_through else 1 for k in range(1,maximum_order+1)],costs=costs,
                source='Exact AD of source-gauge Lie coefficients on full original ROM at center',
                original_field_not_cached=True,represented_field_approximate=True,mass_frozen=False,
                high_order_ad_backend=native.ad_backend,approximation='only one-form coefficient spatial Taylor cache'))
        result.raw_hessians=np.asarray(raw_hess)
        return result

    def save(self,path):
        np.savez_compressed(path,center=self.center,values=self.values,jacobians=self.jacobians,hessians=self.hessians,
                            raw_hessians=getattr(self,'raw_hessians',self.hessians),metadata=json.dumps(self.metadata))

    @classmethod
    def load(cls,path):
        data=np.load(path)
        return cls(data['center'],data['values'],data['jacobians'],data['hessians'],json.loads(str(data['metadata'])))

    def coefficient_data(self,z):
        delta=np.asarray(z)-self.center
        values=self.values+np.einsum('rij,j->ri',self.jacobians,delta)+.5*np.einsum('rijk,j,k->ri',self.hessians,delta,delta)
        jac=self.jacobians+np.einsum('rijk,k->rij',self.hessians,delta)
        return values,jac

    def b_tensor(self,z,t,order):
        delta=z-torch.as_tensor(self.center)
        values=torch.as_tensor(self.values[:order])+torch.einsum('rij,j->ri',torch.as_tensor(self.jacobians[:order]),delta)+.5*torch.einsum('rijk,j,k->ri',torch.as_tensor(self.hessians[:order]),delta,delta)
        return torch.einsum('r,ri->i',t**torch.arange(1,order+1,dtype=z.dtype),values)

    def data(self,z,t,order):
        values,jac=self.coefficient_data(z);powers=t**np.arange(1,order+1)
        timepowers=np.arange(1,order+1)*t**np.arange(order)
        b=np.einsum('r,ri->i',powers,values[:order])
        Db=np.einsum('r,rij->ij',powers,jac[:order])
        Hb=np.einsum('r,rijk->ijk',powers,self.hessians[:order])
        bt=np.einsum('r,ri->i',timepowers,values[:order])
        Dbt=np.einsum('r,rij->ij',timepowers,jac[:order])
        K=self.K0+Db.T-Db
        DK=Hb.swapaxes(0,1)-Hb
        Kt=Dbt.T-Dbt
        Hbt=np.einsum('r,rijk->ijk',timepowers,self.hessians[:order])
        DKt=Hbt.swapaxes(0,1)-Hbt
        return dict(b=b,Db=Db,Hb=Hb,bt=bt,Dbt=Dbt,K=K,DK=DK,Kt=Kt,DKt=DKt)

    def ball_bounds(self,t,order,radius):
        a=self.data(self.center,t,order)
        deltaK=np.linalg.norm(a['K']-self.K0,2)+radius*np.sqrt(sum(np.linalg.norm(a['DK'][:,:,k],2)**2 for k in range(self.d)))
        # Frobenius norm of the bilinear tensor is a safe Euclidean upper bound.
        b_bound=np.linalg.norm(a['b'])+np.linalg.norm(a['Db'],2)*radius+.5*np.linalg.norm(a['Hb'])*radius**2
        return dict(radius=radius,K_perturbation_upper_bound=float(deltaK),
                    all_lambda_min_singular_lower_bound=float(1-deltaK),
                    auxiliary_speed_upper_bound=float(b_bound/(1-deltaK)) if deltaK<1 else None,
                    interpretation='Analytic sufficient bound on the specified Euclidean ball for the cached polynomial; coefficients evaluated in floating point, not an interval certificate.')


class CachedRepresentedField:
    def __init__(self,native,cache,order):
        self.native,self.cache,self.order=native,cache,order
        self.calls=0;self.seconds=0.

    def evaluate(self,t,z,diagnostics=False):
        start=time.perf_counter();self.calls+=1
        f,A,force=self.native.field_and_jacobian(z)
        a=self.cache.data(z,t,self.order)
        source_residual=a['bt']+a['Db']@f+A.T@a['b']+np.r_[force,np.zeros(self.native.n)]
        error=np.linalg.solve(a['K'],source_residual)
        out=f+error
        self.seconds+=time.perf_counter()-start
        if not diagnostics:return out
        transport=a['Kt']+np.einsum('ijk,k->ij',a['DK'],f)+A.T@a['K']+a['K']@A
        closure=a['DK']+a['DK'].transpose(1,2,0)+a['DK'].transpose(2,0,1)
        return out,dict(time=t,representation_residual_2=float(np.linalg.norm(source_residual)),
                        original_field_error_2=float(np.linalg.norm(error)),
                        original_transport_compatibility_2=float(np.linalg.norm(transport,2)),
                        closure_max_component=float(np.max(np.abs(closure))),
                        K_min_singular=float(np.linalg.svd(a['K'],compute_uv=False)[-1]),K_condition=float(np.linalg.cond(a['K'])),
                        state_distance_from_cache_center=float(np.linalg.norm(np.asarray(z)-self.cache.center)),
                        e_B=(-source_residual).tolist(),field_error=error.tolist())

    __call__=evaluate

    def jacobian(self,t,z):
        """Actual represented-field derivative, using full original H and Df."""
        a=self.cache.data(z,t,self.order)
        fa=self(t,z)
        def B(x):
            return self.native.base.hamiltonian_tensor(x)+torch.dot(self.cache.b_tensor(x,t,self.order),self.native.field_tensor(x))
        HessB=torch.func.jacfwd(torch.func.grad(B))(torch.as_tensor(z,dtype=torch.float64)).detach().numpy()
        return np.linalg.solve(a['K'],HessB+a['Dbt']-np.einsum('ijk,j->ik',a['DK'],fa))
