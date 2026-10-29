"""Full 3D Cosserat benchmark on official PyElastica 1.0.0.

SI throughout. Directors map spatial vectors to material coordinates. Forces
are nodal spatial vectors; couples are integrated material-frame torques.
The environmental closures are explicitly chosen benchmark models, not FSI.
"""
from __future__ import annotations

import copy
import csv
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import time as clock

ROOT = Path(__file__).resolve().parent
MODEL_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
os.environ.setdefault("NUMBA_CACHE_DIR", str(ROOT / "cache_numba"))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "cache_matplotlib"))
os.environ.setdefault("OMP_NUM_THREADS", "1")

import numpy as np
from numba import njit
from elastica import BaseSystemCollection, Constraints, Forcing, CosseratRod, OneEndFixedBC, NoForces, PositionVerlet


def load_config(path=None):
    return json.loads(Path(path or ROOT / "config.json").read_text())


# Parameter-vector indices are fixed here and recorded by pack_parameters.
L, RAD, E, G, RHO, GAMMA, MLEN, MLINE = range(8)
BFMAX, GFMAX, WSR, BIAS, FRHO, ETA, U0, UPULSE, UFREQ, CD = range(8, 18)
RV, AX, AY, KH, EXP, ZETA, MUFR, VEPS = range(18, 26)
GX, GY, GZ, GAMP, GFREQ, KP, KD, SHARE, RAMP, TFREQ = range(26, 36)
TX, TY, TAX, TAY, FLOWON, WALLON, GRAVON, CB, CG = range(36, 45)


def pack_parameters(c):
    r, m, f, w, g, k = (c[x] for x in ("rod", "magnet", "flow", "lumen", "microgravity", "controller"))
    length = r["length_m"]
    a = length - m["distal_length_m"]
    ei = r["young_modulus_Pa"] * np.pi * r["radius_m"] ** 4 / 4
    # Small-deflection response to a distributed distal axial dipole.
    cb = m["line_dipole_A_m"] / ei * ((length**3/2-length**3/6)-(length*a*a/2-a**3/6))
    cg = m["line_dipole_A_m"] / ei * ((length**4/6-length**4/24)-(length*a**3/6-a**4/24))
    return np.array([
        length, r["radius_m"], r["young_modulus_Pa"], r["shear_modulus_Pa"], r["density_kg_m3"], r["mass_proportional_damping_rate_s_inv"],
        m["distal_length_m"], m["line_dipole_A_m"], m["B_workspace_bound_T"], m["gradient_frobenius_bound_T_per_m"], m["workspace_radius_m"], m["bias_z_T"],
        f["density_kg_m3"], f["viscosity_Pa_s"], f["peak_centerline_speed_m_s"], f["pulsation_fraction"], f["frequency_Hz"], f["quadratic_drag_coefficient"],
        w["radius_m"], w["centerline_x_amplitude_m"], w["centerline_y_amplitude_m"], w["contact_penalty_N_per_m_power_2p5"], w["contact_exponent"], w["normal_damping_ratio"], w["friction_coefficient"], w["friction_velocity_regularization_m_s"],
        *g["residual_vector_m_s2"], g["jitter_amplitude_m_s2"], g["jitter_frequency_Hz"], k["position_error_gain"], k["velocity_error_gain_s"], k["uniform_field_share"], k["target_ramp_s"], k["target_frequency_Hz"],
        *k["target_base_xy_m"], *k["target_amplitude_xy_m"], float(f["enabled"]), float(w["enabled"]), float(g["enabled"]), cb, cg,
    ], dtype=np.float64)


@njit(cache=True)
def cross(a, b):
    return np.array([a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]])


