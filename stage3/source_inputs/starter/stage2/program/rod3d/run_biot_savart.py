"""Actual coil-field dynamics, with analytical Biot-Savart spatial derivatives.

The current allocator and feedback are identical to the affine-coil branch.
Only the spatial magnetic load evaluation changes. No finite-difference field
gradient is used in the dynamics.
"""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
from numba import njit
import model as base

ROOT=Path(__file__).resolve().parent
OUT=ROOT.parents[1]/'results'/'rod3d'
EXTENSION_SHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def wire_quadrature(cfg):
    angle=(np.arange(cfg['quadrature_points'])+.5)*2*np.pi/cfg['quadrature_points']
    wire=[];dl=[]
    for center,normal in zip(cfg['centers_m'],cfg['normals']):
        normal=np.array(normal);axis=np.eye(3)[np.argmin(abs(normal))]
        e1=np.cross(normal,axis);e1/=np.linalg.norm(e1);e2=np.cross(normal,e1)
        wire.append(np.array(center)+cfg['radius_m']*(np.cos(angle)[:,None]*e1+np.sin(angle)[:,None]*e2))
        dl.append(cfg['radius_m']*2*np.pi/cfg['quadrature_points']*(-np.sin(angle)[:,None]*e1+np.cos(angle)[:,None]*e2))
    return np.asarray(wire),np.asarray(dl),1e-7*cfg['turns']


@njit(cache=True)
def field_gradient(points,wire,dl,currents,prefactor):
    fields=np.zeros((len(points),3));gradients=np.zeros((len(points),3,3))
    for p in range(len(points)):
        for c in range(len(currents)):
            coef=prefactor*currents[c]
            if coef==0.:continue
            for k in range(wire.shape[1]):
                dx=points[p,0]-wire[c,k,0];dy=points[p,1]-wire[c,k,1];dz=points[p,2]-wire[c,k,2]
                lx,ly,lz=dl[c,k,0],dl[c,k,1],dl[c,k,2]
                r2=dx*dx+dy*dy+dz*dz;inv3=1./(r2*np.sqrt(r2));inv5=inv3/r2
                cx=ly*dz-lz*dy;cy=lz*dx-lx*dz;cz=lx*dy-ly*dx
                fields[p,0]+=coef*cx*inv3;fields[p,1]+=coef*cy*inv3;fields[p,2]+=coef*cz*inv3
                gradients[p,0,0]+=coef*(-3*cx*dx*inv5)
                gradients[p,0,1]+=coef*(-lz*inv3-3*cx*dy*inv5)
                gradients[p,0,2]+=coef*(ly*inv3-3*cx*dz*inv5)
                gradients[p,1,0]+=coef*(lz*inv3-3*cy*dx*inv5)
                gradients[p,1,1]+=coef*(-3*cy*dy*inv5)
                gradients[p,1,2]+=coef*(-lx*inv3-3*cy*dz*inv5)
                gradients[p,2,0]+=coef*(-ly*inv3-3*cz*dx*inv5)
                gradients[p,2,1]+=coef*(lx*inv3-3*cz*dy*inv5)
                gradients[p,2,2]+=coef*(-3*cz*dz*inv5)
    return fields,gradients


@njit(cache=True)
def magnetic_loads(r,directors,dipole_body,alpha,wire,dl,currents,prefactor):
    n=directors.shape[2]
    forces=np.zeros((3,n+1));torques=np.zeros((3,n));potential=0.
    for e in range(n):
        if np.sum(dipole_body[:,e]**2)==0.:continue
        mu=directors[:,:,e].T@dipole_body[:,e]
        point=(1-alpha[e])*r[:,e]+alpha[e]*r[:,e+1]
        field=np.zeros(3);force=np.zeros(3)
        for c in range(len(currents)):
            coef=prefactor*currents[c]
            if coef==0.:continue
            for k in range(wire.shape[1]):
                dx=point[0]-wire[c,k,0];dy=point[1]-wire[c,k,1];dz=point[2]-wire[c,k,2]
                lx,ly,lz=dl[c,k,0],dl[c,k,1],dl[c,k,2]
                r2=dx*dx+dy*dy+dz*dz;inv3=1./(r2*np.sqrt(r2));inv5=inv3/r2
                cx=ly*dz-lz*dy;cy=lz*dx-lx*dz;cz=lx*dy-ly*dx
                field[0]+=coef*cx*inv3;field[1]+=coef*cy*inv3;field[2]+=coef*cz*inv3
                dot=mu[0]*cx+mu[1]*cy+mu[2]*cz
                force[0]+=coef*((mu[1]*lz-mu[2]*ly)*inv3-3*dot*dx*inv5)
                force[1]+=coef*((mu[2]*lx-mu[0]*lz)*inv3-3*dot*dy*inv5)
                force[2]+=coef*((mu[0]*ly-mu[1]*lx)*inv3-3*dot*dz*inv5)
        forces[:,e]+=(1-alpha[e])*force;forces[:,e+1]+=alpha[e]*force
        torques[:,e]=directors[:,:,e]@base.cross(mu,field)
        potential-=np.dot(mu,field)
    return forces,torques,potential


OriginalEnvironment=base.Environment
OriginalSnapshot=base.metrics_snapshot


class FullCoilEnvironment(OriginalEnvironment):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        if not self.coil:raise ValueError('Full Biot-Savart branch requires coil allocation')
        self.wire,self.dl,self.prefactor=wire_quadrature(self.allocator.config)

    def evaluate(self,rod,time):
        result=super().evaluate(rod,time)
        forces,torques,potential=magnetic_loads(rod.position_collection,rod.director_collection,self.dipole_body,self.dipole_alpha,self.wire,self.dl,self.currents,self.prefactor)
        result[0][0]=forces;result[1][0]=torques;result[8][1]=potential
        return result


