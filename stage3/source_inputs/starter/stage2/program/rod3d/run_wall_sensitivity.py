"""Separate penalty-softness error from spatial/time refinement error."""
from pathlib import Path
import json
from model import load_config,run_case

ROOT=Path(__file__).resolve().parent
out=ROOT.parents[1]/'results'/'rod3d'
summaries=[]
for stiffness in [20000.,200000.]:
    cfg=load_config(ROOT/'config_position_feedback.json')
    cfg['lumen']['contact_penalty_N_per_m_power_2p5']=stiffness
    name=f'contact_penalty_{int(stiffness)}_n64_h5us'
    summaries.append(run_case(name,out,cfg,64,5e-6,2.,.005,'contact_stress'))
    (out/'wall_penalty_sensitivity.json').write_text(json.dumps(summaries,indent=2))
