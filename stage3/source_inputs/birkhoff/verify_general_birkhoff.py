"""Reproducible synthetic test of a local time-dependent Birkhoff integrator.

This is NOT a catheter/COMSOL simulation or a KAM certificate.
The test has configuration-dependent mass and non-proportional damping.
Its known nonlinear point chart permits independent exact reference solutions.
The numerical step uses a principal-square-root Darboux chart, not the inverse
physical flow, and a midpoint step (so it is not the exact-flow update).

Dependencies: numpy, scipy, sympy. Run: python verify_general_birkhoff.py
Outputs are written beside this script, never to user input files.
"""
from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import sympy as sp
from scipy.linalg import expm, sqrtm, solve_sylvester
from scipy.integrate import solve_ivp

ROOT = Path(__file__).resolve().parent
J = np.block([[np.zeros((2, 2)), np.eye(2)], [-np.eye(2), np.zeros((2, 2))]])
KREF = -J
M0 = np.array([[1.12, .12], [.12, 1.32]])
KS = np.array([[1.05, .05], [.05, 2.05]])
C0 = np.array([[.18, .025], [.025, .37]])
CD = np.array([[.09, .009], [.009, .14]])
KP = np.diag([.05, .10])
Z0 = np.array([.25, -.18, .03, .04])

q1, q2, p1, p2 = sp.symbols('q1 q2 p1 p2', real=True)
zz = sp.Matrix([q1, q2, p1, p2]); qq = zz[:2, :]; pp = zz[2:, :]
Q = sp.Matrix([q1 + sp.Rational(1, 5)*q1**3,
               (1 + sp.Rational(3, 20)*q1)*q2])
D = Q.jacobian(qq)
P = D.T.inv()*pp
yexpr = Q.col_join(P)
xi_raw = sp.lambdify(tuple(zz), yexpr, 'numpy', cse=True)
dxi_raw = sp.lambdify(tuple(zz), yexpr.jacobian(zz), 'numpy', cse=True)
d_raw = sp.lambdify((q1, q2), D, 'numpy', cse=True)


def xi(z): return np.asarray(xi_raw(*z), dtype=float).reshape(4)
def dxi(z): return np.asarray(dxi_raw(*z), dtype=float)
def dqmap(q): return np.asarray(d_raw(*q), dtype=float)


def xi_inverse(y):
    x = float(y[0])
    for _ in range(30):
        dx = (x + .2*x**3 - y[0])/(1 + .6*x*x)
        x -= dx
        if abs(dx) < 5e-15: break
    else: raise RuntimeError('point-chart inverse failed')
    if abs(1 + .15*x) < 1e-8: raise ValueError('chart domain boundary')
    q = np.array([x, y[1]/(1 + .15*x)])
    return np.r_[q, dqmap(q).T @ y[2:]]


def build_case(C, stiffness):
    A = np.block([[np.zeros((2, 2)), np.linalg.inv(M0)],
                  [-stiffness, -C @ np.linalg.inv(M0)]])
    Ms = sp.Matrix(M0); Cs = sp.Matrix(C); Ss = sp.Matrix(stiffness)
    mq = D.T*Ms*D
    cq = D.T*Cs*D
    H = (pp.T*mq.inv()*pp)[0]/2 + (Q.T*Ss*Q)[0]/2
    hp = sp.Matrix([sp.diff(H, p1), sp.diff(H, p2)])
    hq = sp.Matrix([sp.diff(H, q1), sp.diff(H, q2)])
    fexpr = hp.col_join(-hq-cq*hp)
    fr = sp.lambdify(tuple(zz), fexpr, 'numpy', cse=True)
    jr = sp.lambdify(tuple(zz), fexpr.jacobian(zz), 'numpy', cse=True)
    f = lambda z: np.asarray(fr(*z), dtype=float).reshape(4)
    jac = lambda z: np.asarray(jr(*z), dtype=float)
    return A, f, jac


def linear_K(A, t):
    invS = expm(-A*t)
    return invS.T @ KREF @ invS


