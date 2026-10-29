"""Shared corrected identities for E01--E16, with explicit local hypotheses.

No routine reads an exact physical flow.  Symbolic generator coefficients use
only a supplied Hamiltonian and its derivatives; endpoint utilities do not
assert compatibility merely because a linear solve succeeds.  All arrays use
column-vector conventions and z=(q,p), Da[i,j]=partial_j a_i, K=-J canonically.
"""
from __future__ import annotations

import numpy as np


def canonical_J(n: int) -> np.ndarray:
    if not isinstance(n, (int, np.integer)) or n < 1:
        raise ValueError('n must be a positive integer')
    eye = np.eye(n)
    return np.block([[np.zeros_like(eye), eye], [-eye, np.zeros_like(eye)]])


def _spd(mass):
    mass = np.asarray(mass, dtype=float)
    if mass.ndim != 2 or mass.shape[0] != mass.shape[1]:
        raise ValueError('mass must be square')
    if not np.isfinite(mass).all():
        raise ValueError('mechanical mass must be finite')
    # An absolute tolerance can accept a substantially asymmetric SI mass
    # whose entries are themselves smaller than that tolerance.
    scale = np.linalg.norm(mass, ord=np.inf)
    if np.linalg.norm(mass-mass.T, ord=np.inf) > 1e-13*scale:
        raise ValueError('mechanical mass must be symmetric')
    np.linalg.cholesky(mass)
    return mass


def corrected_morison_transverse(tangent, fluid_velocity, rod_velocity,
                                  fluid_accel, rod_accel, *, rho, area,
                                  diameter, Ca, Cd):
    """Candidate force per current length [N/m], not a vascular calibration.

    fluid_accel is the fluid material acceleration, not its velocity.  Ca is
    added-mass coefficient; the pressure-acceleration coefficient is one.
    A reference-length force requires the geometric length conversion.
    """
    if min(rho, area, diameter) <= 0 or min(Ca, Cd) < 0:
        raise ValueError('positive geometry/density and nonnegative coefficients required')
    tangent = np.asarray(tangent, float)
    norm = np.linalg.norm(tangent)
    if tangent.shape != (3,) or norm == 0:
        raise ValueError('a nonzero 3D tangent is required')
    tangent = tangent / norm
    projector = np.eye(3) - np.outer(tangent, tangent)
    u, v, af, ar = map(lambda x: np.asarray(x, float),
                       (fluid_velocity, rod_velocity, fluid_accel, rod_accel))
    if any(x.shape != (3,) for x in (u, v, af, ar)):
        raise ValueError('velocities and accelerations must be 3D vectors')
    relative = projector @ (u-v)
    pressure = rho*area*(projector @ af)
    added = rho*Ca*area*(projector @ (af-ar))
    drag = .5*rho*Cd*diameter*np.linalg.norm(relative)*relative
    return dict(force=pressure+added+drag, pressure=pressure, added_mass=added,
                drag=drag, relative_drag_power=float(drag @ (v-u)),
                rod_power=float((pressure+added+drag) @ v))


def contact_penalty(gap, stiffness, exponent=1.5):
    """g>=0 is separated; force is lambda*grad(g), energy=k delta^(a+1)/(a+1).

    This is a penalty law, not proof of the Hertz approximation for a vessel.
    The force is continuous for exponent>0, not generally analytic at g=0.
    """
    if stiffness < 0 or exponent <= 0:
        raise ValueError('nonnegative stiffness and positive exponent required')
    delta = np.maximum(-np.asarray(gap, float), 0.)
    return dict(penetration=delta, energy=stiffness*delta**(exponent+1)/(exponent+1),
                normal_multiplier=stiffness*delta**exponent)


def regularized_friction(normal_multiplier, tangent_relative_velocity, mu, epsilon):
    if min(normal_multiplier, mu) < 0 or epsilon <= 0:
        raise ValueError('nonnegative force/friction and epsilon>0 required')
    velocity = np.asarray(tangent_relative_velocity, float)
    return -mu*normal_multiplier*velocity/np.sqrt(velocity @ velocity+epsilon**2)


def darboux_perpendicular(unit_tangent, tangent_derivative):
    tangent = np.asarray(unit_tangent, float)
    derivative = np.asarray(tangent_derivative, float)
    if tangent.shape != (3,) or derivative.shape != (3,):
        raise ValueError('3D vectors required')
    if not np.isclose(tangent @ tangent, 1., atol=1e-12, rtol=1e-12):
        raise ValueError('tangent must be unit length')
    if not np.isclose(tangent @ derivative, 0., atol=1e-12, rtol=1e-12):
        raise ValueError('unit tangent derivative must be perpendicular')
    return np.cross(tangent, derivative)


def complex_coordinates(q, p):
    """Requires compatible dimensionless canonical scales before this call."""
    return (np.asarray(q)+1j*np.asarray(p))/np.sqrt(2.)


