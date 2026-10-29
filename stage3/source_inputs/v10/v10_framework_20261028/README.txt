V10 + DIRECTION I: THREE-SUBPROBLEM FRAMEWORK INTEGRATION
28 October 2026
=======================================================

1. What this revision integrates

This revision follows the supplied Direction I research framework through
three linked questions: (P1) Birkhoff/generating-function discretization and
its matrix implementation; (P2) integral identification and physically realized
residual compensation; (P3) structure, solver-residual convergence and
conditional discrete KAM for that controlled scheme.

The original v10 six-section article organization and sagej.cls are retained.
The verified material, magnet and modal baseline supplies one common model.
The learning-reference tracking route is retained in Supplement S4 as a related
extension; it is no longer a coequal organizing objective of the main paper.

english/main.tex and english/supplement.tex are the English master.
chinese/ contains their complete corresponding translations.
The four PDFs are in output/. The Chinese revision note and the mapping in
reviews/ explain how the supplied framework enters the article.

2. Source provenance

Original manuscript repository:
https://github.com/mop74720-commits/IJRR_CHNN_KAM_v10_20261007

Manuscript source commit:
82519542dd057e8fbd6d6879ef33217761e8cbbb

The later repository head 8761d70239a54985b40c0a6196f52e53d5b2e4d2 was
checked during the preceding parameter audit. Its additional commit changes
README, an artifact index and an export script, not the manuscript or figures.
The supplied nine-page Direction I PDF is preserved as
provenance/source_direction_one_framework.pdf; its hash and selected identity
are recorded in provenance/selected_framework.json.

The source framework uses the old illustrative parameter set. Its physical
boundary conditions and numerical results are not copied into the new model:
endpoint mass and rotary inertia, the modal coordinates and all dependent
numbers follow the audited baseline. Source equations are cross-referenced
by their role; the integrated article has its own consistent numbering.
provenance/integration_patch.diff is a review diff of the final English TeX
against the original v10 sources; use the complete project for compilation.
The preceding parameter-stage diff is explicitly named
previous_parameter_integration_patch.diff and is historical provenance only.

3. Build the documents

Requirements: Python 3 and TeX with pdfLaTeX, XeLaTeX, xdvipdfmx, amsmath,
amssymb, amsthm, mathtools, graphicx, booktabs, array, tabularx, multirow,
microtype, etoolbox, xr-hyper, hyperref, fontspec and Latin Modern OpenType
fonts. The original sagej.cls is supplied. Compatible xeCJK/ctex packages from
the final TeX Live 2023 archive are in texmf/, with upstream source. The CJK
fonts and their licenses are in fonts/.

    python3 build_pdfs.py --language en
    python3 build_pdfs.py --language zh

Each build uses an isolated working directory and ordered cross-reference
passes. The Chinese passes produce XDV before converting each final document
once with xdvipdfmx. Only a completed build without unresolved references,
missing characters or overfull boxes is copied into output/.
Keep each main PDF beside its supplement for the relative PDF cross-links.
The *_xr.aux files in the source folders are frozen label indexes; use the
complete build after changing labels or numbered statements.

4. Reproduce the computations

The numerical dependencies are Python 3, NumPy and SciPy; Matplotlib is needed
for figures. requirements.txt records the tested versions.

    python3 reproduction/run_all.py

This regenerates the FE baseline, minimal compensation and related tracking
examples, damping scenarios, and the framework-verification suite. Individual
suite entry points are also supplied under reproduction/experiments/ and
reproduction/framework_experiments/. The numerical data and their experiment
settings are included. Historical absolute paths inside old result metadata
record the original run locations; the executable scripts use package paths.

P1 uses declared artificial matrix models as algorithm checks. P2 uses a
noiseless one-feature conservative residual, beta=0.2, on the revised catheter
model. P3 distinguishes the discretization error of a fixed actual closed loop
from its deviation from h0, and labels deliberate algebraic-defect experiments
as such. These tests are not general network training, hardware experiments,
full-modal controlled-response validation or an interval KAM certificate.

5. Parameters, theory and remaining validation

Material inputs are published reference values at stated preparation
conditions. Magnet properties are manufacturer-grade specifications with a
declared geometry and nominal selection. Derived quantities are recomputed.
Geometry, damping scenarios, control/test settings and numerical grids are
explicit choices rather than specimen measurements.

Exact symplecticity concerns the exactly defined conservative implicit map.
Residual damping and finite algebraic error have their own structure and
convergence statements. Discrete KAM remains conditional on its analytic
domain, remainder, twist, nonresonance and smallness requirements.

The proposed 2/4/8/64-mode tests retain the trained two-mode controller and
require an explicit full-model residual and tip-angle treatment. This is
separate from the linear FE mesh check and from a conditional full-modal
construction using stronger exact feedback. COMSOL, sensing/actuator
calibration, noise/saturation studies and a finite-amplitude certificate retain
their stated uncompleted status. Old v10 results are not relabeled as new ones.

6. Integrity and language

English is completed and reviewed before its Chinese translation is frozen.
The validation report compares labels, numbered statements and mathematical
content. The framework mapping gives the location and evidence status of each
source component. MANIFEST.json records the files and hashes in this delivery.
Intermediate compiler logs and review images are excluded from the archive.
