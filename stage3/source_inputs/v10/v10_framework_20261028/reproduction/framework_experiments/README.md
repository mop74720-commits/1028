# Direction I framework verification

This directory contains the additional P1/P2/P3 verification suite for the
integrated v10 article. It reads the audited `../new_baseline.json`; it does
not select new physical material parameters or refit a controller for each
integration step. The existing identification and control records remain
under `../experiments/`.

## Run the calculations

From the project root, with the versions in `requirements.txt`:

```sh
python3 reproduction/framework_experiments/run_all.py
```

Individual groups can be reproduced independently:

```sh
python3 reproduction/framework_experiments/run_all.py --experiment matrix
python3 reproduction/framework_experiments/run_all.py --experiment closed
python3 reproduction/framework_experiments/run_all.py --experiment defect
python3 reproduction/framework_experiments/run_all.py --experiment weighted
```

The project-level `python3 reproduction/run_all.py` first regenerates the FE
baseline and the existing control/damping records, then runs this suite.
The checks in each group verify its stated order, algebraic equivalence or
geometric identity. Each JSON records inputs, norms, reference protocols,
source hashes and the assertion status.

## Experimental meaning and outputs

| Group | Model and question | Output |
| --- | --- | --- |
| `matrix` | Artificial dimensionless positive mass/stiffness matrices in 1, 2 and 4 degrees of freedom. Full and eliminated ordinary-midpoint trajectories are compared, including a nonproportional damping family in dimensions 2 and 4. Weighted midpoint, conservative midpoint and Central4 use their stated target fields. | `matrix_structure_results.json` |
| `closed` | The revised nonlinear magnetic model, with deliberately fixed errors `delta_beta=0.02`, `delta_gamma=0.01`. The same physical-port implementation is compared with an independently integrated explicit actual closed field and with nominal `h0`. A separate conservative `h0` Central4 test checks fourth order using the complete potential derivatives. | `closed_loop_convergence_results.json`, `closed_loop_convergence_traces.npz` |
| `defect` | A separate one-degree-of-freedom harmonic oscillator. Known increment residuals `r_k=0.01*Delta**q*(1,0)`, `q=1,2,3`, are deliberately injected; every actual residual is recorded. Added error relative to unperturbed midpoint is distinguished from total error relative to the continuous flow. | `algebraic_defect_results.json` |
| `weighted` | The nonlinear magnetic plant and a known fixed-error closed field. Ordinary and weighted midpoint approximate the same field in each case. Their ideal tangents are compared against the exact exponential conformal factor. | `nonlinear_weighted_results.json` |

The matrix and manufactured-defect constants are declared algorithm-test
choices. The imposed closed-loop coefficient errors are test settings, not
literature measurements, specimen uncertainty estimates or outputs of the
preceding fit. The weighted comparison uses known fields to test a method;
it does not disclose unknown coefficients to the learned controller.

All state errors use Euclidean norms. Maximum errors are taken over all
saved times, not only the final state. Matrix references use
`scipy.linalg.expm`; nonlinear references use independently evaluated DOP853
integrations at two refinement settings. Reference-refinement differences
are recorded diagnostics and are not interval enclosures. Increment residual
infinity norms and ideal-tangent spectral norms are explicitly named in the
records. An ideal implicit tangent at a solved point is not the derivative
of a finite floating-point Newton program.

The primary control-ablation runs continue to use midpoint. The Central4
result concerns the autonomous conservative branch with the full nonlinear
`h0`; no fourth-order claim is assigned to general damped feedback.
The suite does not provide high-mode controlled trajectories, a COMSOL
comparison, sensor/coil calibration, a saturation study or a finite-amplitude
KAM certificate.

## Regenerate manuscript assets

The current English text templates are under `authoring/`.
`build_manuscript_assets.py` reads numerical JSON records, inserts the audited
numbers into three English sections, and draws the four current figures.
It does not rerun an experiment. From the project root:

```sh
python3 reviews/build_analysis_assets.py
```

That command intentionally writes English assets. Re-review and freeze the
English master after an intentional revision before updating its translation.
The archived pre-integration two-route generator and templates are in
`reviews/historical/two_route_20261028/`; they are not current entry points.

The Chinese-only commands are:

```sh
python3 reviews/translate_framework_numerics.py
python3 reviews/build_chinese_figures.py
python3 reviews/check_analysis_translation.py
```

The translation script checks the expected frozen English source. It writes
only the three Chinese numerical sections. The figure command writes only
Chinese figures; it never regenerates the English PDFs. The checker compares
mathematics, numeric tokens, labels/references/citations, figure data and plot
geometry. Chinese prose remains an authored translation that also requires
reading and page review.

Compile the article and its supplement separately from numerical generation:

```sh
python3 build_pdfs.py --language en
python3 build_pdfs.py --language zh
python3 reviews/build_framework_map.py
python3 reviews/validate_manuscripts.py
```

`framework_numeric_provenance.json` under `reviews/` connects rendered values
to their JSON sources. The combined framework mapping resolves the supplied
nine-page framework to the actual compiled sections and equations. The
English freeze checks protect the reviewed source and figures during
translation; intentional scientific changes require a new review and freeze.