def chart(A, t, with_generator=False):
    K = linear_K(A, t)
    B = np.linalg.solve(KREF, K)
    raw = sqrtm(B)
    im = float(np.max(np.abs(np.imag(raw))))
    if im > 1e-10: raise ValueError('no tested real principal square root')
    T = np.asarray(np.real(raw), dtype=float)
    defect = np.linalg.norm(T.T@KREF@T-K, 2)
    if defect > 1e-10: raise RuntimeError(f'chart congruence failed: {defect}')
    if not with_generator: return T
    Kdot = -A.T@K-K@A
    Bdot = np.linalg.solve(KREF, Kdot)
    Tdot = solve_sylvester(T, T, Bdot)
    L = Tdot@np.linalg.inv(T)+T@A@np.linalg.inv(T)
    return T, L, defect, np.linalg.norm(L.T@KREF+KREF@L, 2)


def physical_K(A, t, z):
    Dxi = dxi(z)
    return Dxi.T@linear_K(A, t)@Dxi


def conjugated_step(A, t, h, z):
    T0, T1 = chart(A, t), chart(A, t+h)
    Tm, L, chart_defect, ham_defect = chart(A, t+h/2, True)
    Cmid = np.linalg.solve(np.eye(4)-h*L/2, np.eye(4)+h*L/2)
    ymap = np.linalg.solve(T1, Cmid@T0)
    zn = xi_inverse(ymap@xi(z))
    tangent = np.linalg.solve(dxi(zn), ymap@dxi(z))
    return zn, tangent, chart_defect, ham_defect


def midpoint_step(f, jac, h, z):
    zn = z+h*f(z)
    for k in range(20):
        m=(z+zn)/2
        r=zn-z-h*f(m)
        if np.linalg.norm(r, np.inf) < 4e-14: break
        zn -= np.linalg.solve(np.eye(4)-h*jac(m)/2, r)
    else: raise RuntimeError('midpoint Newton failed')
    m=(z+zn)/2; Df=jac(m)
    tangent=np.linalg.solve(np.eye(4)-h*Df/2, np.eye(4)+h*Df/2)
    return zn, tangent, float(np.linalg.norm(zn-z-h*f(m), np.inf))


def run_case(label, C, stiffness, Tf=2.0):
    A, f, jac=build_case(C, stiffness)
    y0=xi(Z0)
    rng=np.random.default_rng(712)
    identity_errors=[]
    for z in Z0 + .08*rng.standard_normal((8,4)):
        identity_errors.append(float(np.linalg.norm(dxi(z)@f(z)-A@xi(z))))
    exact_end=xi_inverse(expm(A*Tf)@y0)
    independent=solve_ivp(lambda t,z:f(z), [0,Tf], Z0, method='DOP853', rtol=3e-13, atol=3e-15)
    if not independent.success: raise RuntimeError(independent.message)
    result={'label':label, 'T':Tf, 'A':A.tolist(),
        'mass_min_eigenvalue_at_initial':float(np.linalg.eigvalsh(dqmap(Z0[:2]).T@M0@dqmap(Z0[:2]))[0]),
        'damping_min_eigenvalue':float(np.linalg.eigvalsh(C)[0]),
        'CM_inverse_commutator_norm':float(np.linalg.norm(C@np.linalg.inv(M0)-np.linalg.inv(M0)@C,2)),
        'nonlinear_physical_equation_conjugacy_error':max(identity_errors),
        'reference_check_DOP853_error':float(np.linalg.norm(independent.y[:,-1]-exact_end)),
        'results':[]}
    for method in ['ordinary_midpoint','birkhoff_chart_midpoint']:
        previous=None
        for h in [.2,.1,.05,.025]:
            n=int(round(Tf/h)); z=Z0.copy()
            mxstruct=mxres=mxchart=mxham=0.
            for k in range(n):
                t=k*h
                if method=='ordinary_midpoint':
                    zn,Dstep,res=midpoint_step(f,jac,h,z); mxres=max(mxres,res)
                else:
                    zn,Dstep,dc,dh=conjugated_step(A,t,h,z)
                    mxchart=max(mxchart,dc); mxham=max(mxham,dh)
                struct=np.linalg.norm(Dstep.T@physical_K(A,t+h,zn)@Dstep-physical_K(A,t,z),2)
                mxstruct=max(mxstruct,float(struct)); z=zn
            err=float(np.linalg.norm(z-exact_end))
            order=None if previous is None else float(np.log2(previous/err))
            result['results'].append({'method':method,'h':h,'endpoint_error':err,'order':order,
               'max_K_defect_spectral_2_norm':mxstruct,'max_Newton_increment_residual':mxres,
               'max_chart_congruence_defect':mxchart,'max_transformed_Hamiltonian_defect':mxham})
            previous=err
    # Independent central-difference tangent verification, not used to define K.
    t=.35; h=.1; z=Z0.copy(); zn,Danalytic,_,_=conjugated_step(A,t,h,z)
    eps=2e-5
    Dfd=np.column_stack([(conjugated_step(A,t,h,z+eps*np.eye(4)[j])[0]-
                         conjugated_step(A,t,h,z-eps*np.eye(4)[j])[0])/(2*eps) for j in range(4)])
    result['finite_difference_tangent_error']=float(np.linalg.norm(Dfd-Danalytic,2))
    result['finite_difference_K_defect']=float(np.linalg.norm(Dfd.T@physical_K(A,t+h,zn)@Dfd-physical_K(A,t,z),2))
    # Endpoint transformation compatibility in the original nonlinear state.
    Tm,Tp=chart(A,t),chart(A,t+h)
    Dm=Tm@dxi(z); Dp=Tp@dxi(zn)
    Dalpha=np.block([[J@Dp,-J@Dm],[.5*Dp,.5*Dm]])
    J8=np.block([[np.zeros((4,4)),np.eye(4)],[-np.eye(4),np.zeros((4,4))]])
    Kprod=np.block([[physical_K(A,t+h,zn),np.zeros((4,4))],
                   [np.zeros((4,4)),-physical_K(A,t,z)]])
    result['endpoint_compatibility_defect']=float(np.linalg.norm(Dalpha.T@J8@Dalpha-Kprod,2))
    return result, A


