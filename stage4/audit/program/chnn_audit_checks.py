"""Independent checks of inherited CHNN formulas and the actual 12-DOF classes.

This is a small architecture/identity audit, NOT a recreation of missing frozen
weights, a training benchmark, a uniform error bound, or a KAM certificate.
All generated files stay under stage4/audit/results/chnn_checks.
"""
from __future__ import annotations
import ast
import hashlib
import json
import os
import platform
from pathlib import Path
import sys
import time
import numpy as np
import scipy
import sympy as sp
import torch

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'stage3/source_inputs/starter/stage2/program/learning'
sys.path.insert(0, str(SOURCE))
from rod_rom import RodROM
from run_learning import ComplexResidual, labels
from train_spd_complex import MechanicalComplexResidual


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    start = time.perf_counter()
    torch.set_default_dtype(torch.float64)
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.manual_seed(102504)
    out = ROOT / 'stage4/audit/results/chnn_checks'
    out.mkdir(parents=True, exist_ok=True)
    paths = [SOURCE / name for name in ['rod_rom.py', 'run_learning.py',
             'run_learning_trained_source.py', 'train_spd_complex.py']]
    before = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    checks = {}
    q, p = 0.7, -0.4
    xi = (q + 1j*p)/np.sqrt(2.)
    actual = (p - 1j*q)/np.sqrt(2.)  # H=(q^2+p^2)/2
    corrected = -1j*xi
    derivative_as_printed = (q + 1j*p)/2
    # Original (18) and later sqrt(2) multiplier can cancel on this test;
    # they are nevertheless inconsistent with the coordinate chain rule.
    checks['original_normalization'] = {
        'coordinate': 'original1025-p0350/m0194; xi=(q+i p)/sqrt(2)',
        'printed_derivative': 'original1025-p0351/m0195; (dq+i dp)/2',
        'correct_derivative': '(dq+i dp)/sqrt(2)',
        'corrected_oscillator_error': float(abs(actual-corrected)),
        'printed_derivative_chain_rule_error': float(abs(derivative_as_printed-xi)),
        'sqrt2_times_correct_derivative_error': float(abs(actual+1j*np.sqrt(2)*xi)),
        'two_wrong_factors_cancel_in_oscillator': float(abs(actual+1j*np.sqrt(2)*derivative_as_printed)),
    }
    assert abs(actual-corrected) < 1e-14
    assert abs(derivative_as_printed-xi) > .1
    gamma = .3
    hdot = -gamma*p*p
    checks['original_energy_loss'] = {
        'source': 'original1025-p0591/m0284',
        'damped_oscillator_Hdot': hdot,
        'omitted_contribution_for_tildeH_sqrt2_H_plus_iP': 2*hdot**2,
        'correction': '|d tildeH/dt|^2=2[(dH/dt)^2+(dP/dt)^2] for real H,P',
    }
    checks['original_rayleigh_mass_counterexample'] = {
        'source': 'original1025-p0342; H=p^2/(2m), C=c constant',
        'mass_m': 2., 'damping_c': .3, 'momentum_p': .4,
        'physical_force_minus_c_Hp': -.3*.4/2.,
        'printed_force_minus_dG1_dp': -.3*.4,
        'force_abs_error': abs(-.3*.4/2.+.3*.4),
        'correction': 'D(q,v)=c*v^2/2; evaluate -D_v at v=H_p. If C depends on v, its derivatives also matter.',
    }
    checks['original_HNN_loss_derivative_mismatch'] = {
        'source': 'original1025-p0593/m0286 versus p0598/m0289',
        'test_energy': '(q^2+p^2)/2 in consistently normalized xi',
        'correct_barxi_predictor_loss': float(abs(actual+1j*xi)**2),
        'xi_derivative_loss_on_exact_trajectory': float(abs(actual+1j*xi.conjugate())**2),
    }
    x, y = .2, .9
    cr = 1/np.cosh(x)**2-1/np.cosh(y)**2
    checks['split_tanh_regularities'] = {
        'CR_defect_at_0p2_plus_0p9i': float(cr),
        'conclusion': 'not holomorphic in one complex input; real analytic locally',
        'continuation': 'tanh((z+w)/2)+i*tanh((z-w)/(2i)), independent z,w; avoid tanh poles',
    }
    assert abs(cr) > .1
    zz = sp.symbols('z')
    polynomial = sp.expand(sp.prod((zz-sp.Rational(j,2))**2 for j in [-2,-1,0,1,2]))
    derivative = sp.diff(polynomial, zz)
    assert all(derivative.subs(zz, sp.Rational(j,2)) == 0 for j in [-2,-1,0,1,2])
    checks['finite_real_data_not_complex_norm'] = {
        'polynomial': str(polynomial), 'training_points': [-1,-.5,0,.5,1],
        'all_sample_values_and_gradients_zero': True,
        'abs_value_at_i': float(abs(complex(polynomial.subs(zz,sp.I)))),
        'conclusion': 'Multiplying this entire polynomial by any A leaves sampled losses zero and makes the complex norm arbitrarily large.'}
    k = 1000
    h = 2*np.pi/k
    checks['discrete_divisor_counterexample'] = {
        'omega': [1., np.sqrt(2.)], 'k': [k,0], 'h': float(h),
        'continuous_k_dot_omega': k,
        'discrete_divisor_abs': float(abs(np.exp(1j*h*k)-1)),
        'conclusion': 'Even for the quadratic-irrational continuous frequency, arbitrarily small chosen steps h=2*pi/k can be exactly resonant.'}
    checks['old_tube_exactness'] = {
        'source': 'external_v10/sections/measure_proof.tex:153-162',
        'circular_torus_radius': .1,
        'period_of_pulled_back_polar_primitive_on_cycle': 2*np.pi*.1**2/2,
        'conclusion': 'The closed pullback difference has nonzero periods. Symplectic is sufficient for volume; exactness relative to I dt needs a primitive shift.'}
    model = RodROM()
    meta = model.metadata()
    nu = model.nu.detach().numpy()
    amplitude = .08
    scale = np.sqrt(np.r_[nu,nu])/amplitude
    jmat = np.block([[np.zeros((12,12)),np.eye(12)],[-np.eye(12),np.zeros((12,12))]])
    checks['actual_3d_model'] = meta
    assert meta['q_dof'] == 12 and meta['repeated_frequency_pairs']
    assert meta['canonical_scaling_defect'] < 1e-16
    checks['training_normalization'] = {
        'noncanonical_norm_DJD_minus_J': float(np.linalg.norm(scale[:,None]*jmat*scale[None,:]-jmat)),
        'correct_equation': 'x_prime=D J D grad_x h; grad_z h=D grad_x h',
        'identity_error': float(np.linalg.norm(np.diag(scale)@jmat@np.diag(scale)-scale[:,None]*jmat*scale[None,:])),
    }
    rng = np.random.default_rng(102504)
    data = labels(model, rng.uniform(-1,1,(16,24)), amplitude, batch_size=16)
    hscale = max(float(np.std(data['h_res'])),1e-7)
    gscale = max(float(np.sqrt(np.mean(data['g_res']**2))),1e-7)
    net = ComplexResidual(12,48,hscale)
    initial = {name: val.detach().clone() for name,val in net.named_parameters()}
    optimizer = torch.optim.Adam(net.parameters(), lr=.003)
    history=[]
    for _ in range(5):
        tx=torch.tensor(data['x'],requires_grad=True)
        ph=net(tx)
        pg=torch.autograd.grad(ph.sum(),tx,create_graph=True)[0]
        loss=((pg-torch.tensor(data['g_res']))/gscale).square().mean()+.15*((ph-torch.tensor(data['h_res']))/hscale).square().mean()
        optimizer.zero_grad(set_to_none=True);loss.backward()
        torch.nn.utils.clip_grad_norm_(net.parameters(),10.)
        optimizer.step();history.append(float(loss.detach()))
    update={name:{'real_norm':float(torch.linalg.norm((val-initial[name]).real)),
                  'imaginary_norm':float(torch.linalg.norm((val-initial[name]).imag))}
            for name,val in net.named_parameters()}
    assert all(v['real_norm']>0 and v['imaginary_norm']>0 for v in update.values())
    zero=torch.zeros(24)
    origin_hess=torch.autograd.functional.hessian(lambda a:net(a[None,:])[0],zero)
    xx=torch.tensor(data['x'])
    xxmirror=torch.cat([xx[:,:12],-xx[:,12:]],dim=1)
    checks['actual_complex_training_smoke']={
        'status':'executed; five fresh updates, not historical retraining',
        'labels':'16 new noiseless samples from the actual configuration-dependent 12-DOF geometric ROM',
        'seed':102504,'steps':5,'losses':history,
        'complex_parameters':sum(v.numel() for v in net.parameters()),
        'real_parameters':2*sum(v.numel() for v in net.parameters()),
        'parameter_updates':update,
        'origin_residual_hessian_norm':float(torch.linalg.norm(origin_hess)),
        'momentum_evenness_max_abs':float((net(xx)-net(xxmirror)).abs().max().detach()),
    }
    assert float(torch.linalg.norm(origin_hess)) < 1e-14
    torch.manual_seed(102505)
    spd=MechanicalComplexResidual(12,48,amplitude,hscale)
    tx=xx[0].detach();z=tx/torch.tensor(scale)
    lower,_,_=spd.factor_and_potential(tx[None,:12])
    a=torch.sqrt(model.nu)[:,None]*(lower[0]@lower[0].T)*torch.sqrt(model.nu)[None,:]
    hpp=torch.autograd.functional.hessian(lambda mom:spd.energy((torch.cat([z[:12],mom])*torch.tensor(scale))[None,:])[0],z[12:])
    rel=float(torch.linalg.norm(hpp-a)/torch.linalg.norm(a))
    eig=torch.linalg.eigvalsh(a).detach()
    recovered=torch.linalg.solve(a,a@z[12:])
    checks['actual_spd_architecture']={
        'status':'fresh initialized architecture; no old checkpoint loaded',
        'real_parameters':2*sum(v.numel() for v in spd.parameters()),
        'Hpp_formula':'diag(sqrt(nu)) L L^T diag(sqrt(nu))',
        'formula_autodiff_relative_error':rel,
        'minimum_eigenvalue':float(eig.min()),'condition_number':float(eig.max()/eig.min()),
        'self_inverse_error':float(torch.linalg.norm(recovered-z[12:])),
        'scope':'pointwise SPD for finite real outputs in exact arithmetic; no uniform accuracy/conditioning/complex-domain claim',
    }
    assert rel < 1e-12 and float(eig.min())>0
    # Compare actual function definitions with the frozen pre-read-guard source.
    defs=[]
    for name in ['run_learning.py','run_learning_trained_source.py']:
        tree=ast.parse((SOURCE/name).read_text())
        defs.append({n.name:ast.dump(n,include_attributes=False) for n in tree.body
                     if isinstance(n,(ast.FunctionDef,ast.ClassDef))})
    differences=[n for n in defs[0].keys()&defs[1].keys() if defs[0][n]!=defs[1][n]]
    checks['source_snapshot_ast']={'changed_common_definitions':sorted(differences),
        'ComplexResidual_unchanged':defs[0]['ComplexResidual']==defs[1]['ComplexResidual'],
        'train_one_unchanged':defs[0]['train_one']==defs[1]['train_one']}
    assert checks['source_snapshot_ast']['ComplexResidual_unchanged']
    after={str(p.relative_to(ROOT)):sha(p) for p in paths}
    assert before==after
    ledger=json.loads((ROOT/'stage4/audit/source_omml/original1025_indexed.json').read_text())
    selected={'original1025-m0194','original1025-m0195','original1025-m0200',
              'original1025-m0284','original1025-m0286','original1025-m0289'}
    objects=ledger['math_objects']
    if isinstance(objects,dict):objects=list(objects.values())
    (out/'original_formula_raw_omml.json').write_text(json.dumps(
        [o for o in objects if o.get('id') in selected],ensure_ascii=False,indent=2)+'\n')
    np.savez_compressed(out/'fresh_architecture_samples.npz',**data,
                        hpp_formula=a.detach().numpy(),hpp_autodiff=hpp.detach().numpy())
    record={'status':'executed_pass','environment':{'python':sys.version,'numpy':np.__version__,
        'scipy':scipy.__version__,'sympy':sp.__version__,'torch':torch.__version__,
        'platform':platform.platform(),'threads':torch.get_num_threads()},
        'command':'PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /workspace/1028-cloud/venvs/learning/bin/python stage4/audit/program/chnn_audit_checks.py',
        'source_sha256_before':before,'source_sha256_after':after,
        'tolerances':{'identity_absolute':1e-14,'Hpp_autodiff_relative':1e-12},
        'checks':checks,'wall_seconds':time.perf_counter()-start}
    (out/'checks.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(record,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
