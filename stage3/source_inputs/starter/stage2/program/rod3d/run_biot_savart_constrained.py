"""Full coil dynamics with explicit sampled-tube field/current constraints.

The constrained set is a tube surrounding the actual lumen, not the 0.12 m
ideal-affine ball that contains the coil conductors. The field bounds remain
sampled numerical constraints, not a continuous-domain bound.
"""
from pathlib import Path
import hashlib
import json
import sys
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['MKL_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
import numpy as np
from scipy.optimize import minimize,Bounds
import model as base
import run_biot_savart as bs

ROOT=Path(__file__).resolve().parent
OUT=ROOT.parents[1]/'results'/'rod3d'
sys.path.insert(0,str(ROOT.parent))
from coil_field import CoilAllocator


def distance_to_wires(points,cfg):
    values=[]
    for center,normal in zip(cfg['centers_m'],cfg['normals']):
        d=np.atleast_2d(points)-np.array(center)
        normal=np.array(normal);axial=d@normal
        radial=np.linalg.norm(d-axial[:,None]*normal,axis=1)
        values.append(np.sqrt(axial*axial+(radial-cfg['radius_m'])**2))
    return np.stack(values,axis=1)


def sampled_tube():
    z=np.linspace(-.001,.101,43);angle=np.arange(8)*np.pi/4
    centers=np.column_stack([.0009*np.sin(2*np.pi*z/.1),.0006*np.sin(np.pi*z/.1),z])
    tangent=np.column_stack([.0009*2*np.pi/.1*np.cos(2*np.pi*z/.1),.0006*np.pi/.1*np.cos(np.pi*z/.1),np.ones_like(z)])
    tangent/=np.linalg.norm(tangent,axis=1)[:,None]
    n1=np.cross(tangent,np.array([0.,1.,0.]));n1/=np.linalg.norm(n1,axis=1)[:,None]
    n2=np.cross(tangent,n1)
    radius=.0033
    surface=centers[:,None,:]+radius*(np.cos(angle)[None,:,None]*n1[:,None,:]+np.sin(angle)[None,:,None]*n2[:,None,:])
    points=np.concatenate([centers,surface.reshape(-1,3)])
    return centers,points,radius,z[1]-z[0]


class TubeConstrainedAllocator(CoilAllocator):
    def __init__(self,config):
        super().__init__(config);self.last_time=0.
        self.wire,self.dl,self.prefactor=bs.wire_quadrature(config)
        centers,points,radius,dz=sampled_tube()
        bb=[];gg=[]
        for j in range(12):
            current=np.zeros(12);current[j]=1.
            b,g=bs.field_gradient(points,self.wire,self.dl,current,self.prefactor)
            bb.append(b);gg.append(g.reshape(len(points),9))
        self.basis_B=np.stack(bb,axis=2);self.basis_G=np.stack(gg,axis=2)
        self.b_limit=.005*.95;self.g_limit=.03*.95
        self.S=np.concatenate([np.einsum('pia,pib->pab',self.basis_B,self.basis_B)/self.b_limit**2,
                               np.einsum('pia,pib->pab',self.basis_G,self.basis_G)/self.g_limit**2])
        matrix=self.A/self.scale[:,None]
        self.H=matrix.T@matrix+1e-6*np.eye(12)
        self.design_matrix=matrix
        self.points=points
        self.solves=0;self.nonconverged=0;self.fallbacks=0;self.max_constraint_violation=0.
        lip=np.sqrt(1+(.0009*2*np.pi/.1)**2+(.0006*np.pi/.1)**2)
        self.audit=dict(sample_points=len(points),centerline_stations=len(centers),tube_radius_m=radius,
                        z_interval_m=[-.001,.101],sampled_B_limit_T=self.b_limit,sampled_G_frobenius_limit_T_per_m=self.g_limit,
                        desired_B_bound_T=.005,desired_G_bound_T_per_m=.03,
                        sampled_point_to_exact_coil_circle_min_distance_m=float(distance_to_wires(points,config).min()),
                        continuous_tube_to_wire_conservative_distance_lower_bound_m=float(distance_to_wires(centers,config).min()-radius-lip*dz/2),
                        geometry_distance_bound='distance to exact circular wires; centerline Lipschitz bound covers z between stations and radius covers the tube',
                        field_bound_scope='finite sampling only, with 5 percent margin; not a continuous field/gradient certificate',
                        excluded_ball='The 0.12m ideal-affine sphere contains these coil conductors and is not a source-free domain for the full coil field.')
        np.savez_compressed(OUT/'constrained_coil_workspace.npz',points_m=points,B_per_ampere=self.basis_B,G_flat_per_ampere=self.basis_G)

    def constraints(self,current):
        return 1.-np.einsum('a,pab,b->p',current,self.S,current,optimize=True)

    def constraint_jac(self,current):
        return -2.*np.einsum('pab,b->pa',self.S,current,optimize=True)

    def allocate(self,requested_u,time_s=None):
        dt=max(0.,float(time_s)-self.last_time)
        if dt==0:return self.A@self.currents,self.currents.copy()
        cap=self.config['slew_bound_A_s']*dt;bound=self.config['current_bound_A']
        lo=np.maximum(-bound,self.currents-cap);hi=np.minimum(bound,self.currents+cap)
        target=np.asarray(requested_u)/self.scale
        linear=self.design_matrix.T@target
        def fun(current):return .5*current@self.H@current-linear@current
        def jac(current):return self.H@current-linear
        result=minimize(fun,self.currents,jac=jac,method='SLSQP',bounds=Bounds(lo,hi),
                        constraints=[dict(type='ineq',fun=self.constraints,jac=self.constraint_jac)],
                        options=dict(ftol=1e-10,maxiter=80,disp=False))
        self.solves+=1
        if not result.success:self.nonconverged+=1
        candidate=result.x
        violation=max(0.,-float(np.min(self.constraints(candidate))),float(np.max(lo-candidate)),float(np.max(candidate-hi))) if np.isfinite(candidate).all() else np.inf
        if violation>1e-7:
            candidate=self.currents.copy();self.fallbacks+=1
        self.max_constraint_violation=max(self.max_constraint_violation,max(0.,-float(self.constraints(candidate).min())))
        self.currents=candidate;self.last_time=float(time_s)
        return self.A@self.currents,self.currents.copy()


class ConstrainedCoilEnvironment(bs.FullCoilEnvironment):
    instances=[]
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.allocator=TubeConstrainedAllocator(self.allocator.config)
        self.audit_rows=[];self.last_audit_index=-1
        self.instances.append(self)

    def apply_forces(self,system,time=0.):
        super().apply_forces(system,time)
        if self.control_index!=self.last_audit_index:
            b,g=bs.field_gradient(system.position_collection.T,self.wire,self.dl,self.currents,self.prefactor)
            self.audit_rows.append([time,float(np.linalg.norm(b,axis=1).max()),float(np.linalg.norm(g,axis=(1,2)).max()),float(distance_to_wires(system.position_collection.T,self.allocator.config).min())])
            self.last_audit_index=self.control_index


def main():
    base.Environment=ConstrainedCoilEnvironment;base.metrics_snapshot=bs.full_snapshot
    name='full_biot_savart_tube_constrained_n32_h10us'
    summary=base.run_case(name,OUT,base.load_config(ROOT/'config_position_feedback.json'),32,1e-5,2.,.005,'coil_allocated')
    env=ConstrainedCoilEnvironment.instances[-1]
    check=np.asarray(env.audit_rows)
    np.savetxt(OUT/name/'actual_field_at_control_updates.csv',check,delimiter=',',header='time_s,max_B_at_actual_nodes_T,max_G_frobenius_at_actual_nodes_T_per_m,min_distance_actual_nodes_to_wire_m',comments='')
    audit=env.allocator.audit
    audit.update(solver='SLSQP on convex quadratic objective and convex sampled norm constraints; feasibility checked after each solve',
                  allocation_calls=env.allocator.solves,optimizer_nonconverged=env.allocator.nonconverged,fallback_to_previous_feasible_current=env.allocator.fallbacks,
                  maximum_normalized_sampled_constraint_violation=env.allocator.max_constraint_violation,
                  actual_node_checks=len(check),max_actual_node_B_T=float(check[:,1].max()),max_actual_node_G_frobenius_T_per_m=float(check[:,2].max()),
                  min_actual_node_distance_to_exact_wire_m=float(check[:,3].min()))
    (OUT/name/'workspace_constraint_audit.json').write_text(json.dumps(audit,indent=2))
    summary.update(magnetic_load_evaluation='full Biot-Savart and analytical derivative with sampled-tube constrained allocation',
                   true_max_G_at_control_updates_T_per_m=float(check[:,2].max()),true_max_B_at_control_updates_T=float(check[:,1].max()),
                   field_constraints_pass_at_actual_checked_nodes=bool(check[:,1].max()<=.005 and check[:,2].max()<=.03))
    (OUT/name/'summary.json').write_text(json.dumps(summary,indent=2))
    ep=OUT/name/'environment.json';environment=json.loads(ep.read_text())
    environment.update(full_biot_savart_extension_sha256=bs.EXTENSION_SHA256,
                       tube_constrained_extension_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                       coil_field_source_sha256=hashlib.sha256((ROOT.parent/'coil_field.py').read_bytes()).hexdigest())
    ep.write_text(json.dumps(environment,indent=2))
    print(json.dumps(audit),flush=True)


if __name__=='__main__':main()
