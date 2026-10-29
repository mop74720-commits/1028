"""Local Womersley profile sensitivity at the same prescribed volume flow.

This is an exact fully-developed straight rigid-tube harmonic profile mapped
onto the curved lumen tangent; it is not a curved-tube Navier-Stokes solution.
"""
from pathlib import Path
import hashlib
import json
import model as base
import numpy as np
from numba import njit
from scipy.special import jv

ROOT=Path(__file__).resolve().parent
OUT=ROOT.parents[1]/'results'/'rod3d'


def lookup(cfg):
    flow=cfg['flow'];radius=cfg['lumen']['radius_m']
    omega=2*np.pi*flow['frequency_Hz']
    alpha=radius*np.sqrt(omega*flow['density_kg_m3']/flow['viscosity_Pa_s'])
    lam=np.sqrt(-1j)*alpha
    rho=np.linspace(0,1,4097)
    f=1-jv(0,lam*rho)/jv(0,lam)
    fbar=1-2*jv(1,lam)/(lam*jv(0,lam))
    beta=f/fbar
    avg=.5*flow['peak_centerline_speed_m_s']
    amp=avg*flow['pulsation_fraction']
    phases=np.linspace(0,2*np.pi,129)
    mean=[]
    for phase in phases:
        u=2*avg*(1-rho*rho)+amp*(beta.real*np.sin(phase)+beta.imag*np.cos(phase))
        mean.append(2*np.trapezoid(rho*u,rho))
    expected=avg+amp*np.sin(phases)
    rng=np.random.default_rng(102529);test=rng.uniform(0,1,1000)
    exact=(1-jv(0,lam*test)/jv(0,lam))/fbar
    interpolated=np.interp(test,rho,beta.real)+1j*np.interp(test,rho,beta.imag)
    # Independently differentiate the sampled harmonic velocity twice in radius.
    radial=rho*radius;uhat=-1j*amp*beta
    first=np.gradient(uhat,radial,edge_order=2);second=np.gradient(first,radial,edge_order=2)
    pressure_hat=1j*flow['density_kg_m3']*omega*(-1j*amp/fbar)
    interior=slice(4,-4)
    residual=1j*flow['density_kg_m3']*omega*uhat[interior]-flow['viscosity_Pa_s']*(second[interior]+first[interior]/radial[interior])-pressure_hat
    result=dict(alpha=float(alpha),lambda_real=float(lam.real),lambda_imag=float(lam.imag),radial_points=len(rho),
                mean_velocity_m_s=avg,harmonic_mean_velocity_amplitude_m_s=amp,
                no_slip_velocity_max_m_s=float(abs(amp*beta[-1])),
                mean_velocity_integral_max_absolute_error_m_s=float(np.max(np.abs(np.asarray(mean)-expected))),
                volume_flow_max_absolute_error_m3_s=float(np.pi*radius**2*np.max(np.abs(np.asarray(mean)-expected))),
                table_relative_max_complex_shape_error=float(np.max(abs(exact-interpolated))/np.max(abs(exact))),
                finite_difference_straight_tube_NS_relative_residual=float(np.max(abs(residual))/abs(pressure_hat)),
                center_harmonic_shape_real=float(beta[0].real),center_harmonic_shape_imag=float(beta[0].imag),
                center_harmonic_phase_relative_to_mean_rad=float(np.angle(beta[0])),
                pressure_gradient_harmonic_amplitude_Pa_per_m=float(abs(pressure_hat)),
                source='J.R. Womersley (1955), J Physiol127:553-563, DOI10.1113/jphysiol.1955.sp005276; harmonic flow normalized here to the prescribed mean flux',
                scope='straight fully-developed Newtonian rigid-tube solution; curved-tangent mapping is a local approximation')
    assert result['no_slip_velocity_max_m_s']<1e-12
    assert result['mean_velocity_integral_max_absolute_error_m_s']<1e-8
    assert result['table_relative_max_complex_shape_error']<1e-6
    assert result['finite_difference_straight_tube_NS_relative_residual']<1e-4
    np.savetxt(OUT/'womersley_lookup.csv',np.column_stack([rho,beta.real,beta.imag]),delimiter=',',header='radius_fraction,beta_real,beta_imag',comments='')
    (OUT/'womersley_profile_verification.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result),flush=True)
    return rho,beta.real.copy(),beta.imag.copy()


@njit(cache=True)
def flow_loads(r,v,directors,omega,lengths,radii,t,p,table):
    n=len(lengths);forces=np.zeros((3,n+1));torques=np.zeros((3,n));dissipation=0.
    rg,re,im=table
    phase=2*np.pi*p[base.UFREQ]*t
    for e in range(n):
        xmid=.5*(r[:,e]+r[:,e+1]);vmid=.5*(v[:,e]+v[:,e+1])
        tangent=(r[:,e+1]-r[:,e])/lengths[e]
        wsp=directors[:,:,e].T@omega[:,e]
        _,ft,_,radial=base.lumen_projection(xmid,p)
        fraction=min(max(radial/p[base.RV],0.),1.)
        velocity=p[base.U0]*(1-fraction*fraction)+.5*p[base.U0]*p[base.UPULSE]*(np.interp(fraction,rg,re)*np.sin(phase)+np.interp(fraction,rg,im)*np.cos(phase))
        relative=velocity*ft-vmid
        parallel=np.dot(relative,tangent)*tangent;perpendicular=relative-parallel
        speed=np.sqrt(np.dot(perpendicular,perpendicular));logslender=np.log(2*p[base.L]/radii[e])
        cp=4*np.pi*p[base.ETA]/(logslender+.5);ca=2*np.pi*p[base.ETA]/(logslender-.5)
        resistance=cp*perpendicular+ca*parallel+p[base.FRHO]*p[base.CD]*radii[e]*speed*perpendicular
        force=resistance*lengths[e];forces[:,e]+=.5*force;forces[:,e+1]+=.5*force
        spin=np.dot(wsp,tangent);torque=-4*np.pi*p[base.ETA]*radii[e]**2*lengths[e]*spin*tangent
        torques[:,e]=directors[:,:,e]@torque
        dissipation+=np.dot(resistance,relative)*lengths[e]+4*np.pi*p[base.ETA]*radii[e]**2*lengths[e]*spin**2
    return forces,torques,dissipation


OriginalEnvironment=base.Environment


class WomersleyEnvironment(OriginalEnvironment):
    table=None
    def evaluate(self,rod,time):
        result=super().evaluate(rod,time)
        f,tau,dissipation=flow_loads(rod.position_collection,rod.velocity_collection,rod.director_collection,rod.omega_collection,
                                    rod.lengths,rod.radius,float(time),self.p,self.table)
        result[0][1]=f;result[1][1]=tau;result[8][3]=dissipation
        return result


def main():
    cfg=base.load_config(ROOT/'config_position_feedback.json')
    cfg['flow']['profile']='local Womersley harmonic with identical mean flow Q(t); 4097-point radial table'
    cfg['flow']['closure']='Local exact straight-tube Womersley velocity mapped to curved-tube tangent; identical anisotropic drag/spin resistance; not full curved-flow NS or FSI'
    WomersleyEnvironment.table=lookup(cfg)
    base.Environment=WomersleyEnvironment
    name='womersley_position_feedback_n32_h10us'
    base.run_case(name,OUT,cfg,32,1e-5,2.,.005,'feedback')
    ep=OUT/name/'environment.json';environment=json.loads(ep.read_text())
    environment['womersley_extension_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    ep.write_text(json.dumps(environment,indent=2))


if __name__=='__main__':main()
