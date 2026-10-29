"""Current-space allocation and continuous ramps for full-coil ROM dynamics.

Allocation constrains actual magnetic quadrature points at the decision state.
It is not a continuum workspace certificate. Along a ramp the frozen spatial
constraints are convex; moving-point violations must be independently checked.
"""
from __future__ import annotations
import numpy as np
import torch
from scipy.optimize import minimize


class CurrentAllocator:
    def __init__(self,model,field_bound_T=.005,gradient_bound_T_per_m=.03):
        self.model=model
        self.field_bound=field_bound_T
        self.gradient_bound=gradient_bound_T_per_m

    def allocate(self,Q,requested,previous,physical_interval_s):
        if physical_interval_s<=0:
            raise ValueError('A positive physical interval is required for current slew bounds')
        model=self.model
        previous=np.asarray(previous);requested=np.asarray(requested)
        cap=model.coil_config['slew_bound_A_s']*physical_interval_s
        bound=model.coil_config['current_bound_A']
        lo=np.maximum(-bound,previous-cap);hi=np.minimum(bound,previous+cap)
        with torch.no_grad():
            points,_=model.magnetic_geometry_tensor(model.tensor(Q))
            b,g=model.field_basis_tensor(points,gradient=True)
        b=b.numpy();g=g.numpy().reshape(len(points),9,model.current_channels)
        # Keep B and G as separate Euclidean norm constraints, not a combined one.
        def constraints(current):
            return np.r_[1-np.sum((b@current/self.field_bound)**2,axis=1),
                         1-np.sum((g@current/self.gradient_bound)**2,axis=1)]
        def constraint_jac(current):
            return np.vstack((-2*np.einsum('pa,paj->pj',b@current,b)/self.field_bound**2,
                              -2*np.einsum('pa,paj->pj',g@current,g)/self.gradient_bound**2))
        candidate=np.clip(requested,lo,hi)
        success=True;message='Box projection already satisfies all magnetic-point field constraints';iterations=0
        if constraints(candidate).min() < -1e-12:
            sol=minimize(lambda x:.5*np.sum((x-requested)**2),np.clip(previous,lo,hi),jac=lambda x:x-requested,
                         bounds=list(zip(lo,hi)),method='SLSQP',
                         constraints=[dict(type='ineq',fun=constraints,jac=constraint_jac)],
                         options={'ftol':1e-13,'maxiter':300,'disp':False})
            candidate=sol.x;success=bool(sol.success);message=sol.message;iterations=int(sol.nit)
        violation=max(0.,float(-constraints(candidate).min()),float((lo-candidate).max()),float((candidate-hi).max()))
        if not success or violation>1e-9:
            # Failing constraints is a result, never a silently accepted input.
            raise RuntimeError(f'Current allocation failed: {message}; violation={violation:.3e}')
        gcoil=model.current_port(Q)
        return candidate,dict(success=success,message=str(message),iterations=iterations,
            physical_interval_s=physical_interval_s,current_request_distance_A=float(np.linalg.norm(candidate-requested)),
            generalized_force_allocation_residual=float(np.linalg.norm(gcoil@(candidate-requested))),
            constraint_violation=violation,active_magnetic_points=len(points),
            maximum_planned_slew_A_s=float(np.max(np.abs(candidate-previous)/physical_interval_s)),
            requested_current_A=requested.tolist(),allocated_current_A=candidate.tolist(),
            field_constraints_scope='Decision-state magnet quadrature points; convex along each ramp at these fixed points only')

    def allocate_force(self,Q,desired_increment,previous,physical_interval_s,rcond=1e-8):
        """Minimize true generalized-force residual under current/field limits.

        Desired force is additional to the fixed total-bias force, in Pdot units.
        Orthogonal unreachability is reported independently of constrained error.
        All 12 current columns share ampere units; no 8-field unit scaling is used.
        """
        model=self.model;desired=np.asarray(desired_increment);previous=np.asarray(previous)
        if physical_interval_s<=0:
            raise ValueError('Positive physical interval required')
        port=model.current_port(Q)
        singular=np.linalg.svd(port,compute_uv=False)
        pinv=np.linalg.pinv(port,rcond=rcond)
        requested=model.bias_currents+pinv@desired
        cap=model.coil_config['slew_bound_A_s']*physical_interval_s
        bound=model.coil_config['current_bound_A']
        lo=np.maximum(-bound,previous-cap);hi=np.minimum(bound,previous+cap)
        with torch.no_grad():
            points,_=model.magnetic_geometry_tensor(model.tensor(Q))
            b,g=model.field_basis_tensor(points,gradient=True)
        b=b.numpy();g=g.numpy().reshape(len(points),9,model.current_channels)
        def constraints(i):
            return np.r_[1-np.sum((b@i/self.field_bound)**2,axis=1),1-np.sum((g@i/self.gradient_bound)**2,axis=1)]
        def jac_constraints(i):
            return np.vstack((-2*np.einsum('pa,paj->pj',b@i,b)/self.field_bound**2,
                              -2*np.einsum('pa,paj->pj',g@i,g)/self.gradient_bound**2))
        # A near-null force singular vector can produce a huge pseudoinverse
        # current request although the previous current is already feasible.
        # Do not solve that unrelated, ill-scaled current-projection problem
        # just to initialize the actual force objective.
        if constraints(previous).min()>=-1e-12 and np.all(previous>=lo) and np.all(previous<=hi):
            seed=previous.copy();seed_policy='previous verified feasible at current magnetic points'
        else:
            seed,warm=self.allocate(Q,requested,previous,physical_interval_s)
            seed_policy='feasible current projection required because previous is infeasible at new state'
        # Scaling the objective does not change its minimizer and prevents tiny
        # canonical force targets from causing premature absolute-ftol stopping.
        scale=max(float(np.linalg.norm(desired)),1e-6)
        matrix=port/scale;rhs=(port@model.bias_currents+desired)/scale
        solution=minimize(lambda i:.5*np.sum((matrix@i-rhs)**2),seed,
            jac=lambda i:matrix.T@(matrix@i-rhs),bounds=list(zip(lo,hi)),method='SLSQP',
            constraints=[dict(type='ineq',fun=constraints,jac=jac_constraints)],
            options={'ftol':1e-12,'maxiter':500,'disp':False})
        i=solution.x
        violation=max(0.,float(-constraints(i).min()),float((lo-i).max()),float((i-hi).max()))
        if not solution.success or violation>1e-9:
            raise RuntimeError(f'Force-space allocation failed: {solution.message}; violation={violation}')
        residual=port@(i-model.bias_currents)-desired
        unreachable=port@pinv@desired-desired
        return i,dict(success=bool(solution.success),message=solution.message,iterations=int(solution.nit),
            seed_policy=seed_policy,
            allocation_objective='least squares of Gcoil(Q)(i-i_bias)-desired_force, in fixed canonical Pdot norm',
            desired_force_increment=desired.tolist(),achieved_force_increment=(port@(i-model.bias_currents)).tolist(),
            orthogonal_unreachable_residual=float(np.linalg.norm(unreachable)),
            constrained_force_residual=float(np.linalg.norm(residual)),
            generalized_force_allocation_residual=float(np.linalg.norm(residual)),
            rank_rcond=rcond,rank=int(np.sum(singular>rcond*singular[0])),singular_values=singular.tolist(),
            current_request_distance_A=float(np.linalg.norm(i-requested)),
            requested_current_A=requested.tolist(),allocated_current_A=i.tolist(),
            maximum_planned_slew_A_s=float(np.max(abs(i-previous)/physical_interval_s)),
            constraint_violation=violation,physical_interval_s=physical_interval_s,
            active_magnetic_points=len(points),
            field_constraints_scope='Decision-state actual magnet quadrature points; moving-point checks separate')


def ramp_current(start,target,tau,begin,end):
    """Continuous interpolation; derivative bound uses seconds in allocation."""
    theta=np.clip((tau-begin)/(end-begin),0.,1.)
    return (1-theta)*start+theta*target
