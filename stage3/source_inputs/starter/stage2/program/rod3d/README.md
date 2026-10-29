# Three-dimensional Cosserat magnetic catheter benchmark

This program runs a geometrically nonlinear **three-dimensional** Cosserat rod with translational and rotational inertia, both bending directions, twist, shear and extension. It uses the official PyElastica 1.0.0 rod and PositionVerlet implementation. All environmental operators and magnetic controllers are explicitly implemented in `model.py`.

The current model contains a prescribed pulsatile reference flow and a stationary curved tube with penalty contact and friction. **It is not a two-way fluid–structure interaction solver.** It is also not a reproduction of Tong et al.'s insertion experiment. The material and magnetic values are anchored to that paper; density, damping, flow, contact and microgravity inputs are explicitly declared engineering or synthetic choices.

The accepted tracking tests use modest deflections. Support for finite rotations in the equations is not presented as comprehensive large-deflection validation. `flow.enabled` switches the immersed-fluid environment, including its buoyancy density correction. For a stationary fluid, keep it enabled and set the reference speed to zero; disabling it is not equivalent to setting blood velocity to zero.

## Reproduce

From the directory containing `stage2/`:

```bash
python3.12 -m venv stage2/program/rod3d/.venv
stage2/program/rod3d/.venv/bin/python -m pip install -r stage2/program/rod3d/requirements.txt
stage2/program/rod3d/.venv/bin/python stage2/program/rod3d/verify_operators.py
stage2/program/rod3d/.venv/bin/python stage2/program/rod3d/run_study.py --resume
stage2/program/rod3d/.venv/bin/python stage2/program/rod3d/failure_study.py
stage2/program/rod3d/.venv/bin/python stage2/program/rod3d/run_wall_sensitivity.py
stage2/program/rod3d/.venv/bin/python stage2/program/rod3d/run_learning_comparison.py --resume
stage2/program/rod3d/.venv/bin/python stage2/program/rod3d/run_biot_savart.py
stage2/program/rod3d/.venv/bin/python stage2/program/rod3d/run_biot_savart_constrained.py
stage2/program/rod3d/.venv/bin/python stage2/program/rod3d/run_biot_savart_ramped.py
stage2/program/rod3d/.venv/bin/python stage2/program/rod3d/run_womersley.py
stage2/program/rod3d/.venv/bin/python stage2/program/rod3d/analyze.py
stage2/program/rod3d/.venv/bin/python stage2/program/rod3d/finalize_notes.py
```

The learning comparison additionally requires the delivered `stage2/results/learning/feedforward/{linear,analytic,complex,truth}.npz`. The coil branch imports the delivered `stage2/program/coil_field.py` and uses the coil geometry documented in `stage2/results/coil/`.

The original coil comparison uses zero-order-held currents and only a discrete sample-to-sample slew limit. `run_biot_savart_ramped.py` is the final continuous piecewise-linear current implementation: the actual current has a bounded time derivative almost everywhere. Both it and the constrained ZOH comparison enforce field constraints on 387 points of a source-free tube around the lumen; the 0.12 m ideal-affine sphere contains the synthetic coil conductors and is not used as a source-free full-coil workspace. The sampled limits are not a continuous spatial field-bound certificate. `run_womersley.py` changes only the reference-flow profile to a flux-matched local Womersley harmonic, with explicit wall/flux/ODE checks.

`run_study.py --only CASE_NAME` runs selected entries; `--resume` accepts matching configurations and the exact implementation hash. A stand-alone example is:

```bash
stage2/program/rod3d/.venv/bin/python stage2/program/rod3d/model.py --config stage2/program/rod3d/config_position_feedback.json --name example --elements 64 --dt 5e-6 --duration 2 --sample-dt .005 --mode feedback
```

`config.json` deliberately preserves the first controller choice with noncollocated velocity feedback, which failed the long-time checks. The accepted finite-time comparison uses `config_position_feedback.json`: identical physics, position gain 1.5 and velocity gain **zero**. Neither the failing experiment nor its configuration has been overwritten.

The `.venv`, downloaded wheels, extracted third-party source and compilation caches are not needed in the distributable archive. Requirements and recorded version/hash information suffice to reconstruct them. The recorded environment used Python 3.12, NumPy 2.3.5, SciPy 1.17.0, Numba 0.62.1 and llvmlite 0.45.1. A first attempt with Numba 0.68.1/llvmlite 0.50.0 failed while loading LLVM; it was replaced in the isolated environment before scientific runs. No global package installation was used.

## Coordinates, units and input contract

All values are SI. Initially the rod extends from `(0,0,0)` to `(0,0,0.1)` along `+z`. The base position and first material frame are fixed. The distal end is free. Current insertion is not implemented.