def full_snapshot(rod,env,t,work):
    row,state=OriginalSnapshot(rod,env,t,work)
    b,g=field_gradient(rod.position_collection.T,env.wire,env.dl,env.currents,env.prefactor)
    row['B_at_nodes_affine_max_T']=row['B_at_nodes_max_T']
    row['B_at_nodes_max_T']=float(np.linalg.norm(b,axis=1).max())
    row['true_G_at_nodes_frobenius_max_T_per_m']=float(np.linalg.norm(g,axis=(1,2)).max())
    row['true_Maxwell_trace_at_nodes_max_T_per_m']=float(np.abs(np.trace(g,axis1=1,axis2=2)).max())
    row['true_Maxwell_curl_at_nodes_max_T_per_m']=float(np.linalg.norm(g-g.transpose(0,2,1),axis=(1,2)).max())
    state['field_at_nodes_T']=b;state['field_gradient_at_nodes_T_per_m']=g
    return row,state


def verify():
    import sys
    sys.path.insert(0,str(ROOT.parent))
    from coil_field import basis,make_array
    cfg=make_array();wire,dl,prefactor=wire_quadrature(cfg)
    points=np.array([[.001,-.0005,.096],[.0013,.0007,.099]])
    currents=np.linspace(-.7,.9,12)
    fields,grad=field_gradient(points,wire,dl,currents,prefactor)
    reference=basis(points,cfg)@currents
    eps=1e-7
    finite=np.stack([(basis(points+eps*np.eye(3)[j],cfg)-basis(points-eps*np.eye(3)[j],cfg))@currents/(2*eps) for j in range(3)],axis=2)
    _,rod,env=base.make_model(base.load_config(ROOT/'config_position_feedback.json'),32,2,coil=True)
    rod.position_collection[0]+=np.linspace(0,.001,33);env.currents=currents
    f,tau,energy=magnetic_loads(rod.position_collection,rod.director_collection,env.dipole_body,env.dipole_alpha,wire,dl,currents,prefactor)
    node=31;axis=np.array([.3,-.4,.5]);axis/=np.linalg.norm(axis)
    rod.position_collection[:,node]+=eps*axis
    ep=magnetic_loads(rod.position_collection,rod.director_collection,env.dipole_body,env.dipole_alpha,wire,dl,currents,prefactor)[2]
    rod.position_collection[:,node]-=2*eps*axis
    em=magnetic_loads(rod.position_collection,rod.director_collection,env.dipole_body,env.dipole_alpha,wire,dl,currents,prefactor)[2]
    derivative=(ep-em)/(2*eps);predicted=-f[:,node]@axis
    result=dict(field_vs_independent_numpy_relative_error=float(np.linalg.norm(fields-reference)/np.linalg.norm(reference)),
                analytic_gradient_vs_finite_difference_relative_error=float(np.linalg.norm(grad-finite)/np.linalg.norm(finite)),
                magnetic_force_virtual_work_relative_error=float(abs(derivative-predicted)/max(abs(derivative),abs(predicted))),
                divergence_max=float(abs(np.trace(grad,axis1=1,axis2=2)).max()),
                curl_defect_max=float(abs(grad-grad.transpose(0,2,1)).max()),
                extension_sha256=EXTENSION_SHA256)
    assert result['field_vs_independent_numpy_relative_error']<1e-12
    assert result['analytic_gradient_vs_finite_difference_relative_error']<1e-6
    assert result['magnetic_force_virtual_work_relative_error']<1e-6
    (OUT/'biot_savart_operator_verification.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result),flush=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--elements',nargs='*',type=int,default=[32,64]);args=parser.parse_args()
    verify()
    base.Environment=FullCoilEnvironment;base.metrics_snapshot=full_snapshot
    summaries=[]
    for n in args.elements:
        name=f'full_biot_savart_coils_n{n}_h'+('10us' if n==32 else '5us')
        summary=base.run_case(name,OUT,base.load_config(ROOT/'config_position_feedback.json'),n,1e-5 if n==32 else 5e-6,2.,.005,'coil_allocated')
        summary['magnetic_load_evaluation']='full 256-point/coil Biot-Savart quadrature, analytic spatial derivative, instantaneous actual rod positions and body-fixed dipoles'
        data=np.genfromtxt(OUT/name/'diagnostics.csv',delimiter=',',names=True)
        summary['true_max_G_at_rod_nodes_T_per_m']=float(data['true_G_at_nodes_frobenius_max_T_per_m'].max())
        summary['max_full_field_Maxwell_divergence_T_per_m']=float(data['true_Maxwell_trace_at_nodes_max_T_per_m'].max())
        summary['max_full_field_Maxwell_curl_defect_T_per_m']=float(data['true_Maxwell_curl_at_nodes_max_T_per_m'].max())
        (OUT/name/'summary.json').write_text(json.dumps(summary,indent=2))
        ep=OUT/name/'environment.json';environment=json.loads(ep.read_text())
        environment['full_biot_savart_extension_sha256']=EXTENSION_SHA256
        environment['coil_field_source_sha256']=hashlib.sha256((ROOT.parent/'coil_field.py').read_bytes()).hexdigest()
        ep.write_text(json.dumps(environment,indent=2))
        summaries.append(summary)
        (OUT/'full_biot_savart_summaries.json').write_text(json.dumps(summaries,indent=2))


if __name__=='__main__':main()
