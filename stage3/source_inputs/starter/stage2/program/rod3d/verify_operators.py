"""Independent variational/frame checks for the magnetic/contact interfaces."""
from pathlib import Path
import json
import numpy as np
from scipy.spatial.transform import Rotation
from model import load_config,make_model,command,unpack_field


def main():
    cfg=load_config()
    _,rod,env=make_model(cfg,32,4)
    t=.137
    original=rod.position_collection.copy()
    direct=rod.director_collection.copy()
    rng=np.random.default_rng(102529)
    # Use a three-dimensional frame, not only the initial identity orientation.
    rod.director_collection[:]=np.einsum('ij,jke->ike',Rotation.from_rotvec([.04,-.03,.02]).as_matrix().T,direct)
    f,tau,*_=env.evaluate(rod,t)
    node=31
    axis=np.array([.37,-.49,.79]);axis/=np.linalg.norm(axis)
    eps=1e-8
    rod.position_collection[:,node]+=eps*axis
    ep=env.evaluate(rod,t)[8][1]
    rod.position_collection[:,node]-=2*eps*axis
    em=env.evaluate(rod,t)[8][1]
    rod.position_collection[:]=original
    derivative=(ep-em)/(2*eps)
    predicted=-float(f[0,:,node]@axis)
    magnetic_force_error=abs(derivative-predicted)/max(abs(derivative),abs(predicted),1e-20)
    e=31
    direct=rod.director_collection.copy()
    epsr=1e-6
    rod.director_collection[:,:,e]=direct[:,:,e]@Rotation.from_rotvec(-epsr*axis).as_matrix()
    ep=env.evaluate(rod,t)[8][1]
    rod.director_collection[:,:,e]=direct[:,:,e]@Rotation.from_rotvec(epsr*axis).as_matrix()
    em=env.evaluate(rod,t)[8][1]
    rod.director_collection[:]=direct
    derivative=(ep-em)/(2*epsr)
    predicted=-float(tau[0,:,e]@(direct[:,:,e]@axis))
    magnetic_torque_error=abs(derivative-predicted)/max(abs(derivative),abs(predicted),1e-20)

    # Contact energy finite differences check force assembly and closest-point normal.
    rod.position_collection[0,:]+=.004
    contact_original=rod.position_collection.copy()
    val=env.evaluate(rod,t)
    node=20
    eps=1e-8
    rod.position_collection[:,node]+=eps*axis
    ep=env.evaluate(rod,t)[8][0]
    rod.position_collection[:,node]-=2*eps*axis
    em=env.evaluate(rod,t)[8][0]
    rod.position_collection[:]=contact_original
    derivative=(ep-em)/(2*eps)
    predicted=-float(val[0][2,:,node]@axis)
    contact_force_error=abs(derivative-predicted)/max(abs(derivative),abs(predicted),1e-20)
    rod.velocity_collection[:]=rng.normal(scale=.01,size=rod.velocity_collection.shape)
    rod.omega_collection[:]=rng.normal(scale=.1,size=rod.omega_collection.shape)
    val=env.evaluate(rod,t)
    dissipative_power=float(np.sum(val[0][3]*rod.velocity_collection)+np.sum(val[1][3]*rod.omega_collection))
    force_angular_power=float(np.sum(val[1][0]*rod.omega_collection))
    mu=np.einsum('jie,je->ie',rod.director_collection,env.dipole_body)
    omega_sp=np.einsum('jie,je->ie',rod.director_collection,rod.omega_collection)
    _,u,_,_=command(rod.position_collection,rod.velocity_collection,t,env.p,4)
    b,g=unpack_field(u)
    centers=(1-env.dipole_alpha)*rod.position_collection[:,:-1]+env.dipole_alpha*rod.position_collection[:,1:]
    bf=b[:,None]+g@(centers-np.array([0.,0.,.1])[:,None])
    space_angular_power=float(np.sum(np.cross(mu.T,bf.T).T*omega_sp))
    frame_power_error=abs(force_angular_power-space_angular_power)/max(abs(force_angular_power),abs(space_angular_power),1e-20)
    dipole_checks=[]
    for n in [16,32,64]:
        _,rd,en=make_model(cfg,n,0)
        dipole_checks.append(dict(elements=n,moment_A_m2=float(np.linalg.norm(en.dipole_body,axis=0).sum()),
                                 rotary_inertia_condition=float(np.linalg.cond(rd.mass_second_moment_of_inertia[:,:,0]))))
    result=dict(magnetic_force_virtual_work_relative_error=magnetic_force_error,
                magnetic_torque_virtual_work_relative_error=magnetic_torque_error,
                contact_elastic_force_virtual_work_relative_error=contact_force_error,
                material_spatial_torque_power_relative_error=frame_power_error,
                contact_dissipative_power_W=dissipative_power,
                Coulomb_inequality_excess_N=float(val[8][2]),
                gradient_trace_T_per_m=float(np.trace(g)),gradient_curl_defect_T_per_m=float(np.linalg.norm(g-g.T)),
                exact_partial_element_magnetization=dipole_checks,
                scope="finite-difference and algebraic verification of implemented operators; not clinical or full-PDE validation")
    assert magnetic_force_error<2e-6
    assert magnetic_torque_error<2e-6
    assert contact_force_error<2e-6
    assert frame_power_error<1e-12
    assert dissipative_power<=1e-15
    assert val[8][2]<=1e-15
    assert all(abs(x['moment_A_m2']-.000724)<1e-15 for x in dipole_checks)
    out=Path(__file__).resolve().parents[2]/'results'/'rod3d'
    out.mkdir(parents=True,exist_ok=True)
    (out/'operator_verification.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
