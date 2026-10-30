#!/usr/bin/env bash
set -euo pipefail
paper_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
export TEXINPUTS="$paper_dir/template//:${TEXINPUTS:-}"
export BSTINPUTS="$paper_dir/template//:${BSTINPUTS:-}"
mkdir -p "$paper_dir/build_logs"
build_one() {
  local folder=$1 source=$2 target=$3
  (cd "$paper_dir/$folder"
   xelatex -interaction=nonstopmode -halt-on-error "$source.tex" > "$paper_dir/build_logs/${target}_pass1.txt"
   bibtex "$source" > "$paper_dir/build_logs/${target}_bibtex.txt"
   xelatex -interaction=nonstopmode -halt-on-error "$source.tex" > "$paper_dir/build_logs/${target}_pass2.txt"
   xelatex -interaction=nonstopmode -halt-on-error "$source.tex" > "$paper_dir/build_logs/${target}_pass3.txt"
   cp "$source.pdf" "$paper_dir/$target.pdf"
   cp "$source.log" "$paper_dir/build_logs/$target.log"
   cp "$source.blg" "$paper_dir/build_logs/$target.blg")
}
build_one english main Stage5_IJRR_EN
build_one chinese main Stage5_IJRR_ZH
build_one supplement main_en Stage5_IJRR_Supplement_EN
build_one supplement main_zh Stage5_IJRR_Supplement_ZH
printf 'Built four PDFs in %s\n' "$paper_dir"
