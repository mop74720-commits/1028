"""Cross-check four independently generated 12-DOF feedforwards on 3D rods."""
from pathlib import Path
import argparse
import hashlib
import json
from model import run_case,load_config,MODEL_SHA256

ROOT=Path(__file__).resolve().parent
out=ROOT.parents[1]/'results'/'rod3d'
parser=argparse.ArgumentParser()
parser.add_argument('--resume',action='store_true')
parser.add_argument('--elements',nargs='*',type=int,default=[32,64])
args=parser.parse_args()
summaries=[]
for n in args.elements:
    for variant in ['linear','analytic','complex','truth']:
        cfg=load_config(ROOT/'config_position_feedback.json')
        cfg['controller']['feedforward_npz']='../../results/learning/feedforward/'+variant+'.npz'
        file=ROOT/cfg['controller']['feedforward_npz']
        name=f'learned_{variant}_n{n}_h'+('10us' if n==32 else '5us')
        dest=out/name
        if args.resume and (dest/'summary.json').exists():
            env=json.loads((dest/'environment.json').read_text())
            if env['model_sha256']==MODEL_SHA256 and env.get('feedforward_npz_sha256')==hashlib.sha256(file.read_bytes()).hexdigest():
                summaries.append(json.loads((dest/'summary.json').read_text()))
                continue
        try:
            summaries.append(run_case(name,out,cfg,n,1e-5 if n==32 else 5e-6,2.,.005,'feedback'))
        except (ZeroDivisionError,FloatingPointError,ValueError):
            if not (dest/'failure.json').exists():raise
            summaries.append(json.loads((dest/'failure.json').read_text()))
        (out/'learning_comparison_progress.json').write_text(json.dumps(summaries,indent=2))
(out/'learning_comparison_summaries.json').write_text(json.dumps(summaries,indent=2))