def main():
    result={'scope':'Synthetic known-chart test; no physical catheter or KAM certification.',
            'M0':M0.tolist(),'C0':C0.tolist(),'Cd':CD.tolist(),'Ks':KS.tolist(),'Kp':KP.tolist(),
            'initial_state':Z0.tolist(),
            'point_chart':'Q1=q1+0.2*q1^3; Q2=(1+0.15*q1)*q2; P=DQ(q)^(-T)*p',
            'cases':[]}
    cases={}
    for label,C,S in [('uncontrolled',C0,KS),('controlled',CD,KS+KP)]:
        case,A=run_case(label,C,S); result['cases'].append(case); cases[label]=A
    # Verify the physical control law and report error against the SAME target.
    A0=cases['uncontrolled']; Ac=cases['controlled']; Tf=2.; h=.025
    y0=xi(Z0); z_no=Z0.copy(); z_yes=Z0.copy(); es0=[]; esc=[]; efforts=[]
    for k in range(int(round(Tf/h))+1):
        t=k*h; target=xi_inverse(expm(Ac*t)@y0)
        es0.append(float(np.linalg.norm(z_no-target)**2)); esc.append(float(np.linalg.norm(z_yes-target)**2))
        y=xi(z_yes); uq=dqmap(z_yes[:2]).T@((C0-CD)@np.linalg.solve(M0,y[2:])-KP@y[:2])
        efforts.append(float(np.linalg.norm(uq)))
        if k<int(round(Tf/h)):
            z_no=conjugated_step(A0,t,h,z_no)[0]
            z_yes=conjugated_step(Ac,t,h,z_yes)[0]
    result['control_comparison']={'reference':'exact controlled target, common initial state and step',
        'h':h,'T':Tf,'uncontrolled_RMS_to_target':float(np.sqrt(np.mean(es0))),
        'controlled_RMS_to_target':float(np.sqrt(np.mean(esc))),
        'maximum_physical_generalized_control_norm':max(efforts),
        'note':'Ideal fully actuated synthetic control. No learning, noise, saturation, or magnetic realization.'}
    result['controlled_and_uncontrolled_K_difference_at_t1']=float(np.linalg.norm(
        physical_K(A0,1,Z0)-physical_K(Ac,1,Z0),2))
    (ROOT/'verification_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    for case in result['cases']:
        print('\n',case['label'],'reference agreement',case['reference_check_DOP853_error'])
        for row in case['results']:
            print(row['method'],row['h'],f"err={row['endpoint_error']:.6g}",
                  'p=',row['order'],f"Kdef={row['max_K_defect_spectral_2_norm']:.3g}")
        print('endpoint',case['endpoint_compatibility_defect'],'FD tangent',case['finite_difference_tangent_error'])
    print(json.dumps(result['control_comparison'],indent=2))

if __name__=='__main__': main()
