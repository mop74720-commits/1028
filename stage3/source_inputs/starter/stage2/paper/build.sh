#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build
for name in framework_en framework_zh; do
  xelatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=build "$name.tex" > "build/${name}_pass1.stdout" 2>&1
  BIBINPUTS="$PWD:" bibtex "build/$name" > "build/${name}_bibtex.stdout" 2>&1
  xelatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=build "$name.tex" > "build/${name}_pass2.stdout" 2>&1
  xelatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=build "$name.tex" > "build/${name}_pass3.stdout" 2>&1
  cp "build/$name.pdf" "$name.pdf"
done
