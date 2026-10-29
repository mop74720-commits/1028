"""Structural and independent numerical checks for the new research branch."""
from pathlib import Path
import itertools,json,sys,unittest
import numpy as np
import torch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'stage5/program'))
from learning_models import MechanicalPolynomial,make_model,real_parameter_count,RodROM
from resonance_normalform_pair import multiply


class LearningResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_default_dtype(torch.float64);torch.set_num_threads(1)

    def test_model_counts_and_equilibrium_jet(self):
        for kind,count in [('analytic_mechanical4',8749),('complex_hidden',7104),('spd_complex',13440)]:
            net=make_model(kind,12,.08,.01,51001)
            self.assertEqual(real_parameter_count(net),count)
            hess=torch.autograd.functional.hessian(lambda x:net(x[None,:])[0],torch.zeros(24))
            self.assertLess(float(torch.linalg.norm(hess)),1e-13)

    def test_mechanical_polynomial_full_mixed_feature(self):
        net=MechanicalPolynomial(3,1.)
        pair={tuple(row.tolist()):i for i,row in enumerate(net.index2)}
        with torch.no_grad():net.c22[pair[(0,2)],pair[(1,2)]]=1.7
        x=torch.tensor([.3,-.1,.6,.2,-.4,.7],requires_grad=True)
        value=net(x[None,:])[0];expected=1.7*x[0]*x[2]*x[4]*x[5]
        self.assertLess(float(abs(value-expected)),1e-15)
        hpp=torch.autograd.functional.hessian(lambda p:net(torch.cat([x[:3],p])[None,:])[0],x[3:])
        self.assertAlmostEqual(float(hpp[1,2]),1.7*.3*.6,places=12)

    def test_frozen_training_and_negative_examples(self):
        checks=json.loads((ROOT/'stage5/results/learning/S5_L01_independent_checks.json').read_text())
        self.assertTrue(all(checks['source_hash_matches'].values()))
        self.assertTrue(all(checks['checkpoint_hash_matches'].values()))
        self.assertTrue(checks['all_negative_signs_confirmed'])
        self.assertGreater(len(checks['negative_Hpp_examples']),0)
        for row in checks['inverse_diagnostics']:
            if row['kind'] in ('analytic_mechanical4','spd_complex'):
                self.assertEqual(row['residual_below_1e8_count'],8)

    def test_cubic_homological_sign_on_known_oscillator(self):
        # q=(xi+chi)/sqrt2; H3=a*q^3; average .5{H3,W3}=-15*a^2*I^2/4.
        a=.2;h={(3,0):a/(2*np.sqrt(2)),(2,1):3*a/(2*np.sqrt(2)),
               (1,2):3*a/(2*np.sqrt(2)),(0,3):a/(2*np.sqrt(2))}
        w={k:1j*v/(k[0]-k[1]) for k,v in h.items()}
        def derivative(poly,index):return {tuple(k[j]-(j==index) for j in range(2)):v*k[index] for k,v in poly.items() if k[index]}
        first=multiply(derivative(h,0),derivative(w,1));second=multiply(derivative(h,1),derivative(w,0))
        coeff=-.5j*(first.get((2,2),0)-second.get((2,2),0))
        self.assertAlmostEqual(coeff.real,-15*a*a/4,places=13)
        self.assertLess(abs(coeff.imag),1e-14)

    def test_actual_quartic_derivative_symmetry_and_scalar_check(self):
        tensor=np.load(ROOT/'stage5/results/resonance/S5_R02_tensors.npz')['fourth_selected']
        symmetry=max(np.max(abs(tensor-tensor.transpose(p))) for p in itertools.permutations(range(4)))
        self.assertLess(symmetry,1e-8)
        rom=RodROM();v=torch.zeros(24);v[0]=1;v[13]=-1
        function=lambda s:rom.hamiltonian((s*v)[None,:])[0]
        for _ in range(4):function=torch.func.grad(function)
        direct=float(function(torch.tensor(0.)))/24
        small=np.array([1.,0,0,-1.]);contract=np.einsum('ijkl,i,j,k,l',tensor,small,small,small,small)/24
        self.assertLess(abs(direct-contract),1e-8)

    def test_resonance_and_cubic_correction_are_retained(self):
        r=json.loads((ROOT/'stage5/results/resonance/S5_R01_results.json').read_text())
        self.assertEqual(r['homological_spectrum'][1]['nonaction_resonances'],128)
        self.assertLess(r['axial_symmetry']['maximum_Poisson_abs'],1e-10)
        q=json.loads((ROOT/'stage5/results/resonance/S5_R02_results.json').read_text())['coefficient_of_xi0_squared_chi1_squared']
        self.assertEqual(q['divisor'],0.)
        self.assertGreater(abs(q['cubic_correction_real']),400.)
        self.assertGreater(abs(q['corrected_H4_real']),1e-4)
        self.assertLess(abs(q['corrected_H4_real']),.1)


if __name__=='__main__':unittest.main(verbosity=2)
