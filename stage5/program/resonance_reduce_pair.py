"""Algebraic circular-polarization reduction of the computed first-pair Z4."""
from pathlib import Path
import csv,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'stage5/results/resonance'
rows=list(csv.DictReader((OUT/'S5_R02_quartic_pair.csv').open()))
coeff={tuple(map(int,r['powers'].split(','))):complex(float(r['corrected_H4_real']),float(r['corrected_H4_imag'])) for r in rows if r['resonant']=='True'}
A=coeff[(2,0,2,0)].real
B=-coeff[(2,0,0,2)].real
expected={(2,0,2,0):A,(0,2,0,2):A,(1,1,1,1):2*(A+B),(2,0,0,2):-B,(0,2,2,0):-B}
defect=max(abs(c-expected.get(k,0.)) for k,c in coeff.items())
twist=2*np.array([[A+B,A-B],[A-B,A+B]])
unitary=np.array([[1,-1j],[1,1j]])/np.sqrt(2)
realmap=np.block([[unitary.real,-unitary.imag],[unitary.imag,unitary.real]])
J=np.block([[np.zeros((2,2)),np.eye(2)],[-np.eye(2),np.zeros((2,2))]])
result=dict(experiment='S5-R03',status='executed',A=A,B=B,
    computed_identity='Z4_first_pair=A*(I0+I1)^2+B*(Q0*P1-Q1*P0)^2',
    coefficient_identity_max_defect=float(defect),
    circular_coordinates='xi_plus=(xi0-i*xi1)/sqrt2; xi_minus=(xi0+i*xi1)/sqrt2',
    circular_actions='I_plus=(N+L)/2; I_minus=(N-L)/2; N=I0+I1',
    real_canonical_map=realmap.tolist(),canonical_defect=float(np.linalg.norm(realmap.T@J@realmap-J)),
    formal_quartic_twist=twist.tolist(),twist_eigenvalues=np.linalg.eigvalsh(twist).tolist(),
    twist_determinant=float(np.linalg.det(twist)),
    limitations=['Only the first-pair restriction of the fourth-order resonant normal form is evaluated.',
        'No full12D twist or full normal form; no quantitative remainder/domain bounds.',
        'The exact24D system need not leave the first-pair subspace invariant.',
        'One global axial SO(2) symmetry does not yield four independent reductions.',
        'Floating nonzero determinant is a numerical candidate, not an interval/KAM certificate.'])
(OUT/'S5_R03_pair_reduction.json').write_text(json.dumps(result,indent=2)+'\n')
phase=np.linspace(0,2*np.pi,257)
r1=json.loads((OUT/'S5_R01_results.json').read_text())['raw_H4_first_pair']['refined']
raw=r1['average_constant']+2*r1['harmonic2_real']*np.cos(2*phase)-2*r1['harmonic2_imag']*np.sin(2*phase)
# Unit energy-radius in each equal-frequency coordinate gives N=1 and L=sin(delta).
normal=A+B*np.sin(phase)**2
fig,axes=plt.subplots(1,2,figsize=(9,3.5),layout='constrained')
axes[0].plot(phase,raw);axes[0].set(title='Raw H4: common-phase average',xlabel='Relative phase delta',ylabel='Quartic coefficient')
axes[1].plot(phase,normal,color='#2ca02c');axes[1].set(title='After all12 cubic bracket channels',xlabel='Relative phase delta',ylabel='Corrected Z4 coefficient')
for ax in axes:ax.grid(alpha=.2)
fig.savefig(OUT/'S5_R03_resonant_cubic_correction.png',dpi=180);fig.savefig(OUT/'S5_R03_resonant_cubic_correction.pdf')
print(json.dumps(result,indent=2))