def wirtinger_real_energy(grad_q, grad_p):
    dq, dp = np.asarray(grad_q), np.asarray(grad_p)
    return (dq-1j*dp)/np.sqrt(2.), (dq+1j*dp)/np.sqrt(2.)


def complex_hamiltonian_rhs(grad_q, grad_p, momentum_force=0.):
    _, derivative_barxi = wirtinger_real_energy(grad_q, grad_p)
    return -1j*derivative_barxi+1j*np.asarray(momentum_force)/np.sqrt(2.)


def complex_energy_rate_squared(H_rate, P_rate):
    """For real H,P and Htilde=sqrt(2)*(H+iP), including nonzero H_rate."""
    if np.iscomplexobj(H_rate) or np.iscomplexobj(P_rate):
        raise ValueError('H and P rates are real in this identity')
    return 2*(np.asarray(H_rate)**2+np.asarray(P_rate)**2)


def rayleigh_force_from_momentum_gradient(mass, gradient_p_G):
    """G(q,p)=D(q,M(q)^-1 p): Q=-M.T grad_p G, at fixed q.

    A velocity-dependent coefficient must already be differentiated inside D.
    This does not replace physical Rayleigh force with synthetic -gamma*p.
    """
    mass = _spd(mass)
    return -mass.T @ np.asarray(gradient_p_G, float)


def mechanical_field(mass, mass_derivative, grad_V, p, force=0.):
    """Complete mechanical field; dM[i,j,k]=partial_(q_i) M[j,k]."""
    mass = _spd(mass)
    p = np.asarray(p, float)
    derivatives = np.asarray(mass_derivative, float)
    n = len(p)
    if mass.shape != (n,n) or derivatives.shape != (n,n,n):
        raise ValueError('mass and derivative dimensions do not match p')
    velocity = np.linalg.solve(mass, p)
    geometric = .5*np.einsum('j,ijk,k->i', velocity, derivatives, velocity)
    return np.concatenate((velocity, geometric-np.asarray(grad_V)+np.asarray(force)))


def twoform_from_oneform_jacobian(Da):
    Da = np.asarray(Da)
    return Da.T-Da


def twoform_evaluation(K, first, second):
    """Omega(v,w) for Omega=1/2 sum Kij dzi wedge dzj (no extra factor 2)."""
    return np.asarray(first) @ np.asarray(K) @ np.asarray(second)


def gradient_integrability_defect(jacobian):
    jacobian = np.asarray(jacobian)
    return jacobian-jacobian.T


def birkhoff_field(K, grad_B, oneform_time_derivative):
    return np.linalg.solve(K, np.asarray(grad_B)+np.asarray(oneform_time_derivative))


def birkhoff_field_from_negative_D(K, D):
    """Original D=-grad(B)-a_t convention, hence f=-K^-1 D."""
    return -np.linalg.solve(K, D)


def time_compatibility_defect(K_time_derivative, Db):
    """b=Kf; Db[i,j]=partial_j b_i.  K_t must equal Db.T-Db."""
    return np.asarray(K_time_derivative)-(np.asarray(Db).T-np.asarray(Db))


def original_endpoint_matrix(n):
    """Original (30): input=(q+,p+,q-,p-); output=(hatQ,hatP,Q,P)."""
    eye, zero = np.eye(n), np.zeros((n,n))
    return np.block([[zero,eye,zero,-eye], [eye,zero,-eye,zero],
                     [.5*eye,zero,.5*eye,zero], [zero,-.5*eye,zero,-.5*eye]])


