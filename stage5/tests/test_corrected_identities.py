"""Independent algebra/physical-law tests for the E01--E16 repairs.

The low-dimensional examples are regression/counterexamples, not replacement
models for the 12-DOF robot.  Exact matrix flows are only analytic benchmarks.
"""
import sys
from pathlib import Path
import unittest

import numpy as np
from scipy.linalg import expm
import sympy as sp

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'program'))
import corrected_identities as ci


class CorrectedIdentities(unittest.TestCase):
    def test_E01_morison_dimensions_relative_power_and_fluid_supply(self):
        kwargs=dict(rho=1000.,area=2e-6,diameter=.002,Ca=.7,Cd=1.2)
        result=ci.corrected_morison_transverse([0,0,1],[2,0,7],[1,0,5],
                                             [3,0,9],[1,0,2],**kwargs)
        np.testing.assert_allclose(result['force'],[1.2088,0,0],atol=1e-14)
        self.assertLess(result['relative_drag_power'],0.)
        self.assertGreater(result['rod_power'],0.)
        # Scaling every velocity by a scales drag by a^2, acceleration separately.
        scaled=ci.corrected_morison_transverse([0,0,1],[6,0,21],[3,0,15],
                                             [3,0,9],[1,0,2],**kwargs)
        np.testing.assert_allclose(scaled['drag'],9*result['drag'],atol=1e-14)
        np.testing.assert_allclose(scaled['added_mass'],result['added_mass'],atol=1e-14)

    def test_E02_real_penetration_energy_gradient_and_friction_power(self):
        gap=-.03; k=7.; result=ci.contact_penalty(gap,k)
        eps=1e-7
        derivative=(ci.contact_penalty(gap+eps,k)['energy']-
                    ci.contact_penalty(gap-eps,k)['energy'])/(2*eps)
        self.assertAlmostEqual(derivative,-result['normal_multiplier'],places=10)
        self.assertEqual(ci.contact_penalty(.01,k)['normal_multiplier'],0.)
        self.assertTrue(np.isreal(result['energy']))
        velocity=np.array([.3,-.2,0.])
        friction=ci.regularized_friction(result['normal_multiplier'],velocity,.2,1e-3)
        self.assertLess(friction @ velocity,0.)

    def test_E03_director_sign_and_independent_torsion(self):
        tangent=np.array([0.,0.,1.]); derivative=np.array([.2,.4,0.])
        u=ci.darboux_perpendicular(tangent,derivative)
        np.testing.assert_allclose(np.cross(u,tangent),derivative,atol=1e-15)
        self.assertGreater(np.linalg.norm(np.cross(np.cross(derivative,tangent),tangent)-derivative),.5)
        # Same straight centerline, different material frame torsion energies.
        twist=np.array([0.,2.]); GJ=.7; length=.3
        energy=.5*GJ*twist**2*length
        self.assertEqual(energy[0],0.);self.assertGreater(energy[1],0.)

    def test_E04_scaled_complex_chain_rule_including_force(self):
        q=np.array([.7,-.2]);p=np.array([-.4,.3]);force=np.array([.1,-.05])
        expected=ci.complex_coordinates(p,-q+force)
        np.testing.assert_allclose(ci.complex_hamiltonian_rhs(q,p,force),expected,atol=1e-15)
        _,barxi=ci.wirtinger_real_energy(q,p)
        self.assertGreater(np.linalg.norm(barxi-(q+1j*p)/2),.1)

    def test_E05_power_loss_and_conjugate_gradient(self):
        Hdot=-.048;Pdot=.12
        direct=abs(np.sqrt(2)*(Hdot+1j*Pdot))**2
        self.assertAlmostEqual(ci.complex_energy_rate_squared(Hdot,Pdot),direct,places=15)
        self.assertGreater(direct-2*Pdot**2,.0046)
        dxi,dbar=ci.wirtinger_real_energy(.7,-.4)
        true=ci.complex_hamiltonian_rhs(.7,-.4)
        self.assertAlmostEqual(abs(true+1j*dbar),0.,places=15)
        self.assertGreater(abs(true+1j*dxi),.5)

    def test_E06_original_pfaff_cross_partial_incompatibility(self):
        q,p,t,gamma=sp.symbols('q p t gamma',real=True)
        candidate=(1+gamma*t)*p
        # Requiring a_q,p=1 forces partial_t partial_p a_q=0, but prescribed
        # a_q,t=gamma*p has partial_p=gamma.  No function satisfies both.
        self.assertEqual(sp.diff(gamma*p,p),gamma)
        self.assertEqual(sp.diff(sp.Integer(1),t),0)
        self.assertEqual(sp.diff(candidate,p)-1,gamma*t)

    def test_E07_endpoint_compatibility_transversality_not_Hessian_inverse(self):
        n=12;d=2*n;L=ci.original_endpoint_matrix(n);K=-ci.canonical_J(n)
        np.testing.assert_array_equal(ci.endpoint_compatibility_defect(L,K,K),np.zeros((2*d,2*d)))
        A,B,C,D=L[:d,:d],L[:d,d:],L[d:,:d],L[d:,d:]
        N=ci.endpoint_gradient_jacobian(A,B,C,D,np.eye(d))
        np.testing.assert_array_equal(N,np.zeros((d,d)))
        np.testing.assert_allclose(ci.reconstruct_flow_jacobian(A,B,C,D,N),np.eye(d),atol=0.)
        with self.assertRaises(np.linalg.LinAlgError):
            ci.endpoint_gradient_jacobian(A,B,C,D,-np.eye(d))
        M=expm(.3*ci.canonical_J(1));I=np.eye(2)
        wrong=ci.endpoint_gradient_jacobian(I,-I,.5*I,.5*I,M)
        self.assertGreater(np.linalg.norm(wrong-wrong.T),.5)

    def test_E08_fixed_coordinate_generator_recurrence(self):
        q,p,t=sp.symbols('q p t',real=True);z=sp.Matrix([q,p])
        H=(1+q*q)*p*p/2+q*q/2+q**4/4
        coeff=ci.central_generator_coefficients(H,[q,p],t,0,4)
        J=sp.Matrix([[0,1],[-1,0]]);f=J*sp.Matrix([sp.diff(H,v) for v in z])
        self.assertEqual(sp.simplify(coeff[1]+H),0)
        self.assertEqual(coeff[2],0);self.assertEqual(coeff[4],0)
        self.assertEqual(sp.simplify(coeff[3]+(f.T*sp.hessian(H,z)*f)[0]/24),0)
        nonaut=ci.central_generator_coefficients(H+t*q*q/2,[q,p],t,0,2)
        self.assertEqual(sp.simplify(nonaut[2]+q*q/4),0)

    def test_E09_fixed_w_chain_rule_and_original32_blocks(self):
        J=ci.canonical_J(1);I=np.eye(2);w=np.array([.2,-.3]);t=.21
        def N_of(time):
            # H=(1+t)*(q²+p²)/2 has known angle t+t²/2, only a benchmark.
            M=expm((time+time*time/2)*J)
            return ci.endpoint_gradient_jacobian(J,-J,.5*I,.5*I,M)
        N=N_of(t);zplus=w-.5*J @ (N @ w)
        rhs=ci.fixed_endpoint_rhs(J,.5*I,N,(1+t)*J @ zplus)
        eps=1e-5
        fd=(N_of(t+eps) @ w-N_of(t-eps) @ w)/(2*eps)
        np.testing.assert_allclose(rhs,fd,atol=2e-10,rtol=0.)
        L=ci.original_endpoint_matrix(1);fplus=np.array([.3,-.8])
        np.testing.assert_allclose(L[2:,:2] @ fplus,[.15,.4],atol=0.)
        np.testing.assert_allclose(L[:2,:2] @ fplus,[-.8,.3],atol=0.)

    def test_E10_damping_sign_does_not_restore_scalar_gradient(self):
        # Candidate (-Q+gamma*P,-P) after P=-p has correct force sign but curl.
        gamma=.7;jac=np.array([[-1.,gamma],[0.,-1.]])
        defect=ci.gradient_integrability_defect(jac)
        self.assertEqual(defect[0,1],gamma)
        self.assertGreater(np.linalg.norm(defect),.9)

    def test_E11_noncommuting_original36_matches_full_midpoint(self):
        M=np.array([[2.,.3],[.3,1.]]);K=np.array([[3.,.8],[.8,1.5]])
        C=np.array([[.4,.07],[.07,.2]]);q=np.array([.2,-.4]);p=np.array([.3,.1])
        force=np.array([.03,-.02]);h=.17;Minv=np.linalg.inv(M)
        q1,p1=ci.midpoint_linear_mechanical_step(q,p,h,M,K,C,force)
        F=np.block([[np.zeros((2,2)),Minv],[-K,-C @ Minv]])
        expected=np.linalg.solve(np.eye(4)-h*F/2,
                                 (np.eye(4)+h*F/2) @ np.r_[q,p]+h*np.r_[np.zeros(2),force])
        np.testing.assert_allclose(np.r_[q1,p1],expected,atol=1e-15,rtol=0.)
        self.assertGreater(np.linalg.norm(K @ Minv-Minv @ K),.1)
        Ebad=h*h*Minv @ K/4+h*Minv @ C/2
        bad=np.linalg.solve(np.eye(2)+Ebad,(np.eye(2)-Ebad) @ p-h*K @ q+h*force)
        self.assertGreater(np.linalg.norm(bad-p1),1e-4)

    def test_E12_twoform_half_double_sum(self):
        Da=np.array([[0.,1.],[0.,0.]])
        K=ci.twoform_from_oneform_jacobian(Da);v=np.array([1.,.3]);w=np.array([.2,1.])
        explicit=.5*np.sum(K*(np.outer(v,w)-np.outer(w,v)))
        self.assertAlmostEqual(ci.twoform_evaluation(K,v,w),explicit,places=15)
        wrong=np.sum(K*(np.outer(v,w)-np.outer(w,v)))
        self.assertAlmostEqual(wrong,2*explicit,places=15)

    def test_E13_negative_D_and_time_compatibility(self):
        gamma=.7;t=.2;q=.3;p=-.4;weight=np.exp(gamma*t)
        K=-weight*ci.canonical_J(1)
        gradB=weight*np.array([q,p]);at=weight*np.array([gamma*p,0.])
        expected=np.array([p,-q-gamma*p])
        np.testing.assert_allclose(ci.birkhoff_field(K,gradB,at),expected,atol=1e-15)
        np.testing.assert_allclose(ci.birkhoff_field_from_negative_D(K,-gradB-at),expected,atol=1e-15)
        Db=weight*np.array([[1.,gamma],[0.,1.]])
        np.testing.assert_allclose(ci.time_compatibility_defect(gamma*K,Db),0.,atol=1e-15)

    def test_E14_transport_volume_not_Euclidean_volume(self):
        n=3;gamma=.4;h=.2;J=ci.canonical_J(n);K=-J
        A=J-np.diag(np.r_[np.zeros(n),gamma*np.ones(n)])
        flow=expm(h*A)
        self.assertAlmostEqual(np.linalg.det(flow),np.exp(-n*gamma*h),places=14)
        self.assertLess(np.linalg.det(flow),.8)
        self.assertAlmostEqual(ci.transported_volume_ratio(flow,K,np.exp(gamma*h)*K),1.,places=14)

    def test_E15_torus_closed_primitive_has_nonzero_period(self):
        radius=.1;action=radius*radius/2
        theta=np.linspace(0.,2*np.pi,10001)
        numerical=np.trapezoid(radius**2*np.sin(theta)**2,theta)
        self.assertAlmostEqual(numerical,ci.torus_primitive_periods(action),places=14)
        self.assertGreater(numerical,.03)
        self.assertEqual(ci.torus_primitive_periods(action-action),0.)

    def test_E16_Rayleigh_mass_chain_rule_and_velocity_dependent_coefficient(self):
        p1,p2,v1,v2=sp.symbols('p1 p2 v1 v2',real=True)
        mass=sp.Matrix([[2,sp.Rational(1,3)],[sp.Rational(1,3),3]])
        v=mass.inv()*sp.Matrix([p1,p2])
        D=(v1*v1+3*v2*v2)/2+v1**4/10
        G=D.subs({v1:v[0],v2:v[1]},simultaneous=True)
        gradp=sp.Matrix([sp.diff(G,x) for x in (p1,p2)])
        force=-sp.Matrix([sp.diff(D,x) for x in (v1,v2)]).subs({v1:v[0],v2:v[1]},simultaneous=True)
        self.assertEqual(sp.simplify(-mass.T*gradp-force),sp.zeros(2,1))
        point={p1:.7,p2:-.3};gp=np.array(gradp.subs(point),float).ravel()
        f=np.array(force.subs(point),float).ravel();M=np.array(mass,float)
        np.testing.assert_allclose(ci.rayleigh_force_from_momentum_gradient(M,gp),f,atol=1e-15)
        self.assertGreater(np.linalg.norm(-gp-f),.1)

    def test_original31_roundtrip_and_joint_inverse_24D(self):
        rng=np.random.default_rng(1025);plus=rng.normal(size=24);minus=rng.normal(size=24)
        hat,w=ci.endpoint_forward(plus,minus);rp,rm=ci.endpoint_inverse(hat,w)
        np.testing.assert_allclose(rp,plus,atol=3e-16,rtol=1e-15)
        np.testing.assert_allclose(rm,minus,atol=3e-16,rtol=1e-15)

    def test_nonzero_initial_generator_gauge_and_endpoint_compatibility(self):
        # A nonlinear generating-coordinate gauge preserves endpoint matching
        # but makes the initial gradient nonzero: E1=J(z+-z-)+grad psi(w).
        w=np.array([.4,-.3]);reference=np.array([-.1,.2]);J=ci.canonical_J(1)
        def psi(x):return x[0]**3/3+x[1]**2/2+x[0]*x[1]
        def gradient(x):return np.array([x[0]**2+x[1],x[1]+x[0]])
        hessian=np.array([[2*w[0],1.],[1.,1.]])
        A=J+.5*hessian;B=-J+.5*hessian;C=D=.5*np.eye(2)
        endpoint_jacobian=np.block([[A,B],[C,D]])
        np.testing.assert_allclose(
            ci.endpoint_compatibility_defect(endpoint_jacobian,-J,-J),0.,atol=1e-15)
        np.testing.assert_allclose(
            ci.endpoint_gradient_jacobian(A,B,C,D,np.eye(2)),hessian,atol=1e-15)
        initial=ci.radial_generator_potential(w,reference,gradient,quadrature_order=4)
        self.assertAlmostEqual(initial,psi(w)-psi(reference),places=15)
        self.assertGreater(np.linalg.norm(gradient(w)),.1)
        self.assertEqual(ci.radial_generator_potential(reference,reference,gradient),0.)

    def test_complete_variable_mass_geometric_force(self):
        q,p=sp.symbols('q p',real=True);mass=1+q*q
        H=p*p/(2*mass)+q*q/2
        state={q:.3,p:.7}
        expected=np.array([sp.diff(H,p),-sp.diff(H,q)],dtype=object)
        expected=np.array([float(e.subs(state)) for e in expected])
        actual=ci.mechanical_field([[1.09]],[[[.6]]],[.3],[.7])
        np.testing.assert_allclose(actual,expected,atol=1e-15)
        self.assertGreater(abs(actual[1]+.3),.1)

    def test_mass_validation_is_independent_of_SI_magnitude(self):
        # A small absolute norm does not make asymmetric mass physical.
        mass=1e-16*np.array([[2.,.2],[.2,1.]])
        gradient=np.array([.3,-.4])
        np.testing.assert_allclose(
            ci.rayleigh_force_from_momentum_gradient(mass,gradient),
            -mass @ gradient,atol=0.,rtol=1e-15)
        wrong=mass.copy();wrong[0,1]*=2
        with self.assertRaises(ValueError):
            ci.rayleigh_force_from_momentum_gradient(wrong,gradient)
        with self.assertRaises(ValueError):
            ci.rayleigh_force_from_momentum_gradient([[np.nan]], [.1])


if __name__=='__main__':
    unittest.main(verbosity=2)