@njit(cache=True)
def lumen_projection(x, p):
    z = x[2]
    kx = 2*np.pi/p[L]
    ky = np.pi/p[L]
    for _ in range(6):
        cx, cy = p[AX]*np.sin(kx*z), p[AY]*np.sin(ky*z)
        dx, dy = p[AX]*kx*np.cos(kx*z), p[AY]*ky*np.cos(ky*z)
        ddx, ddy = -p[AX]*kx*kx*np.sin(kx*z), -p[AY]*ky*ky*np.sin(ky*z)
        fun = (cx-x[0])*dx+(cy-x[1])*dy+z-x[2]
        deriv = 1+dx*dx+dy*dy+(cx-x[0])*ddx+(cy-x[1])*ddy
        z -= fun/deriv
    center = np.array([p[AX]*np.sin(kx*z), p[AY]*np.sin(ky*z), z])
    tangent = np.array([p[AX]*kx*np.cos(kx*z), p[AY]*ky*np.cos(ky*z), 1.])
    tangent /= np.sqrt(np.dot(tangent, tangent))
    delta = x-center
    distance = np.sqrt(np.dot(delta, delta))
    normal = delta/max(distance, 1e-30)
    return center, tangent, normal, distance


@njit(cache=True)
def reference(t, p, mode):
    x = min(max(t/p[RAMP], 0.), 1.)
    ramp = x*x*(3-2*x)
    dr = 6*x*(1-x)/p[RAMP] if 0<x<1 else 0.
    w = 2*np.pi*p[TFREQ]
    xx = p[TX]+p[TAX]*np.sin(w*t)
    yy = p[TY]+p[TAY]*np.sin(w*t+np.pi/3)
    vx, vy = p[TAX]*w*np.cos(w*t), p[TAY]*w*np.cos(w*t+np.pi/3)
    if mode == 3:  # Deliberately infeasible wall/actuator stress test.
        xx, yy, vx, vy = .02, .01, 0., 0.
    return np.array([ramp*xx, ramp*yy, p[L]]), np.array([dr*xx+ramp*vx, dr*yy+ramp*vy, 0.])


@njit(cache=True)
def unpack_field(u):
    grad = np.array([[u[3], u[5], u[6]], [u[5], u[4], u[7]], [u[6], u[7], -u[3]-u[4]]])
    return u[:3].copy(), grad


@njit(cache=True)
def limit_command(raw, p):
    u = raw.copy()
    b, grad = unpack_field(u)
    gn = np.sqrt(np.sum(grad*grad))
    if gn > p[GFMAX]:
        u[3:] *= p[GFMAX]/gn
    b, grad = unpack_field(u)
    bound = np.sqrt(np.dot(b,b))+p[WSR]*np.sqrt(np.sum(grad*grad))
    if bound > p[BFMAX]:
        u *= p[BFMAX]/bound
    return u


@njit(cache=True)
def command(r, v, t, p, mode):
    target, target_v = reference(t, p, mode)
    u = np.zeros(8)
    if mode in (1, 2, 3):
        dx, dy = target[0], target[1]
        if mode in (2, 3):
            dx += p[KP]*(target[0]-r[0,-1])+p[KD]*(target_v[0]-v[0,-1])
            dy += p[KP]*(target[1]-r[1,-1])+p[KD]*(target_v[1]-v[1,-1])
        u[0], u[1] = p[SHARE]*dx/p[CB], p[SHARE]*dy/p[CB]
        u[2] = p[BIAS]
        u[6], u[7] = (1-p[SHARE])*dx/p[CG], (1-p[SHARE])*dy/p[CG]
    elif mode == 4:
        amp = np.array([.00015, .00012, .00010, .0004, .0003, .0003, .001, .0008])
        freq = np.array([.6, .9, 1.3, .7, 1.1, 1.4, .8, 1.6])
        for i in range(8):
            u[i] = amp[i]*np.sin(2*np.pi*freq[i]*t)
        u[2] += p[BIAS]
    raw = u.copy()
    return raw, limit_command(raw,p), target, target_v


