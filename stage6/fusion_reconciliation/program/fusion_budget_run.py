"""Reproduce unchanged fusion budgets and attach analytic bounds to S5-L01.

Usage: python .../fusion_budget_run.py --fusion-root /tmp/.../v10_birkhoff_20261028
All archive scripts/inputs are copied to a fresh temporary directory first.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import numpy as np
import torch
from fusion_budget import (MechanicalPolynomialBudget, dual_route_budget, homological_compatibility,
                           exact_normalized_momentum_bound)
from fractions import Fraction

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'stage6/fusion_reconciliation/results/budgets'
sys.path.insert(0,str(ROOT/'stage5/program'))
from learning_models import MechanicalPolynomial, RodROM


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_save(path,data):
    Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def reproduce_original(source):
    wanted=['reproduction/route_budget/normal_form_budgets.py',
            'reproduction/new_baseline.json','reproduction/experiments/route_b_shared_results.json']
    with tempfile.TemporaryDirectory(prefix='1028-fusion-budget-') as name:
        scratch=Path(name)
        for relative in wanted:
            target=scratch/relative;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source/relative,target)
        command=[sys.executable,str(scratch/wanted[0]),'--language','none']
        started=time.perf_counter()
        proc=subprocess.run(command,text=True,capture_output=True,env=os.environ.copy())
        (OUT/'original_budget_stdout.log').write_text(proc.stdout+proc.stderr)
        meta=dict(command=command,source_sha256={p:digest(source/p) for p in wanted},
                  elapsed_seconds=time.perf_counter()-started,exit_code=proc.returncode,
                  isolated_copy=True,originals_written=False)
        json_save(OUT/'original_budget_execution.json',meta)
        if proc.returncode:raise RuntimeError(proc.stderr)
        result=json.loads((scratch/'reproduction/route_budget/normal_form_budget_results.json').read_text())
        json_save(OUT/'original_budget_recomputed.json',result)
    frozen=json.loads((source/'reproduction/route_budget/normal_form_budget_results.json').read_text())
    comparison=[]
    for a,b in zip(result['routes'],frozen['routes']):
        for key in ['m_velocity_majorant','ell_derivative_majorant','image_margin',
                    'complete_normal_form_remainder_majorant','twist_determinant','twist_sigma_min']:
            comparison.append(dict(kappa=a['kappa'],quantity=key,recomputed=a[key],frozen=b[key],
                                   absolute_difference=abs(a[key]-b[key]),
                                   passed=bool(np.isclose(a[key],b[key],rtol=5.e-13,atol=1.e-30))))
    assert all(row['passed'] for row in comparison)
    json_save(OUT/'original_budget_comparison.json',dict(tolerance_rtol=5.e-13,tolerance_atol=1.e-30,rows=comparison))
    return result


def run_3d():
    torch.set_default_dtype(torch.float64);torch.set_num_threads(1)
    protocol_path=ROOT/'stage5/results/learning/S5_L01_protocol.json'
    protocol=json.loads(protocol_path.read_text());D=np.asarray(protocol['scales']['coordinate_D'])
    rom=RodROM();nu=rom.nu.detach().numpy()
    np.testing.assert_allclose(D,np.r_[np.sqrt(nu),np.sqrt(nu)]/protocol['amplitude'],rtol=3.e-13)
    rng=np.random.default_rng(61025)
    rows=[];arrays={};exact_legendre=[]
    started=time.perf_counter()
    for seed in protocol['seeds']:
        cp=ROOT/f'stage5/results/learning/S5_L01_analytic_mechanical4_seed{seed}.pt'
        saved=torch.load(cp,map_location='cpu',weights_only=False)
        net=MechanicalPolynomial(12,saved['output_scale']);net.load_state_dict(saved['state_dict']);net.eval()
        poly=MechanicalPolynomialBudget.from_checkpoint(saved,D)
        exact_legendre.append(dict(seed=seed,small_box=exact_normalized_momentum_bound(saved,D,Fraction(1,20)),
                                  larger_box=exact_normalized_momentum_bound(saved,D,Fraction(1,10))))
        # New independent 24D samples, with the actual geometric ROM for real labels.
        x=rng.normal(size=(8,24))*.2
        xt=torch.tensor(x,requires_grad=True);prediction=net(xt)
        grad=torch.autograd.grad(prediction.sum(),xt)[0].detach().numpy()*D
        z=x/D
        expected=prediction.detach().numpy()
        values=poly.evaluate(z);grad2=poly.gradient(z)
        labels=rom.hamiltonian(torch.tensor(z)).detach().numpy()-.5*protocol['amplitude']**2*np.sum(x*x,axis=1)
        value_error=float(np.max(abs(values-expected)));gradient_error=float(np.max(abs(grad-grad2)))
        np.testing.assert_allclose(values,expected,atol=2.e-16,rtol=2.e-12)
        np.testing.assert_allclose(grad2,grad,atol=2.e-14,rtol=2.e-11)
        for normal_radius in (.01,.025,.05,.1,.25,.5,1.,1.5):
            radius=normal_radius/D
            bounds=poly.majorants(radius)
            # Complex points use all 24 independent complexified real coordinates.
            complex_z=radius[None,:]*rng.uniform(.1,1.,size=(8,24))*np.exp(2j*np.pi*rng.random((8,24)))
            complex_values=poly.evaluate(complex_z)
            observed=float(np.max(abs(complex_values)))
            assert observed<=bounds['energy']*(1+2.e-14)
            rows.append(dict(seed=seed,checkpoint=str(cp.relative_to(ROOT)),checkpoint_sha256=digest(cp),
                             normalized_radius=normal_radius,canonical_radii=radius.tolist(),
                             learned_residual_energy_majorant=bounds['energy'],
                             gradient_component_majorants=bounds['gradient'].tolist(),
                             learned_residual_Hpp_row_bound=bounds['Hpp_row_sum_bound'],
                             full_learned_Hpp_eigenvalue_lower_bound=float(min(nu)-bounds['Hpp_row_sum_bound']),
                             weighted_momentum_convexity=poly.momentum_convexity_bound(radius,nu),
                             parameter_feature_l2_bound=bounds['parameter_feature_l2_bound'],
                             parameter_count=len(poly.exponents),complex_sample_max_abs=observed,
                             reconstruction_energy_max_abs_error=value_error,
                             reconstruction_canonical_gradient_max_abs_error=gradient_error,
                             actual_ROM_real_sample_residual_error_max=float(np.max(abs(values-labels))),
                             true_ROM_uniform_complex_error_bound=None,
                             deterministic_coefficient_error_bound=None,
                             floating_majorant_evaluation_not_interval_certificate=True))
        arrays[f'seed{seed}_real_z']=z;arrays[f'seed{seed}_learned_residual']=values
        arrays[f'seed{seed}_true_ROM_residual']=labels
        arrays[f'seed{seed}_exponents']=poly.exponents
        arrays[f'seed{seed}_canonical_coefficients']=poly.canonical_coefficients
    np.savez_compressed(OUT/'actual_3d_polynomial_data.npz',**arrays)
    json_save(OUT/'actual_3d_exact_learned_legendre_bounds.json',dict(rows=exact_legendre,
              warning='Exact for frozen learned polynomial only; no trained-model approximation or true-robot certificate'))
    gate=homological_compatibility(nu)
    assert gate['nonaction_resonant_count']==128
    json_save(OUT/'actual_3d_homological_gate.json',dict(source='same RodROM as S5-L01; ideal axial bias, variable M(q)',
               frequencies=nu.tolist(),quartic_gate=gate,full_coil_closed_loop_certificate=False))
    json_save(OUT/'actual_3d_majorants.json',dict(experiment='S6-B01',seed=61025,
              target=protocol['target'],protocol_sha256=digest(protocol_path),rows=rows,
              environment=dict(python=platform.python_version(),numpy=np.__version__,torch=torch.__version__,threads=1),
              elapsed_seconds=time.perf_counter()-started,
              proof='stage6/fusion_reconciliation/proofs/kam_budget_corrections.md',
              statement='Bounds for frozen learned mechanical polynomials, NOT true-ROM learning-error bounds'))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--fusion-root',type=Path)
    args=parser.parse_args();OUT.mkdir(parents=True,exist_ok=True)
    if args.fusion_root is None:
        from materials import resolve_source
        args.fusion_root=resolve_source()
    original=reproduce_original(args.fusion_root)
    routes=original['routes'];bg=original['shared_learning']['B_g_majorant']
    restored=dual_route_budget(routes[0]['complete_normal_form_remainder_majorant'],
                               routes[1]['complete_normal_form_remainder_majorant'],bg,None,
                               common_chart_domain_verified=all(x['image_margin']>0 for x in routes))
    json_save(OUT/'restored_dual_budget_interface.json',restored)
    run_3d()
    print(json.dumps(dict(status='executed',old_budget='reproduced',actual_3d='frozen polynomial bounds and resonance gate',
                          KAM_certificate=False),ensure_ascii=False))

if __name__=='__main__':main()