def endpoint_forward(z_plus, z_minus):
    z_plus, z_minus = np.asarray(z_plus), np.asarray(z_minus)
    if z_plus.shape != z_minus.shape or z_plus.ndim != 1 or len(z_plus)%2:
        raise ValueError('equal even-dimensional endpoint vectors required')
    transformed = original_endpoint_matrix(len(z_plus)//2) @ np.r_[z_plus,z_minus]
    return np.split(transformed,2)


def endpoint_inverse(hat_w, w):
    """Original (31), a joint inverse: never invert the generating Hessian N."""
    hat_w, w = np.asarray(hat_w), np.asarray(w)
    if hat_w.shape != w.shape or len(w)%2:
        raise ValueError('equal even-dimensional vectors required')
    hatQ,hatP=np.split(hat_w,2); Q,P=np.split(w,2)
    return np.r_[Q+.5*hatP,-P+.5*hatQ], np.r_[Q-.5*hatP,-P-.5*hatQ]


def radial_generator_potential(w, reference, closed_gradient, quadrature_order=16):
    """Fix phi(reference)=0 by the straight-path integral of a closed 1-form.

    The caller must establish that the domain is star-shaped about reference
    and D(closed_gradient) is symmetric there.  This quadrature does NOT test
    or create integrability. It is useful for the nonzero initial generator
    c0(w)=E1(z(w),z(w),s,s), not merely the canonical center case c0=0.
    """
    point=np.asarray(w,float);center=np.asarray(reference,float)
    if point.ndim!=1 or center.shape!=point.shape:
        raise ValueError('point and reference must have the same vector shape')
    if not np.isfinite(point).all() or not np.isfinite(center).all():
        raise ValueError('finite point and reference required')
    if not isinstance(quadrature_order,(int,np.integer)) or quadrature_order<1:
        raise ValueError('positive integer quadrature order required')
    nodes,weights=np.polynomial.legendre.leggauss(quadrature_order)
    delta=point-center;integral=0.
    for node,weight in zip(nodes,weights):
        gradient=np.asarray(closed_gradient(center+.5*(node+1)*delta),float)
        if gradient.shape!=point.shape or not np.isfinite(gradient).all():
            raise ValueError('closed_gradient must return a finite vector')
        integral+=.5*weight*(gradient @ delta)
    return float(integral)


def endpoint_compatibility_defect(endpoint_jacobian, K_plus, K_minus):
    d = np.asarray(K_plus).shape[0]
    zero = np.zeros((d,d))
    target = np.block([[K_plus,zero],[zero,-np.asarray(K_minus)]])
    L = np.asarray(endpoint_jacobian)
    return L.T @ canonical_J(d) @ L-target


def endpoint_gradient_jacobian(A, B, C, D, flow_jacobian):
    """N=(AM+B)(CM+D)^-1; caller must separately verify endpoint compatibility."""
    numerator = A @ flow_jacobian+B
    denominator = C @ flow_jacobian+D
    return np.linalg.solve(denominator.T,numerator.T).T


def reconstruct_flow_jacobian(A, B, C, D, N):
    """Inverse Mobius relation, only when A-NC is nonsingular."""
    return np.linalg.solve(A-N @ C,N @ D-B)


def fixed_endpoint_rhs(A, C, N, field_plus, alpha1_time=0., alpha2_time=0.):
    """Theorem B: partial_t g at fixed w, initial endpoint fixed along the flow."""
    f = np.asarray(field_plus)
    a1 = np.broadcast_to(alpha1_time, f.shape)
    a2 = np.broadcast_to(alpha2_time, f.shape)
    return (A-N @ C) @ f+a1-N @ a2


def midpoint_linear_mechanical_step(q, p, h, mass, stiffness, damping, force):
    """Original (36) corrected noncommuting LEFT solve, constant coefficients.

    Variable M, nonlinear potentials or feedback require a nonlinear midpoint
    residual.  This routine deliberately does not pretend to solve that case.
    """
    mass = _spd(mass)
    q,p,force = map(np.asarray,(q,p,force))
    n=len(q); eye=np.eye(n)
    inverse=np.linalg.solve(mass,eye)
    E=(h*h/4)*np.asarray(stiffness) @ inverse+(h/2)*np.asarray(damping) @ inverse
    rhs=(eye-E) @ p-h*np.asarray(stiffness) @ q+h*force
    next_p=np.linalg.solve(eye+E,rhs)
    next_q=q+(h/2)*inverse @ (next_p+p)
    return next_q,next_p


def central_generator_coefficients(H, coordinates, time, start_time, degree):
    """Symbolic fixed-w Hamilton--Jacobi recurrence through a finite degree.

    phi_t=-H(w-J grad(phi)/2,t), phi(w,s;s)=0; increment is -J grad(phi).
    No unknown flow is used.  This exact symbolic benchmark may be expensive
    in high dimension; convergence of the infinite series is NOT asserted.
    """
    import sympy as sp
    variables = list(coordinates)
    if len(variables)%2 or degree < 1:
        raise ValueError('even phase dimension and positive degree required')
    n=len(variables)//2
    J=sp.zeros(2*n)
    J[:n,n:]=sp.eye(n); J[n:,:n]=-sp.eye(n)
    tau=sp.Dummy('tau',real=True)
    coefficients=[sp.Integer(0)]
    phi=sp.Integer(0)
    for k in range(degree):
        gradient=sp.Matrix([sp.diff(phi,v) for v in variables])
        shifted=sp.Matrix(variables)-J*gradient/2
        substitution=dict(zip(variables,shifted));substitution[time]=start_time+tau
        value=H.subs(substitution,simultaneous=True)
        ck=-sp.series(value,tau,0,k+1).removeO().expand().coeff(tau,k)/(k+1)
        ck=sp.simplify(ck)
        coefficients.append(ck)
        phi+=tau**(k+1)*ck
    return coefficients


def transported_volume_ratio(flow_jacobian, K_minus, K_plus):
    """Signed Euclidean determinant times the two symplectic-density ratio."""
    _, log_minus=np.linalg.slogdet(K_minus)
    _, log_plus=np.linalg.slogdet(K_plus)
    if not np.isfinite(log_minus+log_plus):
        raise ValueError('nondegenerate endpoint forms required')
    return np.linalg.det(flow_jacobian)*np.exp((log_plus-log_minus)/2)


def torus_primitive_periods(action_offset):
    """Periods of sum I0_j dtheta_j on the fundamental cycles, theta period 2pi."""
    return 2*np.pi*np.asarray(action_offset,float)