@njit(cache=True)
def environmental_forces(r, v, directors, omega, lengths, radii, rest_lengths, volume, mass, inertia_diag,
                         dipole_body, dipole_alpha, t, p, mode, override, raw_override, use_override):
    n = len(rest_lengths)
    forces = np.zeros((6,3,n+1))
    torques = np.zeros((6,3,n))
    raw, u, target, target_v = command(r,v,t,p,mode)
    if use_override:
        u = override.copy()
        raw = raw_override.copy()
    b0, grad = unpack_field(u)
    origin = np.array([0.,0.,p[L]])
    contact_normal = np.zeros(n)
    penetration = np.zeros(n)
    contact_energy, magnetic_energy = 0., 0.
    friction_excess = 0.
    relative_flow_dissipation = 0.
    g = np.array([p[GX],p[GY]+p[GAMP]*np.sin(2*np.pi*p[GFREQ]*t),p[GZ]+p[GAMP]*np.cos(2*np.pi*.7*p[GFREQ]*t)])
    gauss = np.array([.5-.5/np.sqrt(3.), .5+.5/np.sqrt(3.)])
    for e in range(n):
        # Piecewise-constant material dipole; exact overlap with the distal 5mm.
        mu = np.zeros(3)
        for i in range(3):
            for j in range(3):
                mu[i] += directors[j,i,e]*dipole_body[j,e]
        alpha = dipole_alpha[e]
        xmag = (1-alpha)*r[:,e]+alpha*r[:,e+1]
        field = b0+grad@(xmag-origin)
        fm = grad.T@mu
        tm = cross(mu,field)
        magnetic_energy -= np.dot(mu,field)
        forces[0,:,e] += (1-alpha)*fm
        forces[0,:,e+1] += alpha*fm
        torques[0,:,e] += directors[:,:,e]@tm

        xmid = .5*(r[:,e]+r[:,e+1])
        vmid = .5*(v[:,e]+v[:,e+1])
        tangent = (r[:,e+1]-r[:,e])/lengths[e]
        wsp = directors[:,:,e].T@omega[:,e]
        if p[FLOWON] > .5:
            _, ft, _, radial = lumen_projection(xmid,p)
            profile = max(0.,1-(radial/p[RV])**2)
            uf = p[U0]*(1+p[UPULSE]*np.sin(2*np.pi*p[UFREQ]*t))*profile*ft
            wr = uf-vmid
            parallel = np.dot(wr,tangent)*tangent
            perpendicular = wr-parallel
            speed = np.sqrt(np.dot(perpendicular,perpendicular))
            logslender = np.log(2*p[L]/radii[e])
            cp = 4*np.pi*p[ETA]/(logslender+.5)
            ca = 2*np.pi*p[ETA]/(logslender-.5)
            resistance = cp*perpendicular+ca*parallel+p[FRHO]*p[CD]*radii[e]*speed*perpendicular
            ff = resistance*lengths[e]
            forces[1,:,e] += .5*ff
            forces[1,:,e+1] += .5*ff
            spin = np.dot(wsp,tangent)
            tf = -4*np.pi*p[ETA]*radii[e]**2*lengths[e]*spin*tangent
            torques[1,:,e] += directors[:,:,e]@tf
            relative_flow_dissipation += np.dot(resistance,wr)*lengths[e] + 4*np.pi*p[ETA]*radii[e]**2*lengths[e]*spin**2

        if p[WALLON] > .5:
            for alpha_c in gauss:
                xc = (1-alpha_c)*r[:,e]+alpha_c*r[:,e+1]
                vc = (1-alpha_c)*v[:,e]+alpha_c*v[:,e+1]
                _, _, normal, distance = lumen_projection(xc,p)
                pen = max(0.,distance-(p[RV]-p[RAD]))
                penetration[e] = max(penetration[e],pen)
                if pen > 0.:
                    weight = .5*rest_lengths[e]
                    fn = p[KH]*pen**p[EXP]*weight
                    contact_energy += p[KH]/(p[EXP]+1)*pen**(p[EXP]+1)*weight
                    arm = p[RAD]*normal
                    surface_v = vc+cross(wsp,arm)
                    vn = np.dot(surface_v,normal)
                    kt = p[EXP]*p[KH]*pen**(p[EXP]-1)
                    cn = 2*p[ZETA]*np.sqrt(p[RHO]*np.pi*p[RAD]**2*kt)*weight
                    fdn = cn*max(vn,0.)
                    vt = surface_v-vn*normal
                    speed = np.sqrt(np.dot(vt,vt))
                    ff = -p[MUFR]*(fn+fdn)*np.tanh(speed/p[VEPS])*vt/max(speed,1e-30)
                    fel = -fn*normal
                    fdis = -fdn*normal+ff
                    forces[2,:,e] += (1-alpha_c)*fel
                    forces[2,:,e+1] += alpha_c*fel
                    forces[3,:,e] += (1-alpha_c)*fdis
                    forces[3,:,e+1] += alpha_c*fdis
                    torques[3,:,e] += directors[:,:,e]@cross(arm,ff)
                    contact_normal[e] += fn+fdn
                    friction_excess = max(friction_excess,np.sqrt(np.dot(ff,ff))-p[MUFR]*(fn+fdn))

        if p[GRAVON] > .5:
            density_diff = p[RHO] - (p[FRHO] if p[FLOWON]>.5 else 0.)
            fg = density_diff*volume[e]*g
            forces[4,:,e] += .5*fg
            forces[4,:,e+1] += .5*fg
        for i in range(3):
            torques[5,i,e] = -p[GAMMA]*inertia_diag[i,e]*omega[i,e]/(lengths[e]/rest_lengths[e])
    for j in range(n+1):
        for i in range(3):
            forces[5,i,j] = -p[GAMMA]*mass[j]*v[i,j]
    diag = np.array([contact_energy, magnetic_energy, friction_excess, relative_flow_dissipation])
    return forces, torques, raw, u, target, target_v, contact_normal, penetration, diag


