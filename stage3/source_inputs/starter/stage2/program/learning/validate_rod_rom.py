"""Independent virtual-velocity checks of the spatial ROM embedding.

The finite-difference center/frame velocities below do not use the analytic
Jacobians that assemble M(q). These are finite diagnostics, not interval bounds.
"""
from pathlib import Path
import json
import numpy as np
import torch
from rod_rom import RodROM


def vee(a):
    return torch.stack([a[...,2,1]-a[...,1,2],a[...,0,2]-a[...,2,0],
                        a[...,1,0]-a[...,0,1]],-1)/2


def main():
    torch.set_num_threads(1)
    m=RodROM();rng=np.random.default_rng(41025)
    q=torch.tensor(rng.normal(0,.06,(12,m.n)))
    dq=torch.tensor(rng.normal(0,.08,(12,m.n)))
    b=torch.tensor(rng.normal(0,.0008,(12,8)))
    b[:,3:]*=20
    mat,pot,r,frames,centers=m.mechanics(q,field=b,return_geometry=True)
    eps=2e-6
    plus=m.mechanics(q+eps*dq,field=b,return_geometry=True)
    minus=m.mechanics(q-eps*dq,field=b,return_geometry=True)
    vc=(plus[4]-minus[4])/(2*eps)
    dR=(plus[3]-minus[3])/(2*eps)
    wb=vee(frames.transpose(-1,-2)@dR)
    kinetic_direct=.5*m.ds*(m.rho*m.area*(vc*vc).sum((-1,-2))+
                         torch.einsum('bni,ij,bnj->b',wb,m.rotary,wb))
    kinetic_mass=.5*torch.einsum('bi,bij,bj->b',dq,mat,dq)
    kinetic_rel=torch.abs(kinetic_mass-kinetic_direct)/kinetic_direct

    # Independent dipole force/torque virtual work versus the magnetic potential.
    G=torch.stack([b[:,3],b[:,5],b[:,6],b[:,5],b[:,4],b[:,7],b[:,6],b[:,7],
                   -b[:,3]-b[:,4]],-1).reshape(-1,3,3)
    localB=b[:,None,:3]+torch.einsum('bij,bnj->bni',G,centers-m.field_origin)
    mu=m.segment_moment[None,:,None]*frames[:,:,:,2]
    force=torch.einsum('bji,bnj->bni',G,mu)
    torque=torch.linalg.cross(mu,localB)
    ws=torch.einsum('bnij,bnj->bni',frames,wb)
    work=(force*vc+torque*ws).sum((-1,-2))
    # Remove elastic potential by a zero-field evaluation at the same q.
    bzero=torch.zeros_like(b)
    p_el=m.mechanics(q+eps*dq,field=bzero)[1]
    n_el=m.mechanics(q-eps*dq,field=bzero)[1]
    magnetic_dV=(plus[1]-p_el-minus[1]+n_el)/(2*eps)
    mag_rel=torch.abs(magnetic_dV+work)/torch.maximum(work.abs(),torch.tensor(1e-14))

    out=dict(seed=41025,samples=len(q),finite_difference_step=eps,
             mass_kinematic_energy_relative_max=float(kinetic_rel.max()),
             mass_kinematic_energy_abs_max_J=float(torch.max(abs(kinetic_mass-kinetic_direct))),
             dipole_virtual_work_relative_max=float(mag_rel.max()),
             dipole_virtual_work_abs_max_W=float(torch.max(abs(magnetic_dV+work))),
             source='Independent centered differences of centers and SO(3) frames, then translational/rotary kinetic energy and physical dipole virtual work.',
             limitation='Finite samples and double precision; does not certify continuum accuracy or ROM truncation error.')
    path=Path('stage2/results/learning/independent_kinematic_checks.json');path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))


if __name__=='__main__':main()
