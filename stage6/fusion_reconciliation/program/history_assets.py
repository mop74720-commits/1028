"""Inventory scientific assets and collect byte-identical actual rerun outputs."""
from pathlib import Path
import hashlib
import json
import shutil
from materials import resolve_source,BASE


def main():
    source=resolve_source();out=BASE/'results/history'
    suffixes={'.pt','.pth','.ckpt','.npz','.npy','.mat','.h5','.hdf5','.mph','.hdf'}
    assets=[dict(path=str(p.relative_to(source)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
        for p in source.rglob('*') if p.is_file() and p.suffix.lower() in suffixes]
    record=dict(archive='stage3/source_inputs/v10/v10_birkhoff_20261028_no_fonts_for_github.zip',assets=assets,
        missing_frozen_classes=['Original v10 S1 Fourier torus candidates and Arb inputs','Original COMSOL .mph and exported identification trajectories',
            'Stage2 full complex and SPD trained .pt weights and matching .npz labels'],
        caution='The one included NPZ contains new two-mode convergence traces, not these historical training/certificate inputs.',
        authority='english/sections/endmatter.tex Data and code availability; supp_experiments.tex sx:migration-table')
    (out/'scientific_asset_inventory.json').write_text(json.dumps(record,indent=2)+'\n')
    result=out/'fusion_original_reproduction'
    run=json.loads((result/'execution.json').read_text())
    if run['status']!='completed':raise RuntimeError('Only collect outputs after complete successful logged rerun')
    copied=Path(run['scratch'])/'reproduction'
    exported=[]
    for p in (copied/'framework_experiments').glob('*'):
        if p.suffix not in {'.json','.npz'} or p.name not in ['matrix_structure_results.json','closed_loop_convergence_results.json','closed_loop_convergence_traces.npz','algebraic_defect_results.json','nonlinear_weighted_results.json']:continue
        dest=result/p.relative_to(copied);dest.parent.mkdir(parents=True,exist_ok=True)
        digest=hashlib.sha256(p.read_bytes()).hexdigest()
        if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest()!=digest:raise ValueError('Refuse overwrite of different evidence')
        shutil.copyfile(p,dest)
        exported.append(dict(path=str(dest.relative_to(BASE)),sha256=digest,byte_identical_to_supplied=digest==run['source_sha256'][str(p.relative_to(copied))]))
    (out/'framework_output_collection.json').write_text(json.dumps(dict(source='logged actual completed framework run, not a new numerical rerun',outputs=exported),indent=2)+'\n')

if __name__=='__main__':main()