class Simulator(BaseSystemCollection, Constraints, Forcing):
    pass


class Environment(NoForces):
    def __init__(self, params, mode, dipole_body, dipole_alpha, rest_lengths, inertia_diag, coil=False, ff_data=None):
        super().__init__()
        self.p, self.mode = params, mode
        self.dipole_body, self.dipole_alpha = dipole_body, dipole_alpha
        self.rest_lengths, self.inertia_diag = rest_lengths, inertia_diag
        self.coil, self.held_u = coil, np.zeros(8)
        self.ff_data = ff_data
        self.currents = np.zeros(12)
        self.control_period, self.control_index = .002, 0
        self.coil_log = [np.r_[0., np.zeros(28)]] if coil else []
        if coil:
            sys.path.insert(0,str(ROOT.parent))
            from coil_field import CoilAllocator
            self.allocator = CoilAllocator()
            self.allocator.last_time = 0.
        self.last = None

    def desired_command(self,rod,time):
        raw,u,target,target_v=command(rod.position_collection,rod.velocity_collection,float(time),self.p,self.mode)
        if self.ff_data is not None:
            ft,fu=self.ff_data
            learned=np.array([np.interp(time,ft,fu[:,j]) for j in range(8)])
            analytic_ff=command(rod.position_collection,rod.velocity_collection,float(time),self.p,1)[0]
            raw=learned+raw-analytic_ff
            u=limit_command(raw,self.p)
        return raw,u,target,target_v

    def evaluate(self, rod, time):
        override=self.held_u
        raw_override=np.zeros(8)
        if self.ff_data is not None or self.coil:
            raw_override,requested,_,_=self.desired_command(rod,time)
            if not self.coil:override=requested
        return environmental_forces(rod.position_collection,rod.velocity_collection,rod.director_collection,rod.omega_collection,
                                    rod.lengths,rod.radius,self.rest_lengths,rod.volume,rod.mass,self.inertia_diag,
                                    self.dipole_body,self.dipole_alpha,float(time),self.p,self.mode,override,raw_override,self.coil or self.ff_data is not None)

    def apply_forces(self, system, time=0.):
        rod = system
        if self.coil:
            index = int(np.floor((float(time)+1e-12)/self.control_period))
            if index > self.control_index:
                _, requested, _, _ = self.desired_command(rod,float(time))
                control_time = index*self.control_period
                self.held_u,self.currents = self.allocator.allocate(requested,control_time)
                self.coil_log.append(np.r_[control_time,requested,self.held_u,self.currents])
                self.control_index = index
        self.last = self.evaluate(rod,time)
        self.before_v = rod.velocity_collection.copy()
        self.before_w = rod.omega_collection.copy()
        rod.external_forces += self.last[0].sum(axis=0)
        rod.external_torques += self.last[1].sum(axis=0)


