"""Compile the integrated article and supplement, retaining cross references."""
from pathlib import Path
import argparse
import os
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output"
LANGUAGES = {
    "en": ("english", "pdflatex", "v10_Integrated_EN.pdf", "v10_Integrated_EN_Supplement.pdf"),
    "zh": ("chinese", "xelatex", "v10_Integrated_ZH.pdf", "v10_Integrated_ZH_Supplement.pdf"),
}


def build(language):
    # Each invocation owns its auxiliary files. Separate build directories
    # also keep interrupted or concurrent runs from truncating source indexes.
    folder = LANGUAGES[language][0]
    (ROOT / "qa").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f"build_{language}_", dir=ROOT / "qa") as temporary:
        staging = Path(temporary)
        work = staging / folder
        work.mkdir()
        for source in (ROOT / folder).iterdir():
            if source.is_file() and source.suffix in (".tex", ".cls"):
                shutil.copy2(source, work / source.name)
        for directory in ("sections", "figures"):
            shutil.copytree(ROOT / folder / directory, work / directory)
        if language == "zh":
            shutil.copytree(ROOT / "fonts", staging / "fonts")
        compile_staged(language, work)


def compile_staged(language, work):
    folder, engine, main_name, supplement_name = LANGUAGES[language]
    if not shutil.which(engine):
        raise RuntimeError(f"Required TeX engine is unavailable: {engine}")
    if language == "zh" and not shutil.which("xdvipdfmx"):
        raise RuntimeError("Required XeTeX PDF converter is unavailable: xdvipdfmx")
    environment = dict(os.environ)
    environment["TEXINPUTS"] = str(ROOT / "texmf/tex") + "//" + os.pathsep + environment.get("TEXINPUTS", "")
    (ROOT / "qa").mkdir(exist_ok=True)
    OUTPUT.mkdir(exist_ok=True)
    for old in (ROOT / "qa").glob(f"build_{language}_*.txt"):
        old.unlink()
    for old in (ROOT / "qa").glob(f"aux_{language}_*.txt"):
        old.unlink()
    # Preserve complete auxiliary snapshots and atomically restore them before
    # each pass. A late writer on an old inode cannot truncate the next pass's
    # input. This also keeps the two documents' cross-reference state explicit.
    auxiliary_snapshots = {}

    def restore_auxiliary():
        for filename, content in auxiliary_snapshots.items():
            destination = work / filename
            temporary = work / (filename + ".restore")
            temporary.write_text(content, encoding="utf-8")
            temporary.replace(destination)

    # The documents cross-reference one another. The ordered passes resolve
    # labels without importing a stale auxiliary file from another language.
    for number, name in enumerate(("supplement", "main") * 3, 1):
        restore_auxiliary()
        command = [engine, "-interaction=nonstopmode", "-halt-on-error",
                   "-file-line-error", "-no-shell-escape"]
        if language == "zh":
            # Resolve every reference in XDV first, then convert each final
            # document once. No PDF-converter subprocess overlaps TeX passes.
            command.append("-no-pdf")
        command.append(name + ".tex")
        result = subprocess.run(
            command,
            cwd=work, env=environment, capture_output=True, text=True, errors="replace",
            timeout=240,
        )
        (ROOT / "qa" / f"build_{language}_{number}_{name}.txt").write_text(
            result.stdout + result.stderr, encoding="utf-8"
        )
        if result.returncode:
            print((result.stdout + result.stderr)[-12000:])
            raise RuntimeError(f"{language}: {name} compilation failed")
        # Import mathematical labels only. Importing all of the other document's
        # aux file would duplicate natbib entries and sagej's FirstPage/LastPage.
        labels = []
        aux_content = (work / (name + ".aux")).read_text(encoding="utf-8")
        if "\\gdef \\@abspage@last" not in aux_content:
            raise RuntimeError(f"Incomplete auxiliary output after {language}/{name} pass {number}")
        auxiliary_snapshots[name + ".aux"] = aux_content
        (ROOT / "qa" / f"aux_{language}_{number}_{name}.txt").write_text(aux_content, encoding="utf-8")
        for line in aux_content.splitlines():
            if line.startswith("\\newlabel{") and not re.match(
                r"\\newlabel\{(?:FirstPage|LastPage)\}", line
            ):
                labels.append(line)
        cross_references = "\\relax\n" + "\n".join(labels) + "\n"
        auxiliary_snapshots[name + "_xr.aux"] = cross_references
        (work / (name + "_xr.aux")).write_text(cross_references, encoding="utf-8")
        outline = work / (name + ".out")
        if outline.exists():
            auxiliary_snapshots[name + ".out"] = outline.read_text(encoding="utf-8")
        current_aux = (work / (name + ".aux")).read_text(encoding="utf-8")
        if current_aux != aux_content:
            raise RuntimeError(f"Auxiliary file changed unexpectedly after {language}/{name} pass {number}")
        print(f"{language} pass {number}: {name}, {len(aux_content.encode('utf-8'))} auxiliary bytes", flush=True)
    restore_auxiliary()
    for name in ("main", "supplement"):
        log = (work / (name + ".log")).read_text(errors="replace")
        warnings = [line for line in log.splitlines()
                    if re.search(r"undefined|multiply defined|Overfull|Missing character", line)]
        print(f"{language}/{name}: {len(warnings)} review warnings")
        if warnings:
            raise RuntimeError("Final document requires review:\n" + "\n".join(warnings[:40]))
    if language == "zh":
        for name in ("main", "supplement"):
            result = subprocess.run(
                ["xdvipdfmx", "-o", name + ".pdf", name + ".xdv"],
                cwd=work, env=environment, capture_output=True, text=True,
                errors="replace", timeout=240,
            )
            (ROOT / "qa" / f"build_{language}_pdf_{name}.txt").write_text(
                result.stdout + result.stderr, encoding="utf-8"
            )
            if result.returncode:
                raise RuntimeError((result.stdout + result.stderr)[-12000:])
    for source, destination in (("main.pdf", main_name), ("supplement.pdf", supplement_name)):
        shutil.copy2(work / source, OUTPUT / destination)
        print(f"Built {destination}", flush=True)
    for name in ("main", "supplement"):
        for suffix in (".aux", ".log", ".pdf", ".out", "_xr.aux"):
            source = work / (name + suffix)
            if source.exists():
                shutil.copy2(source, ROOT / folder / source.name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", choices=("en", "zh", "all"), default="all")
    args = parser.parse_args()
    for language in (("en", "zh") if args.language == "all" else (args.language,)):
        build(language)
