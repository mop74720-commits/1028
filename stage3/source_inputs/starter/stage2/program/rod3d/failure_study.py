"""Preserve the unsuccessful noncollocated velocity-feedback experiment."""
from pathlib import Path
import json
import numpy as np
from model import run_case,load_config

ROOT=Path(__file__).resolve().parent
out=ROOT.parents[1]/'results'/'rod3d'
summaries=[]
for dt,label in [(1e-5,'10us'),(5e-6,'5us'),(2.5e-6,'2p5us')]:
    name='failed_velocity_feedback_n32_h'+label
    try:
        result=run_case(name,out,load_config(),32,dt,2.,.001,'feedback')
        result['experiment_acceptance']='rejected: completion alone is insufficient; large strain and unresolved energy-work budget'
        data=np.genfromtxt(out/name/'diagnostics.csv',delimiter=',',names=True)
        result['strain_threshold_first_crossings_saved_s']={str(level):float(data['time_s'][np.where(data['max_shear_stretch_strain']>level)[0][0]]) for level in [.001,.01,.1] if np.any(data['max_shear_stretch_strain']>level)}
        summaries.append(result)
    except (ZeroDivisionError,FloatingPointError,ValueError):
        dest=out/name/'failure.json'
        if not dest.exists():raise
        summaries.append(json.loads(dest.read_text()))
    (out/'velocity_feedback_failure_study.json').write_text(json.dumps(summaries,indent=2))
