"""S5-R01: actual 3D ROM resonance, axial Noether symmetry, raw H4 candidate.

No KAM certificate is claimed. The phase average is a numerical Taylor
coefficient diagnostic, not a completed Birkhoff normal form: elimination of
cubic coupling to the remaining modes contributes an additional quartic term.
"""
from __future__ import annotations
import csv,itertools,json,hashlib,time
from pathlib import Path
import sys
import numpy as np
from scipy.linalg import expm
import torch
from learning_models import RodROM,S2

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'stage5/results/resonance'


def monomials(variables,degree):
    result=[]
    for comb in itertools.combinations_with_replacement(range(variables),degree):
        result.append(np.bincount(comb,minlength=variables))
    return np.asarray(result,dtype=np.uint8)


def homological_spectrum(nu):
    allrows=[];arrays={};summary=[];n=len(nu)
    for degree in (3,4):
        powers=monomials(2*n,degree)
        imbalance=powers[:,:n].astype(int)-powers[:,n:].astype(int)
        divisor=imbalance@nu
        cutoff=1e-10
        resonant=np.abs(divisor)<cutoff
        action=np.all(imbalance==0,axis=1)
        arrays[f'degree{degree}_powers']=powers;arrays[f'degree{degree}_divisor']=divisor
        arrays[f'degree{degree}_resonant']=resonant
        for i in np.flatnonzero(resonant):
            allrows.append(dict(degree=degree,index=int(i),alpha=','.join(map(str,powers[i,:n])),
                beta=','.join(map(str,powers[i,n:])),divisor=float(divisor[i]),action_monomial=bool(action[i])))
        summary.append(dict(degree=degree,total_monomials=len(powers),resonant_count=int(resonant.sum()),
            action_monomials=int(action.sum()),nonaction_resonances=int((resonant&~action).sum()),
            minimum_nonzero_divisor=float(np.min(np.abs(divisor[~resonant]))),
            cutoff=cutoff,warning='Numerical spectrum of the actual linearized ROM; exact paired degeneracy follows from the declared isotropic axial symmetry, not finite tolerance alone.'))
    return summary,allrows,arrays


def symmetry_check(rom):
    n=rom.n;per=n//3
    r=np.zeros((n,n));r[:per,per:2*per]=-np.eye(per);r[per:2*per,:per]=np.eye(per)
    sq=rom.Sq.numpy();a=np.linalg.solve(sq,r@sq)
    rng=np.random.default_rng(510201);scale=np.sqrt(np.r_[rom.nu.numpy(),rom.nu.numpy()])
    states=rng.uniform(-1,1,(12,24))*.05/scale
    rows=[]
    for z in states:
        theta=.37;qmap=expm(theta*a);pmap=expm(-theta*a.T)
        transformed=np.r_[qmap@z[:n],pmap@z[n:]]
        h,g=rom.gradient(torch.tensor(z[None,:]));hh=rom.hamiltonian(torch.tensor(transformed[None,:]))
        # grad J = (A^T P, A Q), and X_J=(A Q,-A^T P).
        generator=np.r_[a@z[:n],-a.T@z[n:]]
        bracket=float(g.detach().numpy()[0]@generator)
        q,p=z[:n],z[n:]
        charge=float(p@a@q)
        charge_new=float(transformed[n:]@a@transformed[:n])
        rows.append(dict(energy_abs_difference=float(abs(hh[0]-h[0])),
                        poisson_H_J=bracket,noether_charge=charge,charge_change=charge_new-charge))
    return dict(generator_A=a.tolist(),configuration_generator_R=r.tolist(),rows=rows,
        maximum_energy_abs_difference=max(x['energy_abs_difference'] for x in rows),
        maximum_Poisson_abs=max(abs(x['poisson_H_J']) for x in rows),
        statement='J_axial=P^T A Q; this is the ideal-axisymmetric conservative ROM only. A generic full-coil bias, blood flow, contact, and actuation need not preserve this symmetry.'),states


def energy_batch(rom,z,batch=128):
    result=[]
    with torch.no_grad():
        for start in range(0,len(z),batch):result.append(rom.hamiltonian(torch.tensor(z[start:start+batch])).numpy())
    return np.concatenate(result)


