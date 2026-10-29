"""Mechanical, momentum-quadratic complex network on the existing 12-DOF data.

This script only writes the explicitly selected new output directory.  It does
not regenerate labels, modify the earlier checkpoints, or claim that positive
finite Hessian samples prove positivity: H_PP is SPD by the factorization.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import time
from pathlib import Path

import numpy as np
import scipy
import torch
from torch import nn

from rod_rom import RodROM
from run_learning import network_prediction, scores
from evaluate_models import grad_metrics, split_checks


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class MechanicalComplexResidual(nn.Module):
    """Real H, complex trainable hidden layers, full SPD inverse mass.

    ``forward`` returns H-H0, for direct comparison with the existing labels;
    ``energy`` returns H itself.  All dependence on P is exactly quadratic.
    """

    def __init__(self, n, width=48, amplitude=.08, output_scale=1.):
        super().__init__()
        self.n = int(n)
        self.width = int(width)
        self.amplitude = float(amplitude)
        self.output_scale = float(output_scale)
        self.l1 = nn.Linear(n, width, bias=False, dtype=torch.complex128)
        self.l2 = nn.Linear(width, width, bias=True, dtype=torch.complex128)
        self.mass_head = nn.Linear(width, n*(n+1)//2, bias=False,
                                   dtype=torch.complex128)
        self.potential_head = nn.Linear(width, 1, bias=False,
                                        dtype=torch.complex128)
        row, col = torch.tril_indices(n, n)
        self.register_buffer('tril_row', row)
        self.register_buffer('tril_col', col)
        self.register_buffer('tril_diag', row == col)
        with torch.no_grad():
            self.l1.weight.mul_(.5)
            self.l2.weight.mul_(.5)
            self.l2.bias.mul_(.2)
            self.mass_head.weight.mul_(.1)
            self.potential_head.weight.mul_(.5)

    @staticmethod
    def activation(z):
        return torch.complex(torch.tanh(z.real), torch.tanh(z.imag))

    def trunk(self, q):
        a = self.l1(torch.complex(q, torch.zeros_like(q)))
        h = self.activation(self.l2(self.activation(a)))
        return a, h

    def factor_and_potential(self, q):
        a, h = self.trunk(q)
        # The origin branch remains in the computational graph.  Subtracting
        # a cached/detached origin output would not impose the same constraint.
        _, h0 = self.trunk(torch.zeros((1, self.n), dtype=q.dtype,
                                      device=q.device))
        raw = self.mass_head(h-h0).real
        entries = torch.where(self.tril_diag[None, :], torch.exp(raw), raw)
        lower = q.new_zeros((len(q), self.n, self.n))
        lower[:, self.tril_row, self.tril_col] = entries
        potential = self.output_scale*self.potential_head(a**3*h).real[:, 0]
        return lower, potential, raw

    def inverse_mass_normalized(self, q):
        lower, _, _ = self.factor_and_potential(q)
        return lower @ lower.transpose(-1, -2)

    def forward(self, x):
        q, p = x[:, :self.n], x[:, self.n:]
        lower, potential, _ = self.factor_and_potential(q)
        lp = torch.bmm(lower.transpose(1, 2), p[:, :, None])[:, :, 0]
        return .5*self.amplitude**2*(lp.square().sum(-1)-p.square().sum(-1))+potential

    def energy(self, x):
        q, p = x[:, :self.n], x[:, self.n:]
        lower, potential, _ = self.factor_and_potential(q)
        lp = torch.bmm(lower.transpose(1, 2), p[:, :, None])[:, :, 0]
        return .5*self.amplitude**2*(lp.square().sum(-1)+q.square().sum(-1))+potential


def architecture_checks(net, model, data):
    zero = torch.zeros(2*net.n, requires_grad=True)
    residual = lambda x: net(x[None, :])[0]
    origin_h = residual(zero)
    origin_g = torch.autograd.grad(origin_h, zero)[0]
    origin_hessian = torch.autograd.functional.hessian(residual, zero)
    with torch.no_grad():
        lower, _, _ = net.factor_and_potential(torch.zeros(1, net.n))
        x = torch.tensor(data['x'][:64])
        mirrored = torch.cat([x[:, :net.n], -x[:, net.n:]], dim=1)
        evenness = torch.max(torch.abs(net.energy(x)-net.energy(mirrored)))
        baseline_difference = torch.max(torch.abs(
            net.energy(x)-(.5*net.amplitude**2*x.square().sum(-1)+net(x))))
    return {
        'origin_residual_energy': float(origin_h.detach()),
        'origin_residual_gradient_norm_x': float(torch.linalg.norm(origin_g)),
        'origin_residual_hessian_norm_x': float(torch.linalg.norm(origin_hessian)),
        'origin_L_minus_I_norm': float(torch.linalg.norm(lower[0]-torch.eye(net.n))),
        'p_even_energy_max_abs_difference_64_samples': float(evenness),
        'direct_H_vs_H0_plus_residual_max_abs_difference': float(baseline_difference),
        'analytic_statement': (
            'H_PP = diag(sqrt(nu)) L L^T diag(sqrt(nu)); the real lower '
            'triangular L has exp(diagonal) > 0. It is SPD for every finite '
            'real input and finite real-arithmetic weights. H is exactly '
            'quadratic and even in momentum. The residual has zero 0/1/2 '
            'jet at the origin, since L(0)=I and the potential gate is cubic.'),
        'floating_point_limitation': (
            'Exact positivity does not prevent overflow, underflow or poor '
            'conditioning in floating point. Finite numerical checks are '
            'reported separately; no global potential convexity is claimed.'),
    }


def hpp_audit(net, model, x, indices):
    n = model.n
    root_nu = torch.sqrt(model.nu)
    scale = torch.cat([root_nu, root_nu])/net.amplitude
    selected_x = torch.tensor(x[indices])
    z = selected_x/scale
    with torch.no_grad():
        lower, _, raw = net.factor_and_potential(selected_x[:, :n])
        c = lower @ lower.transpose(-1, -2)
        learned = root_nu[None, :, None]*c*root_nu[None, None, :]
        rawq = z[:, :n] @ model.Sq.T
        mass, _ = model.mechanics(rawq)
        scaled_mass = (model.omega0**2/model.E0)*(model.Sq.T @ mass @ model.Sq)
        truth = torch.linalg.inv(scaled_mass)
        evals = torch.linalg.eigvalsh(learned)
        truth_evals = torch.linalg.eigvalsh(truth)
        relative_hpp = torch.linalg.matrix_norm(learned-truth)/torch.linalg.matrix_norm(truth)
        # Inverse Legendre map at fixed Q; velocity is canonical, not a tip speed.
        velocities = (learned @ z[:, n:, None])[:, :, 0]
        recovered = torch.linalg.solve(learned, velocities[:, :, None])[:, :, 0]
        inversion_defect = torch.linalg.vector_norm(recovered-z[:, n:], dim=1)
        inertia = torch.linalg.inv(learned)
        legendre_condition = evals[:, -1]/evals[:, 0]
    auto_defects = []
    momentum_invariance = []
    for j, state in enumerate(z):
        q = state[:n].detach()
        energy = lambda p: net.energy((torch.cat([q, p])*scale)[None, :])[0]
        hess = torch.autograd.functional.hessian(energy, state[n:]).detach()
        alternative = torch.autograd.functional.hessian(energy, state[n:]*1.7+.03).detach()
        auto_defects.append(float(torch.linalg.norm(hess-learned[j])/torch.linalg.norm(learned[j])))
        momentum_invariance.append(float(torch.linalg.norm(hess-alternative)))
    return {
        'sample_indices': [int(i) for i in indices],
        'sample_count': len(indices),
        'object': 'canonical H_PP at fixed Q, same split indices as unrestricted evaluation',
        'learned_minimum_eigenvalues': evals[:, 0].tolist(),
        'truth_minimum_eigenvalues': truth_evals[:, 0].tolist(),
        'learned_maximum_eigenvalues': evals[:, -1].tolist(),
        'summary': {
            'minimum_eigenvalue': float(evals[:, 0].min()),
            'maximum_eigenvalue': float(evals[:, -1].max()),
            'nonpositive_sample_count': int((evals[:, 0] <= 0).sum()),
            'maximum_condition_number': float(legendre_condition.max()),
            'minimum_learned_mass_eigenvalue': float(torch.linalg.eigvalsh(inertia)[:, 0].min()),
            'relative_hpp_frobenius_global': float(torch.linalg.norm(learned-truth)/torch.linalg.norm(truth)),
            'relative_hpp_frobenius_max_sample': float(relative_hpp.max()),
            'formula_vs_autodiff_hpp_max_relative_error': max(auto_defects),
            'momentum_independence_hpp_max_abs_difference': max(momentum_invariance),
            'inverse_legendre_max_absolute_residual_in_P': float(inversion_defect.max()),
            'lower_factor_minimum_diagonal': float(torch.diagonal(lower, dim1=-2, dim2=-1).min()),
            'lower_factor_maximum_diagonal': float(torch.diagonal(lower, dim1=-2, dim2=-1).max()),
            'maximum_absolute_diagonal_log': float(raw[:, net.tril_diag].abs().max()),
            'all_hpp_values_finite': bool(torch.isfinite(learned).all()),
        },
        'positivity_basis': 'Analytic triangular factorization, not inference from these finite samples.',
        'not_established': 'Uniform approximation or condition number bounds, continuum validity, closed-loop performance or KAM.',
    }


def parameter_changes(net, initial):
    result = {}
    for name, parameter in net.named_parameters():
        delta = parameter.detach()-initial[name]
        result[name] = {
            'complex_entries': parameter.numel(),
            'requires_grad': parameter.requires_grad,
            'real_update_norm': float(torch.linalg.norm(delta.real)),
            'imaginary_update_norm': float(torch.linalg.norm(delta.imag)),
            'final_real_norm': float(torch.linalg.norm(parameter.detach().real)),
            'final_imaginary_norm': float(torch.linalg.norm(parameter.detach().imag)),
        }
    return result


def run(args):
    started = time.perf_counter()
    source = Path(__file__).resolve().parent
    input_files = [source/'rod_rom.py', source/'run_learning.py', source/'evaluate_models.py',
                   args.data_dir/'learning_data.npz', args.data_dir/'learning_summary.json',
                   args.data_dir/'evaluation_summary.json']
    initial_hashes = {str(path): sha(path) for path in input_files}
    previous = json.loads((args.data_dir/'learning_summary.json').read_text())
    previous_eval = json.loads((args.data_dir/'evaluation_summary.json').read_text())
    args.amplitude = float(previous['amplitude'])
    raw = np.load(args.data_dir/'learning_data.npz')
    sets = {name: {key: raw[name+'_'+key] for key in ['x', 'h_res', 'g_res', 'q_raw', 'tip_m']}
            for name in ['train', 'validation', 'test', 'ood']}
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    if (out/'learning_summary.json').exists() and not args.allow_replace_own:
        raise RuntimeError('Refusing to overwrite this experiment; use a new output or --allow-replace-own.')
    (out/'run_inputs.json').write_text(json.dumps({
        'source_sha256': sha(Path(__file__)), 'input_hashes': initial_hashes,
        'seed': args.seed, 'steps_label': args.steps, 'amplitude': args.amplitude,
        'width': args.width, 'batch_size': args.batch, 'learning_rate': args.lr,
    }, indent=2)+'\n')
    model = RodROM()
    torch.manual_seed(args.seed)
    rng = np.random.default_rng(args.seed)
    hscale = max(float(np.std(sets['train']['h_res'])), 1e-7)
    gscale = max(float(np.sqrt(np.mean(sets['train']['g_res']**2))), 1e-7)
    net = MechanicalComplexResidual(model.n, args.width, args.amplitude, hscale)
    initial = {name: p.detach().clone() for name, p in net.named_parameters()}
    tx = torch.tensor(sets['train']['x'])
    th = torch.tensor(sets['train']['h_res'])
    tg = torch.tensor(sets['train']['g_res'])
    optimizer = torch.optim.Adam(net.parameters(), lr=args.lr)
    history = []
    best = float('inf')
    best_state = None
    best_step = None
    training_start = time.perf_counter()
    # Match the earlier source exactly: labels 0,...,steps, hence steps+1
    # optimizer updates. This convention is recorded rather than hidden.
    for step in range(args.steps+1):
        idx = rng.integers(0, len(tx), size=args.batch)
        x = tx[idx].clone().requires_grad_(True)
        h = net(x)
        g = torch.autograd.grad(h.sum(), x, create_graph=True)[0]
        loss = ((g-tg[idx])/gscale).square().mean()+.15*((h-th[idx])/hscale).square().mean()
        if not torch.isfinite(loss):
            raise FloatingPointError(f'Nonfinite loss at step {step}; no silent fallback or label change.')
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        grad_norm = torch.nn.utils.clip_grad_norm_(net.parameters(), 10.)
        optimizer.step()
        if step % 200 == 0 or step == args.steps:
            vh, vg = network_prediction(net, sets['validation']['x'])
            metric = scores(vh, vg, sets['validation'], args.amplitude)
            if not np.isfinite(metric['residual_gradient_relative_l2']):
                raise FloatingPointError(f'Nonfinite validation at step {step}.')
            elapsed = time.perf_counter()-training_start
            record = dict(step=step, optimizer_updates=step+1, training_loss=float(loss.detach()),
                          pre_clip_gradient_norm=float(grad_norm), validation=metric, wall_s=elapsed)
            history.append(record)
            if metric['residual_gradient_relative_l2'] < best:
                best = metric['residual_gradient_relative_l2']
                best_step = step
                best_state = {k: v.detach().clone() for k, v in net.state_dict().items()}
            print(json.dumps(dict(amplitude=args.amplitude, seed=args.seed, step=step,
                                  val_residual=metric['residual_gradient_relative_l2'],
                                  best_step=best_step, elapsed_s=elapsed)), flush=True)
    training_seconds = time.perf_counter()-training_start
    net.load_state_dict(best_state)
    net.eval()
    checkpoint_path = out/f'spd_complex_seed{args.seed}.pt'
    torch.save(dict(state_dict=best_state, n=model.n, width=args.width,
                    amplitude=args.amplitude, output_scale=hscale,
                    architecture='MechanicalComplexResidual', best_step=best_step), checkpoint_path)
    (out/f'training_seed{args.seed}.json').write_text(json.dumps(dict(
        history=history, best_validation_step=best_step,
        training_seconds_including_validation=training_seconds,
        parameter_changes=parameter_changes(net, initial)), indent=2)+'\n')
    scale = np.sqrt(np.r_[model.nu.numpy(), model.nu.numpy()])/args.amplitude
    unrestricted_record = next(r for r in previous_eval['complex_checkpoints'] if r['seed'] == args.seed)
    original_training = next(r for r in previous['complex_network'] if r['seed'] == args.seed)
    evaluation = {'splits': {}, 'hpp': {}}
    for name in ['test', 'ood']:
        ph, pg = network_prediction(net, sets[name]['x'])
        metrics = grad_metrics(pg, sets[name], args.amplitude, scale, model.Sq.numpy(),
                               model.omega0, model.E0)
        metrics.update(scores(ph, pg, sets[name], args.amplitude))
        metrics['physical_energy_rmse_J'] = float(model.E0*metrics['energy_rmse'])
        evaluation['splits'][name] = metrics
        indices = np.array(unrestricted_record['hpp'][name]['sample_indices'])
        evaluation['hpp'][name] = hpp_audit(net, model, sets[name]['x'], indices)
        np.savez_compressed(out/f'predictions_{name}.npz', h_res=ph, g_res=pg, sample_indices=np.arange(len(ph)))
    checks = architecture_checks(net, model, sets['test'])
    final_hashes = {str(path): sha(path) for path in input_files}
    if final_hashes != initial_hashes:
        raise RuntimeError('An audited upstream source/input changed during this run.')
    result = {
        'experiment': 'SPD mechanical complex network, predeclared seed 1025, same data and derivative loss',
        'environment': dict(python=platform.python_version(), torch=torch.__version__, numpy=np.__version__,
                            scipy=scipy.__version__, threads=torch.get_num_threads()),
        'source_sha256': sha(Path(__file__)),
        'source_and_data_hashes_before_after_equal': final_hashes == initial_hashes,
        'upstream_input_hashes': initial_hashes,
        'data_directory': str(args.data_dir),
        'data_sha256': sha(args.data_dir/'learning_data.npz'),
        'data_hash_matches_upstream_summary': sha(args.data_dir/'learning_data.npz') == previous['data_sha256'],
        'configuration_dof': model.n,
        'phase_dimension': 2*model.n,
        'amplitude': args.amplitude,
        'split_counts': {name: len(data['x']) for name, data in sets.items()},
        'split_overlap': split_checks(sets),
        'seed': args.seed,
        'width': args.width,
        'complex_trainable_parameters': sum(p.numel() for p in net.parameters()),
        'real_trainable_parameters': sum(2*p.numel() for p in net.parameters()),
        'steps_label': args.steps,
        'optimizer_updates': args.steps+1,
        'batch_size': args.batch,
        'learning_rate': args.lr,
        'gradient_clip_norm': 10.,
        'energy_loss_weight': .15,
        'output_scale': hscale,
        'gradient_loss_scale': gscale,
        'best_validation_step': best_step,
        'best_validation_residual_gradient_relative_l2': best,
        'training_seconds_including_validation': training_seconds,
        'total_seconds_including_ROM_setup_evaluation': time.perf_counter()-started,
        'checkpoint_sha256': sha(checkpoint_path),
        'parameter_changes': parameter_changes(net, initial),
        'architecture_checks': checks,
        'evaluation': evaluation,
        'same_seed_unrestricted_comparison': {
            'real_trainable_parameters': unrestricted_record['real_trainable_parameters'],
            'training_seconds': original_training['training_seconds'],
            'checkpoint_sha256': unrestricted_record['checkpoint_sha256'],
            'splits': unrestricted_record['splits'],
            'hpp_summary': {name: unrestricted_record['hpp'][name]['summary']['complex'] for name in ['test', 'ood']},
        },
        'upstream_linear_and_analytic_baselines': previous_eval['baselines'],
        'limitations': [
            'This is a full 12-configuration-DoF mechanical prior, not dimensional reduction, and it is more restrictive in momentum than an arbitrary phase-space neural Hamiltonian.',
            'The SPD network has more parameters than the unrestricted network; this is not a controlled comparison of real versus complex representation or equal-capacity architectures.',
            'Shared Q-only trainable complex hidden layers and split tanh are real analytic on real input, not a holomorphic neural function of phase-space coordinates.',
            'Reused test/OOD data informed this architectural correction after observed H_PP failure. These are exploratory comparisons, not an untouched prospective test.',
            'Only one predeclared seed and unchanged hyperparameters are used per amplitude; no robustness claim across initialization or new data.',
            'No training for blood flow/contact, no magnetic actuator rollout, no integration convergence test and no KAM certificate are supplied by this experiment.',
            'The model is the same 12-DoF strain-Ritz Kirchhoff family; positivity of this reduced inverse mass does not establish continuum, patient or full Cosserat validity.',
        ],
    }
    (out/'learning_summary.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: result[key] for key in ['amplitude', 'real_trainable_parameters',
                                                 'best_validation_step', 'training_seconds_including_validation',
                                                 'total_seconds_including_ROM_setup_evaluation']}, indent=2), flush=True)
    print(json.dumps(evaluation, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=Path('stage2/results/learning'))
    parser.add_argument('--output', type=Path, default=Path('stage2/results/learning_spd/local'))
    parser.add_argument('--steps', type=int, default=6000)
    parser.add_argument('--width', type=int, default=48)
    parser.add_argument('--batch', type=int, default=256)
    parser.add_argument('--lr', type=float, default=.003)
    parser.add_argument('--seed', type=int, default=1025)
    parser.add_argument('--allow-replace-own', action='store_true')
    args = parser.parse_args()
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    run(args)


if __name__ == '__main__':
    main()
