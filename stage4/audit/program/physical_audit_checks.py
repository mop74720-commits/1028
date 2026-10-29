"""Independent SI coil/ROM audit; all outputs are confined to stage4.

Reuses the delivered geometry, but independently implements analytic derivatives
of the circular-wire Biot--Savart quadrature (no spatial finite differences).
Frozen stage3 trajectories are inputs for a pointwise audit, not rerun dynamics.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
sys.dont_write_bytecode = True
import numpy as np
import scipy
import torch

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "stage3/program"))
from rom_bridge import ROMBridge
sys.path.insert(0, str(REPO / "stage3/source_inputs/starter/stage2/program"))
from coil_field import basis, unpack


def analytic_field_gradient(points, currents, config):
    """Returns B[p,a], d_b B_a[p,a,b]; points in m, I in A, B in T."""
    points = np.atleast_2d(points)
    n = config["quadrature_points"]
    angle = (np.arange(n) + 0.5) * 2 * np.pi / n
    b = np.zeros((len(points), 3))
    g = np.zeros((len(points), 3, 3))
    for center, normal, current in zip(config["centers_m"], config["normals"], currents):
        normal = np.asarray(normal)
        e1 = np.cross(normal, np.eye(3)[np.argmin(abs(normal))])
        e1 /= np.linalg.norm(e1)
        e2 = np.cross(normal, e1)
        wire = np.asarray(center) + config["radius_m"] * (np.cos(angle)[:, None]*e1 + np.sin(angle)[:, None]*e2)
        dl = config["radius_m"]*2*np.pi/n*(-np.sin(angle)[:, None]*e1 + np.cos(angle)[:, None]*e2)
        d = points[:, None, :] - wire[None, :, :]
        r = np.linalg.norm(d, axis=-1)
        if r.min() < 1e-8:
            raise ValueError("Evaluation too close to an ideal line conductor")
        cross = np.cross(dl[None, :, :], d)
        pref = 1e-7 * config["turns"] * current
        b += pref * np.sum(cross/r[..., None]**3, axis=1)
        for j in range(3):
            dg = np.cross(dl, np.eye(3)[j])[None, :, :]/r[..., None]**3
            dg -= 3*cross*d[..., j, None]/r[..., None]**5
            g[:, :, j] += pref*np.sum(dg, axis=1)
    return b, g


def geometry(bridge, raw_q):
    """Coordinates here are physical Ritz coefficients, not basis-dependent Q."""
    active = torch.nonzero(bridge.rom.segment_moment > 0).flatten()
    _, _, _, frame, center = bridge.rom.mechanics(raw_q[None, :], return_geometry=True)
    mu = frame[0, active, :, 2] * bridge.rom.segment_moment[active, None]
    return torch.stack((center[0, active], mu))


def force_audit(bridge, raw_q, currents, config, local_input):
    q = torch.tensor(raw_q)
    x, mu = geometry(bridge, q).detach().numpy()
    dx, dmu = torch.autograd.functional.jacobian(lambda a: geometry(bridge, a), q, vectorize=True).detach().numpy()
    b, g = analytic_field_gradient(x, currents, config)
    b0, ga = unpack(local_input)
    ba = b0+(x-np.asarray(config["origin_m"]))@ga.T
    force = np.einsum("pak,pa->k", dmu, b)+np.einsum("pa,pab,pbk->k", mu, g, dx)
    affine = np.einsum("pak,pa->k", dmu, ba)+np.einsum("pa,ab,pbk->k", mu, ga, dx)
    s = bridge.rom.Sq.numpy().T / bridge.rom.E0
    return dict(force_SI=force, affine_SI=affine, force_Q=s@force,
                affine_Q=s@affine, centers=x, moments=mu, field=b, gradient=g,
                torque_difference_Q=s@np.einsum("pak,pa->k",dmu,b-ba),
                gradient_difference_Q=s@np.einsum("pa,pab,pbk->k",mu,g-ga,dx))


def potential(bridge, raw_q, currents, config):
    x, mu = geometry(bridge, torch.tensor(raw_q)).detach().numpy()
    b, _ = analytic_field_gradient(x, currents, config)
    return -float(np.sum(mu*b))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=REPO/"stage4/audit/results/physical_independent.json")
    args = parser.parse_args()
    start = time.perf_counter()
    torch.set_num_threads(1)
    frozen = REPO/"stage3/results/control"
    inputs = [frozen/"control_results.json", frozen/"trajectories.npz", frozen/"full_coil_force_audit.json"]
    hashes = {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    saved = json.loads(inputs[0].read_text())
    trajectory = np.load(inputs[1])
    old_audit = json.loads(inputs[2].read_text())
    config = saved["coil_allocation"]["config"]
    bridge = ROMBridge()
    records = []
    for order, index in enumerate((0,len(saved["coil_allocation"]["records"])-1)):
        sample = saved["coil_allocation"]["records"][index]
        state = trajectory["bounded_compensation_state"][index+1]
        Q = state[:bridge.n]
        q = bridge.rom.Sq.numpy()@Q
        currents = np.asarray(sample["currents_A"])
        u = np.asarray(sample["actual_local_input"])
        audit = force_audit(bridge,q,currents,config,u)
        reference_b = basis(audit["centers"],config)@currents
        origin_b,origin_g = analytic_field_gradient(np.asarray(config["origin_m"]),currents,config)
        b0,g0 = unpack(u)
        refinements = []
        for n in (128,256,512):
            cfg = {**config,"quadrature_points":n}
            br,gr = analytic_field_gradient(audit["centers"],currents,cfg)
            refinements.append(dict(wire_points=n,field_difference_T=float(np.linalg.norm(br-audit["field"])),gradient_difference_T_per_m=float(np.linalg.norm(gr-audit["gradient"]))))
        fd = []
        for step in (2e-6,1e-6):
            values = []
            for j in range(bridge.n):
                dq = step*bridge.rom.Sq.numpy()[:,j]
                values.append(-(potential(bridge,q+dq,currents,config)-potential(bridge,q-dq,currents,config))/(2*step*bridge.rom.E0))
            fd.append(np.asarray(values))
        error = float(np.linalg.norm(audit["force_Q"]-audit["affine_Q"]))
        record = dict(index=index, time_s=sample["time_s"],
             convention="Both full and affine forces include total bias. H0 already includes ideal affine bias; a total coil force inserted into dynamics must subtract that ideal bias once.",
             coordinates="q are dimensionless integrated-curvature Ritz coefficients; force_SI is joules per q coefficient. force_Q=Sq.T force_SI/E0 is dimensionless Pdot.",
             active_centers_m=audit["centers"].tolist(),total_moment_A_m2=float(bridge.rom.segment_moment.sum()),
             full_force_Q=audit["force_Q"].tolist(),affine_force_Q=audit["affine_Q"].tolist(),
             full_force_SI=audit["force_SI"].tolist(),affine_force_SI=audit["affine_SI"].tolist(),
             force_difference_Q_norm=error,force_relative_error=error/np.linalg.norm(audit["force_Q"]),
             field_implementation_difference_T=float(np.linalg.norm(reference_b-audit["field"])),
             origin_field_error_T=float(np.linalg.norm(origin_b[0]-b0)),
             origin_gradient_error_T_per_m=float(np.linalg.norm(origin_g[0]-g0)),
             distal_gradient_change_T_per_m=float(np.linalg.norm(audit["gradient"]-g0)),
             maxwell_divergence_T_per_m=float(np.max(np.abs(np.trace(audit["gradient"],axis1=1,axis2=2)))),
             maxwell_curl_T_per_m=float(np.linalg.norm(audit["gradient"]-audit["gradient"].transpose(0,2,1))),
             energy_derivative_disagreement_Q=[float(np.linalg.norm(f-audit["force_Q"])) for f in fd],
             affine_Gm_disagreement_Q=float(np.linalg.norm(audit["affine_Q"]-bridge.magnetic_map(Q)@u)),
             frozen_audit_disagreement_Q=float(np.linalg.norm(audit["force_Q"]-np.asarray(old_audit["records"][order]["full_coil_generalized_force"]))),
             torque_change_Q_norm=float(np.linalg.norm(audit["torque_difference_Q"])),
             gradient_force_change_Q_norm=float(np.linalg.norm(audit["gradient_difference_Q"])),wire_refinement=refinements)
        # Spatial magnetic integration at the SAME physical curvature coefficients.
        # Unlike comparing each grid's eigenbasis initial_state, this isolates mesh dependence.
        record["same_physical_q_rod_quadrature"]=[]
        for n in (20,40,80):
            bb = bridge if n==20 else ROMBridge(elements=n)
            aa = force_audit(bb,q,currents,config,u)
            # Transform every physical force to the original 20-cell Q coordinates.
            canonical_common = bridge.rom.Sq.numpy().T@aa["force_SI"]/bridge.rom.E0
            canonical_affine = bridge.rom.Sq.numpy().T@aa["affine_SI"]/bridge.rom.E0
            record["same_physical_q_rod_quadrature"].append(dict(elements=n,
                magnetic_points=len(aa["centers"]),full_force_common_Q=canonical_common.tolist(),
                relative_full_affine_difference=float(np.linalg.norm(canonical_common-canonical_affine)/np.linalg.norm(canonical_common)),
                common_Q_difference_from_20=float(np.linalg.norm(canonical_common-audit["force_Q"]))))
        assert record["field_implementation_difference_T"] < 1e-15
        assert record["affine_Gm_disagreement_Q"] < 1e-10
        assert max(record["energy_derivative_disagreement_Q"]) < 2e-8
        assert record["frozen_audit_disagreement_Q"] < 2e-8
        assert record["maxwell_divergence_T_per_m"] < 1e-12
        assert record["maxwell_curl_T_per_m"] < 1e-12
        records.append(record)
    # Absolute SI sign/turns/length check independent of the saved loop routine.
    cfg = dict(centers_m=[[0.,0.,0.]],normals=[[0.,0.,1.]],radius_m=.025,turns=300,quadrature_points=256)
    axial_z=np.array([0.,.02,.075])
    bs,gs=analytic_field_gradient(np.c_[np.zeros((3,2)),axial_z],np.array([1.]),cfg)
    exact=2*np.pi*1e-7*cfg["turns"]*cfg["radius_m"]**2/(cfg["radius_m"]**2+axial_z**2)**1.5
    axial_error=float(np.linalg.norm(bs[:,2]-exact)/np.linalg.norm(exact))
    assert axial_error < 1e-13
    # Full variable-mass geometry and canonical rescaling, independently differentiated.
    z=bridge.initial_state();q=torch.tensor(z[:bridge.n]);p=torch.tensor(z[bridge.n:])
    m=bridge.mass(z[:bridge.n]);m0=bridge.mass(np.zeros(bridge.n));v=np.linalg.solve(m,z[bridge.n:])
    dm=torch.autograd.functional.jacobian(bridge.mass_tensor,q,vectorize=True).numpy()
    kin_gradient=torch.autograd.functional.jacobian(lambda a:.5*p@torch.linalg.solve(bridge.mass_tensor(a),p),q).numpy()
    kinetic_force=.5*np.einsum("i,ijk,j->k",v,dm,v)
    geometric_error=float(np.linalg.norm(kinetic_force+kin_gradient))
    assert geometric_error < 1e-12
    with np.errstate(invalid="ignore"):
        bad_contact=float(np.float64(-1e-4)**1.5)
    counterexamples=dict(
        morison={"original_acceleration_dimension":"L T^-2","original_Vf_dimension":"L T^-1","subtraction_valid":False,"quadratic_drag_without_D":"M L^-1 T^-2, force per area rather than force per length","correction":"rho_f*A*a_f + m_a*(a_f-r_tt) - c1*v_rel - (rho_f*Cd*D/2)*abs(v_rel)*v_rel"},
        contact={"d_minus_d0_m":-1e-4,"exponent":1.5,"real_numpy_result":"NaN" if np.isnan(bad_contact) else bad_contact,"correction":"delta=max(d0-d,0), F=-k*delta**1.5*n, with n and gap convention stated"},
        moving_fluid={"u_f_m_s":2.,"v_rod_m_s":1.,"drag_coefficient_N_s_m":1.,"force_N":1.,"rod_power_W":1.,"relative_dissipation_W":1.,"identity":"F*v = F*u_f - F*(u_f-v); rod power can be positive"},
        director_convention={"t_at_zero":[0.,0.,1.],"t_s_at_zero":[1.,0.,0.],"u_perp_from_t_cross_t_s":[0.,1.,0.],"t_s_cross_t":[0.,-1.,0.],"qualification":"Sign contradiction only if original k is identified with Darboux u_perp; opposite-binormal naming alone is not an algebraic contradiction."},
        centerline_torsion={"r":"(0,0,s)","R1":"I","R2":"rotation_z(theta(s,t))","same_centerline":True,"distinct_energy":"R2 has 1/2 integral GJ theta_s^2 and 1/2 integral rho J theta_t^2; centerline alone cannot reconstruct independent torsion."},
        contact_regularity={"damping_coefficient":"const*delta_+^(1/4)","local_lipschitz_quotient":"delta^(-3/4) tends to infinity at opening","implication":"Smooth-field uniqueness/order/KAM hypotheses require separate handling; this fact alone is not a proof of nonuniqueness."})
    result=dict(status="actually_executed_pass",environment=dict(python=sys.version,executable=sys.executable,numpy=np.__version__,scipy=scipy.__version__,torch=torch.__version__,platform=platform.platform()),command=" ".join(sys.argv),
        units=dict(E0_J=bridge.rom.E0,omega0_rad_s=bridge.rom.omega0,physical_duration_s=saved["trajectories"][0]["duration_seconds"]),
        tolerances=dict(field_abs_T=1e-15,affine_force_abs_Q=1e-10,energy_gradient_abs_Q=2e-8,maxwell_abs_T_per_m=1e-12,axis_relative=1e-13,geometric_force_abs=1e-12),
        axial_closed_form_relative_error=axial_error,
        variable_mass=dict(relative_change=float(np.linalg.norm(m-m0)/np.linalg.norm(m0)),minimum_eigenvalue=float(np.linalg.eigvalsh(m).min()),condition=float(np.linalg.cond(m)),geometric_force_norm=float(np.linalg.norm(kinetic_force)),geometric_force_identity_error=geometric_error),
        records=records,counterexamples=counterexamples,input_sha256=hashes,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),elapsed_seconds=time.perf_counter()-start,
        limitation="Pointwise force and quadrature audit at two historical saved states. No new coil-driven trajectories, continuous workspace bound, physiological validation, ROM-to-PDE error estimate, or KAM theorem.")
    for path,digest in hashes.items():
        assert hashlib.sha256((REPO/path).read_bytes()).hexdigest()==digest
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"status":result["status"],"output":str(args.output),"seconds":result["elapsed_seconds"],"force_relative_errors":[r["force_relative_error"] for r in records],"rod_quadrature":[r["same_physical_q_rod_quadrature"] for r in records]},ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
