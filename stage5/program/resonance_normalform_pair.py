"""Cubic-elimination correction to the first 1:1 pair's quartic normal form.

Computes the derivatives of the *actual* 24D variable-mass energy at zero.
Only terms needed for the restriction to the first pair are materialized.
This is a finite-order floating-point calculation, not an analytic/KAM bound.
"""
from __future__ import annotations
import csv,itertools,json,math,time
from collections import Counter
from pathlib import Path
import numpy as np
import torch
from learning_models import RodROM

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'stage5/results/resonance'


def factorial_multiplicity(indices):return math.prod(math.factorial(v) for v in Counter(indices).values())


def transform(n):
    eye=np.eye(n)/np.sqrt(2)
    return np.block([[eye,eye],[-1j*eye,1j*eye]])


def multiply(a,b):
    out={}
    for i,x in a.items():
        for j,y in b.items():
            k=tuple(u+v for u,v in zip(i,j));out[k]=out.get(k,0j)+x*y
    return out


def main():
    torch.set_default_dtype(torch.float64);torch.set_num_threads(1);torch.set_num_interop_threads(1)
    OUT.mkdir(parents=True,exist_ok=True);start=time.perf_counter();rom=RodROM();n=rom.n
    selected=[0,1,n,n+1];embedding=torch.zeros(2*n,4)
    for j,i in enumerate(selected):embedding[i,j]=1.
    energy=lambda z:rom.hamiltonian(z[None,:])[0]
    full_gradient=torch.func.grad(energy)
    third=torch.func.jacrev(torch.func.jacrev(lambda y:full_gradient(embedding@y)))(torch.zeros(4)).detach().numpy()
    third_seconds=time.perf_counter()-start
    fourth=torch.func.jacrev(torch.func.jacrev(torch.func.jacrev(torch.func.jacrev(lambda y:energy(embedding@y)))))(torch.zeros(4)).detach().numpy()
    fourth_seconds=time.perf_counter()-start-third_seconds
    symmetry=max(float(np.max(np.abs(fourth-fourth.transpose(order)))) for order in itertools.permutations(range(4)))
    if symmetry>1e-8:raise RuntimeError(f'Fourth derivative tensor failed symmetry: {symmetry}')
    t3=np.zeros((2*n,)*3)
    for a in range(2*n):
        for j,b in enumerate(selected):
            for k,c in enumerate(selected):
                for permutation in set(itertools.permutations((a,b,c))):t3[permutation]=third[a,j,k]
    linear=transform(n)
    complex3=np.einsum('abc,ai,bj,ck->ijk',t3,linear,linear,linear,optimize=True)
    complex4=np.einsum('abcd,ai,bj,ck,dl->ijkl',fourth,transform(2),transform(2),transform(2),transform(2),optimize=True)
    h3={};w3={};nu=rom.nu.numpy();divisors=[]
    for indices in itertools.combinations_with_replacement(range(2*n),3):
        powers=tuple(np.bincount(indices,minlength=2*n));coeff=complex3[indices]/factorial_multiplicity(indices)
        divisor=float(np.dot(np.asarray(powers[:n])-np.asarray(powers[n:]),nu))
        if abs(divisor)<1e-10:raise ValueError('A cubic resonance requires a different normal-form construction')
        h3[powers]=coeff;w3[powers]=1j*coeff/divisor;divisors.append(abs(divisor))
    def restricted_derivative(poly,axis):
        result={}
        for powers,c in poly.items():
            if not powers[axis]:continue
            remain=list(powers);remain[axis]-=1
            if any(remain[j] for j in range(2*n) if j not in selected):continue
            exponent=tuple(remain[j] for j in selected)
            result[exponent]=result.get(exponent,0j)+c*powers[axis]
        return result
    correction={}
    per_mode=[]
    for j in range(n):
        first=multiply(restricted_derivative(h3,j),restricted_derivative(w3,j+n))
        second=multiply(restricted_derivative(h3,j+n),restricted_derivative(w3,j))
        contribution={power:-.5j*(first.get(power,0j)-second.get(power,0j)) for power in set(first)|set(second)}
        for power,value in contribution.items():correction[power]=correction.get(power,0j)+value
        power=(2,0,0,2)
        per_mode.append(dict(mode=j,frequency_ratio=float(nu[j]),
            xi0_squared_chi1_squared_correction_real=float(contribution.get(power,0j).real),
            xi0_squared_chi1_squared_correction_imag=float(contribution.get(power,0j).imag)))
    rows=[]
    for indices in itertools.combinations_with_replacement(range(4),4):
        power=tuple(np.bincount(indices,minlength=4));raw=complex4[indices]/factorial_multiplicity(indices)
        corr=correction.get(power,0j);normal=raw+corr
        divisor=nu[0]*(power[0]-power[2])+nu[1]*(power[1]-power[3])
        rows.append(dict(powers=','.join(map(str,power)),raw_H4_real=float(raw.real),raw_H4_imag=float(raw.imag),
            cubic_correction_real=float(corr.real),cubic_correction_imag=float(corr.imag),
            corrected_H4_real=float(normal.real),corrected_H4_imag=float(normal.imag),
            divisor=float(divisor),resonant=bool(abs(divisor)<1e-10),action=bool(power[0]==power[2] and power[1]==power[3])))
    target=next(row for row in rows if row['powers']=='2,0,0,2')
    previous=json.loads((OUT/'S5_R01_results.json').read_text())['raw_H4_first_pair']['refined']
    report=dict(experiment='S5-R02',status='executed',selected_real_coordinates=selected,
        convention='H∘Phi_W3=H2+[H4+0.5{H3,W3}]+...; {H2,W3}=-H3; complex bracket=-i(F_xi G_chi-F_chi G_xi)',
        raw_tensor_symmetry_defect=symmetry,
        minimum_cubic_divisor=min(divisors),coefficient_of_xi0_squared_chi1_squared=target,
        cross_mode_cubic_correction=per_mode,
        comparison_to_independent_radius_extrapolation=dict(raw_coefficient_abs_difference=abs(target['raw_H4_real']-previous['candidate_xi0_squared_chi1_squared_coefficient_real'])),
        timings=dict(third_derivative_s=third_seconds,fourth_derivative_s=fourth_seconds,total_s=time.perf_counter()-start),
        completeness='For a quartic restricted to this four-real-coordinate subspace, the bracket only needs cubic monomials with at most one external variable. These follow from full24-gradient differentiated twice along the four selected coordinates. All12 canonical bracket pairs included. Other quartic terms of the full24D normal form not computed.',
        limitations=['finite-order floating coefficients, no interval residual bound','restricted quartic normal form is not proof that the four-coordinate subspace is invariant','no KAM/twist/analytic-domain certificate','at zero, Rodrigues polynomial branch has the correct required Taylor jet; global branch analyticity is separate'])
    (OUT/'S5_R02_results.json').write_text(json.dumps(report,indent=2)+'\n')
    np.savez_compressed(OUT/'S5_R02_tensors.npz',third_full_gradient_selected=third,fourth_selected=fourth,third_complex_restricted=complex3,fourth_complex_selected=complex4)
    with (OUT/'S5_R02_quartic_pair.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