def dipoles(rest_lengths, cfg):
    boundaries = np.r_[0.,np.cumsum(rest_lengths)]
    l = cfg["rod"]["length_m"]
    a = l-cfg["magnet"]["distal_length_m"]
    begin = np.maximum(boundaries[:-1],a)
    end = np.minimum(boundaries[1:],l)
    overlap = np.maximum(end-begin,0.)
    alpha = np.where(overlap>0,(.5*(begin+end)-boundaries[:-1])/rest_lengths,.5)
    body = np.array(cfg["magnet"]["body_direction"],dtype=float)
    body /= np.linalg.norm(body)
    moment = body[:,None]*cfg["magnet"]["line_dipole_A_m"]*overlap[None,:]
    return moment,alpha


def make_model(cfg,n,mode,coil=False):
    p=pack_parameters(cfg)
    rod=CosseratRod.straight_rod(n,np.zeros(3),np.array([0.,0.,1.]),np.array([1.,0.,0.]),
                               p[L],p[RAD],p[RHO],youngs_modulus=p[E],shear_modulus=p[G])
    twist=cfg["rod"].get("initial_twist_rad",0.)
    if twist:
        for j in range(n):
            angle=twist*(j/max(n-1,1))**2
            rod.director_collection[:,:,j]=np.array([[np.cos(angle),np.sin(angle),0.],[-np.sin(angle),np.cos(angle),0.],[0.,0.,1.]])
    sim=Simulator()
    sim.append(rod)
    sim.constrain(rod).using(OneEndFixedBC,constrained_position_idx=(0,),constrained_director_idx=(0,))
    moment,alpha=dipoles(rod.rest_lengths,cfg)
    # Copies remain independent of PyElastica's finalized memory-block layout.
    inertia=np.array([rod.mass_second_moment_of_inertia[i,i,:].copy() for i in range(3)])
    holder={}
    ff_data=None
    if cfg['controller'].get('feedforward_npz'):
        path=Path(cfg['controller']['feedforward_npz'])
        if not path.is_absolute():path=ROOT/path
        with np.load(path) as data:
            ft,fu=data['time_s'].copy(),data['u_ff'].copy()
        if len(ft)<2 or fu.shape!=(len(ft),8) or not np.isfinite(fu).all() or not np.all(np.diff(ft)>0):
            raise ValueError('feedforward requires increasing time_s and finite u_ff[nt,8] in SI')
        ff_data=(ft,fu)
    class CapturedEnvironment(Environment):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            holder["environment"]=self
    sim.add_forcing_to(rod).using(CapturedEnvironment,p,mode,moment,alpha,rod.rest_lengths.copy(),inertia,coil=coil,ff_data=ff_data)
    sim.finalize()
    rod.compute_internal_forces_and_torques(0.)
    return sim,rod,holder["environment"]