def quartic_candidate(rom,ntheta,ndelta,amplitudes,ratio=1.):
    n=rom.n;nu=rom.nu.numpy();theta=2*np.pi*np.arange(ntheta)/ntheta;delta=2*np.pi*np.arange(ndelta)/ndelta
    theta,delta=np.meshgrid(theta,delta,indexing='ij');theta=theta.flatten();delta=delta.flatten()
    v=np.zeros((len(theta),2*n))
    v[:,0]=np.cos(theta)/np.sqrt(nu[0]);v[:,n]=-np.sin(theta)/np.sqrt(nu[0])
    v[:,1]=ratio*np.cos(theta+delta)/np.sqrt(nu[1]);v[:,n+1]=-ratio*np.sin(theta+delta)/np.sqrt(nu[1])
    h2=.5*(1+ratio**2)
    values=[]
    for a in amplitudes:
        hplus=energy_batch(rom,a*v);hminus=energy_batch(rom,-a*v)
        values.append((.5*(hplus+hminus)-a*a*h2)/a**4)
    values=np.asarray(values)
    # H_even(a v)/a^4-H2/a^2 = H4(v)+a^2 H6(v)+a^4 H8(v)+...
    # Intercept from three preset radii; no assertion that the tail is zero.
    design=np.stack([np.ones(len(amplitudes)),np.asarray(amplitudes)**2,np.asarray(amplitudes)**4],axis=1)
    coefficients=np.linalg.solve(design,values)
    h4=coefficients[0].reshape(ntheta,ndelta)
    averaged=h4.mean(axis=0)
    fourier=np.fft.fft(averaged)/ndelta
    return dict(theta_count=ntheta,delta_count=ndelta,amplitudes=list(amplitudes),ratio=ratio,
        average_constant=float(fourier[0].real),relative_angle_range=float(np.ptp(averaged)),
        harmonic2_real=float(fourier[2].real),harmonic2_imag=float(fourier[2].imag),
        candidate_xi0_squared_chi1_squared_coefficient_real=float(4*nu[0]*nu[1]*fourier[2].real),
        candidate_xi0_squared_chi1_squared_coefficient_imag=float(4*nu[0]*nu[1]*fourier[2].imag),
        harmonic1_abs=float(abs(fourier[1])),harmonic3plus_max_abs=float(np.max(np.abs(fourier[3:ndelta//2+1]))),
        raw_largest_radius_H4_difference=float(np.max(np.abs(values[-1].reshape(ntheta,ndelta)-h4))),
        phase_average=averaged.tolist(),fourier_real=fourier.real.tolist(),fourier_imag=fourier.imag.tolist()),dict(h4=h4,values_by_radius=values,directions=v)


def main():
    torch.set_default_dtype(torch.float64);torch.set_num_threads(1);torch.set_num_interop_threads(1)
    OUT.mkdir(parents=True,exist_ok=True);start=time.perf_counter();rom=RodROM()
    spectrum,rows,arrays=homological_spectrum(rom.nu.numpy())
    symmetry,states=symmetry_check(rom)
    coarse,carr=quartic_candidate(rom,32,16,[.004,.006,.008])
    refined,rarr=quartic_candidate(rom,64,32,[.003,.0045,.006])
    single,sarr=quartic_candidate(rom,32,16,[.004,.006,.008],ratio=0.)
    comparison=dict(coefficient2_absolute_difference=abs(complex(coarse['harmonic2_real'],coarse['harmonic2_imag'])-complex(refined['harmonic2_real'],refined['harmonic2_imag'])),
        average_absolute_difference=abs(coarse['average_constant']-refined['average_constant']),
        phase_grid_and_amplitude_changed_together=True,
        caveat='Refinement is a finite numerical consistency diagnostic; not interval proof of a Taylor coefficient or rigorous tail bound.')
    result=dict(experiment='S5-R01',status='executed',model=rom.metadata(),
        convention='xi=(Q+iP)/sqrt2; {H2,xi^alpha chi^beta}=i nu·(alpha-beta) xi^alpha chi^beta',
        homological_spectrum=spectrum,axial_symmetry=symmetry,
        raw_H4_first_pair=dict(coarse=coarse,refined=refined,single_mode=single,comparison=comparison),
        limitations=['not a completed normal form: 0.5{H3,W3} from all modes remains to compute',
            'one global SO(2) charge is not four independent symmetries; regular reduction removes one configuration DOF only',
            'quotient is singular at nonfree or critical points, including the straight equilibrium',
            'no twist inverse, complex-domain remainder, Diophantine constant, or KAM threshold certified',
            'frozen RodROM uses piecewise truncated Rodrigues safeguards; rigorous analyticity concerns the exact analytic mechanical branch plus implementation-error bounds, not all torch.where branches automatically'],
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),S2/'rod_rom.py']},
        wall_seconds=time.perf_counter()-start)
    (OUT/'S5_R01_results.json').write_text(json.dumps(result,indent=2)+'\n')
    np.savez_compressed(OUT/'S5_R01_arrays.npz',**arrays,symmetry_states=states,
        **{'coarse_'+k:v for k,v in carr.items()},**{'refined_'+k:v for k,v in rarr.items()},**{'single_'+k:v for k,v in sarr.items()})
    with (OUT/'S5_R01_resonant_monomials.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=['degree','index','alpha','beta','divisor','action_monomial']);writer.writeheader();writer.writerows(rows)
    print(json.dumps(dict(spectrum=spectrum,symmetry_energy=symmetry['maximum_energy_abs_difference'],symmetry_bracket=symmetry['maximum_Poisson_abs'],coarse=coarse,refined=refined,comparison=comparison,wall_seconds=result['wall_seconds']),indent=2))


if __name__=='__main__':main()