Directors `D[e]` map spatial vectors to body coordinates. Thus a body-fixed dipole becomes `mu_space = D.T @ mu_body`, and a spatial torque becomes `tau_body = D @ tau_space`.

The input has eight components:

```text
[Bx, By, Bz, Gxx, Gyy, Gxy, Gxz, Gyz]
```

`B` is magnetic flux density in tesla; `G_ij = dB_i/dx_j` is in tesla/metre. The gradient is symmetric and trace free:

```text
G = [[Gxx, Gxy, Gxz], [Gxy, Gyy, Gyz], [Gxz, Gyz, -Gxx-Gyy]].
```

The field expansion point is `(0,0,0.1)`. An additional controller may supply an NPZ with `time_s[nt]` and `u_ff[nt,8]`, covering the entire simulation interval. Set `controller.feedforward_npz` in a copied configuration. A relative filename is resolved from this program directory. The values must include the axial bias already. The program interpolates the feedforward, adds exactly the same position feedback as the baseline, then applies the same field/gradient limits. In `coil_allocated` mode the resulting field request passes through the same 12-coil current allocator and is held between 2 ms updates.

## Outputs and audit

Every successful case writes:

* `summary.json`: dimensions, step size, run time, error, contact, constraints and energy-work diagnostics.
* `parameters.json`: the complete configuration used in that run.
* `environment.json`: actual dependency versions, Python version, implementation SHA256, and external feedforward SHA256 where relevant.
* `diagnostics.csv`: SI scalar time histories.
* `trajectory.npz`: position `r[time,node,3]`, velocity `v`, directors `directors[time,element,3,3]`, body angular velocity, shear/stretch and bending/twist strains, requested and actual inputs, targets, contact, magnetic/fluid/contact forces and couples, and coil currents.

The reference coordinate, exact integrated material dipoles and the centroid of each magnetic subinterval are stored in the trajectory. The distal 5 mm magnet is integrated using exact element overlap, so changing the mesh does not change total dipole moment.

A numerical exception writes `failure.json`, `partial_trajectory.npz` and `partial_diagnostics.csv`, then propagates the exception. The failure study also retains a case that completed but was rejected because of large strains and a badly unresolved work balance. Finite numbers by themselves are not treated as validation.

`analyze.py` produces `comparison.csv`, `analysis.json`, full Biot–Savart/affine comparisons at actual sampled magnetic points, and editable SVG/PNG figures. Spatial refinement compares 16, 32 and 64 elements at the same 5 microsecond step. Time refinement compares 10, 5 and 2.5 microseconds at 32 elements. Differences are measured in a common interpolated reference coordinate and matched saved times. They are empirical finite-time refinement evidence, not a general continuum convergence proof.

## Scope of structural claims

The magnetic and contact elastic operators pass independent energy directional-derivative tests. The spatial/body torque power identity, Coulomb bound, exact magnetic overlap, and source-free affine field constraints are checked separately. The contact dissipation and structural drag have nonpositive instantaneous mechanical power, while the prescribed flowing fluid can supply energy to the rod.

The official PositionVerlet name does not establish symplecticity of the complete system with relative fluid drag, friction, feedback, field saturation or sampled current allocation. Conservative pure-torsion refinement is reported separately. No full-system KAM, passivity, asymptotic stability or PDE convergence theorem is claimed by this code.

## Primary sources

* Tong et al., *Journal of the Mechanics and Physics of Solids* 203 (2025), 106198, DOI [10.1016/j.jmps.2025.106198](https://doi.org/10.1016/j.jmps.2025.106198), published PDF p. 10, §5.1, and pp. 10–11 numerical setup. [Author institution PDF](https://eprints.ncl.ac.uk/file_store/production/306197/7CAB59D2-D36A-4A12-8648-428A2D798BBC.pdf).
* Gazzola, Dudte, McCormick and Mahadevan, *Royal Society Open Science* 5 (2018), 171628, DOI [10.1098/rsos.171628](https://doi.org/10.1098/rsos.171628), especially §§2–3 and the qualifications in §3.3. [Author group PDF](https://www.cosseratrods.org/publications/pubs/2018_RSOS.pdf).
* [Official PyElastica repository](https://github.com/GazzolaLab/PyElastica) and [version 1.0.0 API](https://docs.cosseratrods.org/en/v1.0.0/api/rods.html). Relevant installed source was inspected before use.
* Lunnoo and Puangmali, *Nanoscale Research Letters* 10 (2015), 426, DOI [10.1186/s11671-015-1127-5](https://link.springer.com/article/10.1186/s11671-015-1127-5), Methods near Eq. (14) and Eq. (16). The density and high-shear viscosity are adopted as modeling conventions; that paper's entire non-Newtonian fluid/particle model is not being imported.