def metrics_snapshot(rod,env,t,work):
    # Synchronize geometry/strains at the snapshot time, not the previous half-step.
    rod.compute_internal_forces_and_torques(t)
    val=env.evaluate(rod,t)
    f,tau,raw,u,target,target_v,normal,penetration,diag=val
    trans=float(rod.compute_translational_energy())
    rot=float(rod.compute_rotational_energy())
    bend=float(rod.compute_bending_energy())
    shear=float(rod.compute_shear_energy())
    twist=float(.5*np.sum(rod.bend_matrix[2,2,:]*(rod.kappa[2]-rod.rest_kappa[2])**2*rod.rest_voronoi_lengths))
    so3=np.einsum('ije,kje->ike',rod.director_collection,rod.director_collection)-np.eye(3)[:,:,None]
    b,grad=unpack_field(u)
    field=b[:,None]+grad@(rod.position_collection-np.array([0.,0.,env.p[L]])[:,None])
    tip_gap=env.p[RV]-env.p[RAD]-lumen_projection(rod.position_collection[:,-1],env.p)[3]
    power=np.sum(f*rod.velocity_collection[None,:,:],axis=(1,2))+np.sum(tau*rod.omega_collection[None,:,:],axis=(1,2))
    values=dict(time_s=t,tip_x_m=rod.position_collection[0,-1],tip_y_m=rod.position_collection[1,-1],tip_z_m=rod.position_collection[2,-1],
                target_x_m=target[0],target_y_m=target[1],target_z_m=target[2],tip_error_m=float(np.linalg.norm(rod.position_collection[:,-1]-target)),
                kinetic_translation_J=trans,kinetic_rotation_J=rot,bending_twisting_J=bend,twisting_J=twist,shear_stretch_J=shear,contact_potential_J=diag[0],
                mechanical_energy_J=trans+rot+bend+shear+diag[0],magnetic_potential_J=diag[1],
                contact_normal_total_N=float(normal.sum()),max_quadrature_penetration_m=float(penetration.max()),tip_clearance_m=float(tip_gap),
                max_shear_stretch_strain=float(np.max(np.abs(rod.sigma))),max_twist_curvature_per_m=float(np.max(np.abs(rod.kappa[2]))),
                so3_orthogonality_error=float(np.max(np.sqrt(np.sum(so3*so3,axis=(0,1))))),
                so3_det_error=float(np.max(np.abs(np.linalg.det(rod.director_collection.transpose(2,0,1))-1))),
                B_at_nodes_max_T=float(np.max(np.linalg.norm(field,axis=0))),G_frobenius_T_per_m=float(np.linalg.norm(grad)),
                Maxwell_trace_T_per_m=float(np.trace(grad)),Maxwell_curl_T_per_m=float(np.linalg.norm(grad-grad.T)),
                friction_inequality_excess_N=float(diag[2]),relative_flow_dissipation_W=float(diag[3]),
                requested_input_clipping=float(np.linalg.norm(raw-u)),max_current_A=float(np.max(np.abs(env.currents))))
    names=["magnetic","flow","contact_elastic","contact_dissipative","residual_g","structural_damping"]
    for j,name in enumerate(names):
        values["power_"+name+"_W"]=float(power[j])
        values["work_"+name+"_J"]=float(work[j])
    state=dict(r=rod.position_collection.T.copy(),v=rod.velocity_collection.T.copy(),directors=rod.director_collection.transpose(2,0,1).copy(),
               omega_body=rod.omega_collection.T.copy(),sigma=rod.sigma.T.copy(),kappa=rod.kappa.T.copy(),u_requested=raw.copy(),u=u.copy(),
               target=target.copy(),contact_normal_force_N=normal.copy(),contact_penetration_m=penetration.copy(),
               force_magnetic=f[0].T.copy(),force_flow=f[1].T.copy(),force_contact=(f[2]+f[3]).T.copy(),
               torque_magnetic_body=tau[0].T.copy(),torque_flow_body=tau[1].T.copy(),torque_contact_body=tau[3].T.copy(),currents_A=env.currents.copy())
    return values,state


MODE={"uncontrolled":0,"feedforward":1,"feedback":2,"contact_stress":3,"excitation":4,"conservative":0,"coil_allocated":2}


