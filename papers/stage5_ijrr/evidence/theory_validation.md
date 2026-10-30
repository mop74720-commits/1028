# Theory validation

The main sections and supplementary bodies were written only from the permitted original1025 anchors and Stage 3–5 source snapshot. No Stage 6 or later research source was opened or used. Existing research files were not modified and no scientific experiment was rerun.

## Mathematical review

An independent read-only review checked the Birkhoff sign and two-form factor, sourced residual and gauge terminal term, Moser pullback and time sensitivities, endpoint compatibility/transversality, nonzero initial gauge, fixed-coordinate recursion, noncommuting left solve, Central4 correction and primitive, and separated finite-time bounds. Review corrections made the endpoint closedness/nondegeneracy hypotheses explicit, specified a closed convex self-mapped set for Banach's theorem, clarified a Chinese gauge sentence, and removed a malformed fraction escape.

The general nonautonomous transport recurrence comes from `stage5/proofs/birkhoff_transport.md` section 6. The fixed-coordinate generator PDE and local analytic recursion come from `stage5/proofs/corrected_mathematics.md` sections 5–5.1, B1–B4. The text attributes analyticity to the local analytic flow and endpoint inverse; it explicitly limits implemented 24-dimensional transport branches to smooth autonomous fields with moving charts. Moser domain bounds remain conditional estimates for the specified polynomial, without interval certification.

## Bilingual and LaTeX checks

- `english/sections/theory.tex` / `chinese/sections/theory.tex`: 27 identical displayed equation blocks; inline mathematical expressions match as multisets; label lists match.
- `supplement/theory_en.tex` / `supplement/theory_zh.tex`: 53 identical displayed equation blocks; inline mathematical expressions match as multisets; label lists match.
- 85 unique labels across English main/supplement; no brace imbalance or stray control characters.

Independent XeLaTeX checks used isolated output jobs in `/tmp/stage5_theory_layout`, with the supplied SAGE class/preamble for the two main sections and the supplied article preambles for the two supplements. All four jobs compiled successfully after equation reflow, with no overfull boxes in the theory-only documents. These checks did not write to the root build outputs. The root agent separately builds the complete manuscripts.

## Claim traceability

`theory_claims.csv` contains 30 claims with manuscript labels, exact source paths and anchors, proof/conditional/implemented status, scope limitations, and SHA-256 digests of the source files. Each major claim in the TeX also carries an adjacent source comment. Model mass is normalized in this section; integration step is eta, and K_s denotes stiffness while K denotes a two-form matrix.
