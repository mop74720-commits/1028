"""Independent, read-only check of the S5 full complex network/ideal ROM interface.

No training and no full-coil target substitution. All new output stays in this
bridge directory. Existing S5 independent test/OOD samples retain their meaning.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import platform
import sys
import time

import numpy as np
from scipy.optimize import root
import torch

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'1025_bridges/01_chnn_to_birkhoff'
sys.path.insert(0,str(ROOT/'stage5/program'))
from learning_models import RodROM,make_model,predict,real_parameter_count

CHECKPOINT=ROOT/'stage5/results/learning/S5_L01_complex_hidden_seed51001.pt'
DATA=ROOT/'stage5/results/learning/S5_L01_independent_evaluation_data.npz'
PROTOCOL=ROOT/'stage5/results/learning/S5_L01_protocol.json'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class FrozenIdealNetwork:
    """The already trained scalar energy, differentiated in physical canonical z."""
    def __init__(self,rom=None):
        self.rom=RodROM() if rom is None else rom
        self.n=self.rom.n
        payload=torch.load(CHECKPOINT,map_location='cpu',weights_only=False)
        assert payload['kind']=='complex_hidden' and payload['seed']==51001 and payload['n']==12
        freeze=json.loads((ROOT/'stage5/results/learning/S5_L01_freeze_before_test.json').read_text())
        entry=next(x for x in freeze['records'] if x['kind']=='complex_hidden' and x['seed']==51001)
        assert sha(CHECKPOINT)==entry['checkpoint_sha256']
        self.payload=payload
        self.amplitude=payload['amplitude']
        self.D=torch.cat((torch.sqrt(self.rom.nu),torch.sqrt(self.rom.nu)))/self.amplitude
        declared=torch.tensor(json.loads(PROTOCOL.read_text())['scales']['coordinate_D'])
        assert torch.equal(self.D,declared)
        self.net=make_model(payload['kind'],self.n,self.amplitude,payload['output_scale'],payload['seed'])
        self.net.load_state_dict(payload['state_dict']);self.net.eval()
        for parameter in self.net.parameters():parameter.requires_grad_(False)
        eye=torch.eye(self.n);zero=torch.zeros_like(eye)
        self.J=torch.cat((torch.cat((zero,eye),1),torch.cat((-eye,zero),1)),0)

    def h(self,z):
        x=self.D*z
        return .5*self.amplitude**2*(x*x).sum()+self.net(x[None,:])[0]

    def truth(self,z):return self.rom.hamiltonian(z[None,:])[0]
    def gradient(self,z):return torch.func.grad(self.h)(z)
    def field(self,z):return self.J@self.gradient(z)
    def force(self,z):
        # Exactly NativeTransport(kind='state_dependent'), unchanged rates,
        # momentum scale and cross coupling; not a physiological calibration.
        q,p=z[:self.n],z[self.n:]
        rates=torch.linspace(.1,.3,self.n)*(1+.15*torch.tanh(q/.02))
        cross=torch.cos(.7*torch.arange(self.n,dtype=z.dtype));cross=cross/torch.linalg.vector_norm(cross)
        return -rates*(p+.1*p**3/.002**2)-.04*cross*torch.dot(cross,p)

    def a1_general(self,z):
        def scalar(y):return self.h(y)-torch.dot(y[self.n:],self.gradient(y)[self.n:])
        return torch.func.grad(scalar)(z)-torch.cat((self.force(z),torch.zeros(self.n)))

    def a1_mechanical(self,z):
        def scalar(y):
            y0=torch.cat((y[:self.n],torch.zeros(self.n)))
            return 2*self.h(y0)-self.h(y)
        return torch.func.grad(scalar)(z)-torch.cat((self.force(z),torch.zeros(self.n)))


def evaluate_hpp(model,z):
    q,p=z[:model.n],z[model.n:]
    energy=lambda momentum:model.h(torch.cat((q,momentum)))
    hpp=torch.autograd.functional.hessian(energy,p).detach().numpy()
    eig,vec=np.linalg.eigh(hpp)
    v=torch.tensor(vec[:,0]);eps=2e-5/max(float(torch.linalg.vector_norm(model.D[model.n:]*v)),1.)
    fd=float((energy(p+eps*v)-2*energy(p)+energy(p-eps*v))/eps**2)
    return dict(min_eigenvalue=float(eig[0]),max_eigenvalue=float(eig[-1]),
        min_singular=float(np.linalg.svd(hpp,compute_uv=False)[-1]),condition=float(np.linalg.cond(hpp)),
        symmetry_max=float(np.max(abs(hpp-hpp.T))),eigen_direction_fd=fd,fd_step=eps,
        positive_definite_sample=bool(eig[0]>0)),hpp,vec[:,0]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',default='network_checks');args=parser.parse_args()
    out=BASE/'results';out.mkdir(parents=True,exist_ok=True)
    dest=out/f'{args.run_id}.json'
    if dest.exists():raise FileExistsError('Choose a fresh run-id; previous evidence is preserved.')
    torch.set_default_dtype(torch.float64);torch.set_num_threads(1)
    start=time.perf_counter();model=FrozenIdealNetwork();raw=np.load(DATA)
    assert raw['test_x'].shape==(512,24) and raw['OOD_x'].shape==(256,24)
    arrays={};report=dict(status='running',command=sys.argv,started_utc=datetime.now(timezone.utc).isoformat(),
        environment=dict(python=sys.version,numpy=np.__version__,torch=torch.__version__,platform=platform.platform(),threads=1),
        inputs={str(p.relative_to(ROOT)):sha(p) for p in [CHECKPOINT,DATA,PROTOCOL]},
        source_sha256={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'stage5/program/learning_models.py',
            ROOT/'stage5/program/run_learning_research.py',ROOT/'stage3/source_inputs/starter/stage2/program/learning/run_learning.py',
            ROOT/'stage3/source_inputs/starter/stage2/program/learning/rod_rom.py']},
        object=dict(phase_dimension=24,quadrature_elements=20,energy=model.payload['target'],
            training_target='h_res=h_ideal-h0; h0=.5 amplitude^2 |Dz|^2; not full dynamics or Hcoil',
            amplitude=model.amplitude,normalization='x=Dz; grad_z=D grad_x; D is not a canonical coordinate change',
            complex_parameters=True,real_parameter_count=real_parameter_count(model.net),
            real_scalar_output=True,activation='split real/imaginary tanh, conjugate inputs and real output; real analytic, not holomorphic in xi alone',
            inherited_drag='same NativeTransport state_dependent canonical force; not blood/contact',
            mass='truth recomputes full M(q); no learned mechanical-mass assertion'),splits={},hpp_samples=[],witnesses=[])
    original=json.loads((ROOT/'stage5/results/learning/S5_L01_results.json').read_text())
    old=next(r for r in original['models'] if r['kind']=='complex_hidden' and r['seed']==51001)
    for split in ['test','OOD']:
        x=raw[split+'_x'];ph,pg=predict(model.net,x)
        truthg=(raw[split+'_g_res']+model.amplitude**2*x)*model.D.numpy()
        learng=(pg+model.amplitude**2*x)*model.D.numpy()
        err=learng-truthg
        deltaf=err@model.J.numpy().T
        old_error=old[split]['canonical_gradient_and_tau_field_relative_l2']
        new_error=float(np.linalg.norm(err)/np.linalg.norm(truthg))
        assert abs(new_error-old_error)<5e-13
        report['splits'][split]=dict(samples=len(x),canonical_field_relative_l2=new_error,
            field_max_sample_error=float(np.max(np.linalg.norm(deltaf,axis=1))),
            energy_rmse=float(np.sqrt(np.mean((ph-raw[split+'_h_res'])**2))),
            original_report_field_relative_l2=old_error,exact_prior_restored=True)
        arrays[split+'_x']=x;arrays[split+'_field_error']=deltaf
        # Detecting power sign only uses supplied points, never creates a new
        # force law to force a favorable mechanical interpretation.
        z=x/model.D.numpy();force=torch.stack([model.force(torch.tensor(zz)) for zz in z]).detach().numpy()
        truth_power=np.einsum('bi,bi->b',truthg[:,12:],force)
        learned_power=np.einsum('bi,bi->b',learng[:,12:],force)
        report['splits'][split]['drag_power']=dict(truth_min=float(truth_power.min()),truth_max=float(truth_power.max()),
            learned_min=float(learned_power.min()),learned_max=float(learned_power.max()),
            truth_positive_count=int(np.sum(truth_power>0)),learned_positive_count=int(np.sum(learned_power>0)),
            warning='Finite sample signs only; R=-D(Q,P)P is not automatically dissipative for arbitrary Hhat or arbitrary variable-mass H.')
        arrays[split+'_truth_drag_power']=truth_power;arrays[split+'_learned_drag_power']=learned_power
        for index in original['evaluation_indices'][split]:
            zz=torch.tensor(z[index]);diagnostic,hpp,direction=evaluate_hpp(model,zz)
            oldrow=next(v for v in old[split]['Hpp_Legendre']['rows'] if v['sample_index']==index)
            assert abs(diagnostic['min_eigenvalue']-oldrow['minimum_eigenvalue'])<5e-10
            report['hpp_samples'].append(dict(split=split,index=index,**diagnostic,
                prior_truth_velocity_inverse_status=oldrow['root_success'],
                prior_truth_velocity_inverse_residual=oldrow['root_residual']))
            arrays[f'{split}_{index}_Hpp']=hpp;arrays[f'{split}_{index}_min_eigenvector']=direction
    # Fresh full geometric gradients at existing states independently verify
    # that saved labels identify the claimed ideal Hamiltonian.
    for index in [0,146,219,292]:
        z=torch.tensor(raw['test_x'][index]/model.D.numpy())
        truth_grad=torch.func.grad(model.truth)(z)
        saved=(raw['test_g_res'][index]+model.amplitude**2*raw['test_x'][index])*model.D.numpy()
        learned=model.gradient(z)
        xx=(z*model.D).detach().requires_grad_(True)
        hx=.5*model.amplitude**2*xx.square().sum()+model.net(xx[None,:])[0]
        gx=torch.autograd.grad(hx,xx)[0]
        chain=float(torch.linalg.vector_norm(learned-model.D*gx))
        direction=torch.cos(torch.arange(24,dtype=torch.float64)+.2)
        direction=direction/torch.linalg.vector_norm(direction)
        eps=1e-5/float(torch.linalg.vector_norm(model.D*direction))
        first_fd=float((model.h(z+eps*direction)-model.h(z-eps*direction))/(2*eps))
        hessian=torch.autograd.functional.hessian(model.h,z)
        hessian_direction_fd=(model.gradient(z+eps*direction)-model.gradient(z-eps*direction))/(2*eps)
        a1=model.a1_general(z);a1wrong=model.a1_mechanical(z)
        f=model.field(z)+torch.cat((torch.zeros(12),model.force(z)))
        a0=torch.cat((z[12:],torch.zeros(12)))
        # Complex conjugate negative views lack the vmap rule in torch 2.5.1.
        # Explicit reverse rows retain the exact network and avoid batching.
        Df=torch.func.jacrev(lambda yy:model.field(yy)+torch.cat((torch.zeros(12),model.force(yy))),chunk_size=1)(z)
        Lie=torch.cat((f[12:],torch.zeros(12)))+Df.T@a0
        report['witnesses'].append(dict(split='test',index=index,
            truth_fresh_gradient_vs_saved_max=float(np.max(abs(truth_grad.detach().numpy()-saved))),
            normalization_chain_residual=chain,
            forgetting_D_gradient_error=float(torch.linalg.vector_norm(learned-gx)),
            directional_energy_fd_error=abs(first_fd-float(torch.dot(learned,direction))),fd_step=eps,
            hessian_direction_fd_error=float(torch.linalg.vector_norm(hessian_direction_fd-hessian@direction)),
            full_hessian_symmetry_max=float(torch.max(abs(hessian-hessian.T))),
            conservative_power_residual=abs(float(torch.dot(learned,model.field(z)))),
            general_a1_vs_negative_Lie=float(torch.linalg.vector_norm(a1+Lie)),
            mechanical_a1_wrong_norm=float(torch.linalg.vector_norm(a1wrong-a1))))
        arrays[f'witness_test_{index}_z']=z.numpy()
    origin=torch.zeros(24)
    origin_hess=torch.autograd.functional.hessian(model.h,origin).detach().numpy()
    prior=np.diag(np.r_[model.rom.nu.numpy(),model.rom.nu.numpy()])
    report['origin']=dict(H=float(model.h(origin)),gradient_norm=float(torch.linalg.vector_norm(model.gradient(origin))),
        exact_fixed_quadratic_jet_max=float(np.max(abs(origin_hess-prior))),
        Hpp_min=float(np.linalg.eigvalsh(origin_hess[12:,12:])[0]),
        scope='Fixed cubic gate proves positive origin Hessian and, by continuity, some local mechanical Legendre neighborhood; no numerical sampling gives its uniform radius.')
    # An actually recovered local inverse of learned velocity, not an attempt
    # to identify physical momentum from another model's velocity.
    zz=torch.tensor(raw['test_x'][292]/model.D.numpy());q,p=zz[:12],zz[12:]
    target=model.gradient(zz)[12:].detach().numpy()
    fun=lambda mom:model.gradient(torch.cat((q,torch.tensor(mom))))[12:].detach().numpy()-target
    jac=lambda mom:torch.autograd.functional.hessian(lambda pp:model.h(torch.cat((q,pp))),torch.tensor(mom)).detach().numpy()
    start_mom=p.numpy()+1e-5/model.D[12:].numpy()
    inverse=root(fun,start_mom,jac=jac,method='hybr',options={'xtol':1e-11,'maxfev':100})
    report['learned_self_legendre_sample']=dict(split='test',index=292,success=bool(inverse.success),
        residual=float(np.linalg.norm(fun(inverse.x))),momentum_difference=float(np.linalg.norm(inverse.x-p.numpy())),
        message=str(inverse.message),scope='Only local solver check on this frozen learned model; not global SPD/invertibility or truth momentum recovery.')
    report.update(status='executed',seconds=time.perf_counter()-start,
        conclusion='Same ideal-Hamiltonian target and canonical normalization verified; finite nonzero learning errors and negative Hpp witnesses remain. Canonical/Birkhoff phase dynamics do not require Hpp positive.',
        no_training=True,no_full_coil_learning_claim=True,no_uniform_error_claim=True)
    np.savez_compressed(out/f'{args.run_id}.npz',**arrays)
    dest.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:report[k] for k in ['status','seconds','splits','origin','learned_self_legendre_sample']},indent=2))


if __name__=='__main__':main()
