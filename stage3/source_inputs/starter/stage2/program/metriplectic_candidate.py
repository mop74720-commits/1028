"""Algebraic validation of an optional thermal extension, with no fitted heat data.

The test uses dimensionless internal energy e and entropy log(e). It verifies
the candidate bracket on the actual 12-DOF ROM states, not a physiological heat
transfer simulation. Prescribed blood flow and coil power remain external ports.
"""
from pathlib import Path
import json
import sys
import numpy as np
import torch
sys.path.insert(0,str(Path(__file__).resolve().parent/'learning'))
from rod_rom import RodROM


def dissipative_matrix(v,C,temperature):
    n=len(v);M=np.zeros((2*n+1,2*n+1))
    Cv=C@v
    M[n:2*n,n:2*n]=temperature*C
    M[n:2*n,-1]=-temperature*Cv
    M[-1,n:2*n]=-temperature*Cv
    M[-1,-1]=temperature*np.dot(v,Cv)
    return M


def main():
    torch.set_num_threads(1);model=RodROM();n=model.n
    rng=np.random.default_rng(7131025)
    z=torch.tensor(rng.uniform(-.03,.03,(32,2*n)))/torch.sqrt(torch.cat([model.nu]*2))
    _,gradient=model.gradient(z)
    a=rng.normal(size=(n,n));C=(a.T@a)/n+.1*np.eye(n)
    J=np.zeros((2*n+1,2*n+1));J[:n,n:2*n]=np.eye(n);J[n:2*n,:n]=-np.eye(n)
    data=[]
    for k,g in enumerate(gradient.numpy()):
        e=float(rng.uniform(.8,1.2));T=e
        v=g[n:];M=dissipative_matrix(v,C,T)
        dE=np.r_[g,1.];dS=np.r_[np.zeros(2*n),1/T]
        rhs=J@dE+M@dS
        data.append(dict(energy_degeneration_relative=float(np.linalg.norm(M@dE)/(np.linalg.norm(M)*np.linalg.norm(dE))),
                         entropy_poisson_defect=float(np.linalg.norm(J@dS)),
                         symmetric_defect=float(np.linalg.norm(M-M.T)),
                         min_metric_eigenvalue_scaled=float(np.linalg.eigvalsh(M).min()/np.linalg.norm(M)),
                         total_energy_rate=float(dE@rhs),entropy_rate=float(dS@rhs),
                         predicted_entropy_rate=float(v@C@v/T)))
    result=dict(state='(Q,P,e), e>0; E=H_ROM+e, S=log(e), T=e; all nondimensional',
                dof=n,samples=len(data),seed=7131025,
                max_energy_degeneration_relative=max(x['energy_degeneration_relative'] for x in data),
                max_entropy_poisson_defect=max(x['entropy_poisson_defect'] for x in data),
                min_metric_eigenvalue_scaled=min(x['min_metric_eigenvalue_scaled'] for x in data),
                max_absolute_total_energy_rate=max(abs(x['total_energy_rate']) for x in data),
                min_entropy_rate=min(x['entropy_rate'] for x in data),
                entropy_rate_identity_abs_max=max(abs(x['entropy_rate']-x['predicted_entropy_rate']) for x in data),
                limitation='Finite floating-point checks supplement the exact factorization proof. No robot heat capacity, thermal conduction, physiological temperature history, or coupled fluid/coil entropy model was identified.',
                adoption='Optional validated algebraic candidate. Mechanical Rayleigh and external power ports remain the current simulation model.',samples_detail=data)
    out=Path('stage2/results/metriplectic_candidate.json');out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='samples_detail'},indent=2))


if __name__=='__main__':main()