def run_case(name,output,cfg=None,n=None,dt=None,duration=None,sample_dt=None,mode="feedback"):
    cfg=copy.deepcopy(cfg or load_config())
    n=int(n or cfg["numerics"]["baseline_elements"])
    dt=float(dt or cfg["numerics"]["baseline_dt_s"])
    duration=float(duration or cfg["numerics"]["final_time_s"])
    sample_dt=float(sample_dt or cfg["numerics"]["snapshot_interval_s"])
    out=Path(output)/name
    out.mkdir(parents=True,exist_ok=True)
    nsteps=int(np.ceil(duration/dt))
    dt=duration/nsteps
    stride=max(1,int(round(sample_dt/dt)))
    start=clock.perf_counter()
    sim,rod,env=make_model(cfg,n,MODE[mode],coil=(mode=="coil_allocated"))
    if env.ff_data is not None and (env.ff_data[0][0]>0 or env.ff_data[0][-1]<duration-1e-12):
        raise ValueError('feedforward NPZ must cover the complete simulation interval')
    stepper=PositionVerlet()
    work=np.zeros(6)
    rows,states=[],[]
    row,state=metrics_snapshot(rod,env,0.,work)
    rows.append(row);states.append(state)
    energy0=row["mechanical_energy_J"]
    max_pen,max_contact,max_so3,max_strain,max_field,max_gradient=0.,0.,0.,0.,0.,0.
    clip_steps=0
    strain_crossings={}
    def record_failure(error,step):
        failure=dict(case=name,mode=mode,n_elements=n,dt_s=dt,attempted_duration_s=duration,
                     exception_type=type(error).__name__,message=str(error),failure_step=int(step),
                     failure_step_start_time_s=step*dt,last_saved_finite_time_s=rows[-1]['time_s'],
                     wall_time_s=clock.perf_counter()-start,strain_threshold_first_crossings_s=strain_crossings,
                     model_sha256=MODEL_SHA256,evidence='failed computation; not a successful full trajectory')
        (out/'failure.json').write_text(json.dumps(failure,indent=2))
        (out/'parameters.json').write_text(json.dumps(cfg,indent=2))
        arrays={k:np.stack([s[k] for s in states]) for k in states[0]}
        arrays['time_s']=np.array([x['time_s'] for x in rows])
        arrays['reference_s_m']=np.r_[0.,np.cumsum(env.rest_lengths)]
        np.savez_compressed(out/'partial_trajectory.npz',**arrays)
        with (out/'partial_diagnostics.csv').open('w',newline='') as file:
            writer=csv.DictWriter(file,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
        print(json.dumps(failure),flush=True)
    for step in range(nsteps):
        t=step*dt
        try:
            stepper.step(sim,t,dt)
        except (ZeroDivisionError,FloatingPointError,ValueError) as error:
            record_failure(error,step)
            raise
        strain=float(np.max(np.abs(rod.sigma)))
        for threshold in (.001,.01,.1):
            if strain>threshold and str(threshold) not in strain_crossings:
                strain_crossings[str(threshold)]=(step+.5)*dt
        val=env.last
        vmid=.5*(env.before_v+rod.velocity_collection)
        wmid=.5*(env.before_w+rod.omega_collection)
        work+=dt*(np.sum(val[0]*vmid[None,:,:],axis=(1,2))+np.sum(val[1]*wmid[None,:,:],axis=(1,2)))
        max_pen=max(max_pen,float(val[7].max()))
        max_contact=max(max_contact,float(val[6].sum()))
        if np.linalg.norm(val[2]-val[3])>1e-12:clip_steps+=1
        if (step+1)%stride==0 or step+1==nsteps:
            if not np.isfinite(rod.position_collection).all() or not np.isfinite(rod.omega_collection).all():
                error=FloatingPointError(f"nonfinite trajectory at step {step+1}")
                record_failure(error,step)
                raise error
            row,state=metrics_snapshot(rod,env,(step+1)*dt,work)
            rows.append(row);states.append(state)
            max_so3=max(max_so3,row["so3_orthogonality_error"])
            max_strain=max(max_strain,row["max_shear_stretch_strain"])
            max_field=max(max_field,row["B_at_nodes_max_T"])
            max_gradient=max(max_gradient,row["G_frobenius_T_per_m"])
    wall_time=clock.perf_counter()-start
    # Contact elastic work is paired with contact potential, hence excluded here.
    total_work=work[[0,1,3,4,5]].sum()
    residual=rows[-1]["mechanical_energy_J"]-energy0-total_work
    errors=np.array([x["tip_error_m"] for x in rows])
    times=np.array([x["time_s"] for x in rows])
    late=times>=min(.5,duration/2)
    summary=dict(case=name,mode=mode,n_elements=n,n_nodes=n+1,configuration_dof=6*n+3-6,dt_s=dt,steps=nsteps,snapshot_stride=stride,
                 snapshots=len(rows),duration_s=duration,wall_time_s=wall_time,
                 tip_rmse_m=float(np.sqrt(np.mean(errors**2))),tip_rmse_after_ramp_m=float(np.sqrt(np.mean(errors[late]**2))),
                 final_tip_error_m=float(errors[-1]),max_contact_penetration_m=max_pen,max_total_contact_normal_N=max_contact,
                 max_so3_orthogonality_error=max_so3,max_abs_shear_stretch_strain=max_strain,max_B_at_rod_nodes_T=max_field,max_G_frobenius_T_per_m=max_gradient,
                 input_clipped_or_allocated_fraction=clip_steps/nsteps,
                 mechanical_energy_initial_J=energy0,mechanical_energy_final_J=rows[-1]["mechanical_energy_J"],external_work_J=float(total_work),
                 energy_work_residual_J=float(residual),energy_work_residual_scaled=float(abs(residual)/max(abs(total_work),abs(energy0),max(x["mechanical_energy_J"] for x in rows),1e-15)),
                 total_magnetic_moment_norm_sum_A_m2=float(np.linalg.norm(env.dipole_body,axis=0).sum()),
                 density_kg_m3=cfg["rod"]["density_kg_m3"],damping_rate_s_inv=cfg["rod"]["mass_proportional_damping_rate_s_inv"],
                 evidence="newly computed synthetic/literature-anchored benchmark; no patient measurement or full FSI")
    if env.coil:
        history=np.asarray(env.coil_log)
        cols=["time_s"]+["requested_"+s for s in cfg["controller"]["input_order"]]+["actual_"+s for s in cfg["controller"]["input_order"]]+[f"I{j+1}_A" for j in range(12)]
        np.savetxt(out/"coil_commands.csv",history,delimiter=",",header=",".join(cols),comments="")
        slew=np.diff(history[:,17:],axis=0)/np.diff(history[:,0])[:,None]
        summary["coil_max_current_A"]=float(np.max(np.abs(history[:,17:])))
        summary["coil_max_slew_A_per_s"]=float(np.max(np.abs(slew)))
        summary["coil_control_period_s"]=env.control_period
    arrays={k:np.stack([s[k] for s in states]) for k in states[0]}
    arrays["time_s"]=times
    arrays["reference_s_m"]=np.r_[0.,np.cumsum(env.rest_lengths)]
    arrays["magnetic_dipole_body_A_m2"]=env.dipole_body.T
    arrays["magnetic_barycentric_coordinate"]=env.dipole_alpha
    np.savez_compressed(out/"trajectory.npz",**arrays)
    with (out/"diagnostics.csv").open("w",newline="") as file:
        writer=csv.DictWriter(file,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    (out/"parameters.json").write_text(json.dumps(cfg,indent=2))
    (out/"summary.json").write_text(json.dumps(summary,indent=2))
    env_versions={s:importlib.metadata.version(s) for s in ["pyelastica","numba","llvmlite","numpy","scipy","matplotlib"]}
    env_versions.update(python=sys.version,model_sha256=MODEL_SHA256)
    if cfg['controller'].get('feedforward_npz'):
        path=Path(cfg['controller']['feedforward_npz'])
        if not path.is_absolute():path=ROOT/path
        env_versions['feedforward_npz_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    (out/"environment.json").write_text(json.dumps(env_versions,indent=2))
    print(json.dumps(summary),flush=True)
    return summary


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--name",default="smoke")
    parser.add_argument("--output",default=str(ROOT.parents[1]/"results"/"rod3d"))
    parser.add_argument("--config")
    parser.add_argument("--mode",choices=list(MODE),default="feedback")
    parser.add_argument("--elements",type=int)
    parser.add_argument("--dt",type=float)
    parser.add_argument("--duration",type=float)
    parser.add_argument("--sample-dt",type=float)
    args=parser.parse_args()
    run_case(args.name,args.output,load_config(args.config),args.elements,args.dt,args.duration,args.sample_dt,args.mode)
