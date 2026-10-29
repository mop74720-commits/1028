"""Reproduce the entire new 3D experiment set. Existing matching runs may resume."""
from pathlib import Path
import argparse
import copy
import hashlib
import json
from model import load_config,run_case

ROOT=Path(__file__).resolve().parent


def study_cases():
    base=load_config(ROOT/'config_position_feedback.json')
    cases=[]
    def add(name,n=32,dt=1e-5,duration=2.,mode='feedback',cfg=None,sample=.005):
        cases.append(dict(name=name,n=n,dt=dt,duration=duration,mode=mode,cfg=copy.deepcopy(cfg or base),sample_dt=sample))
    add('position_feedback_n32_h10us')
    add('uncontrolled_n32_h10us',mode='uncontrolled',cfg=load_config())
    add('feedforward_n32_h10us',mode='feedforward',cfg=load_config())
    add('coil_allocated_n32_h10us',mode='coil_allocated')
    add('contact_stress_n32_h10us',mode='contact_stress')
    add('position_feedback_n16_h5us',n=16,dt=5e-6)
    add('position_feedback_n32_h5us',dt=5e-6)
    add('position_feedback_n64_h5us',n=64,dt=5e-6)
    add('position_feedback_n32_h2p5us',dt=2.5e-6)
    add('contact_stress_n16_h5us',n=16,dt=5e-6,mode='contact_stress')
    add('contact_stress_n32_h5us',n=32,dt=5e-6,mode='contact_stress')
    add('contact_stress_n64_h5us',n=64,dt=5e-6,mode='contact_stress')
    for density in [1200.,2400.]:
        c=copy.deepcopy(base);c['rod']['density_kg_m3']=density
        add(f'density_{int(density)}_n32_h10us',cfg=c)
    for gamma in [1.,4.]:
        c=copy.deepcopy(base);c['rod']['mass_proportional_damping_rate_s_inv']=gamma
        add(f'damping_{int(gamma)}_n32_h10us',cfg=c)
    add('excitation_n64_h10us',n=64,mode='excitation')
    for dt,label in [(1e-5,'10us'),(5e-6,'5us'),(2.5e-6,'2p5us')]:
        c=copy.deepcopy(base)
        c['flow']['enabled']=False;c['lumen']['enabled']=False;c['microgravity']['enabled']=False
        c['rod']['mass_proportional_damping_rate_s_inv']=0.
        c['rod']['initial_twist_rad']=.03
        add('conservative_twist_n32_h'+label,dt=dt,duration=.1,mode='conservative',cfg=c,sample=.0005)
    return cases


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT.parents[1]/'results'/'rod3d')
    p.add_argument('--resume',action='store_true');p.add_argument('--only',nargs='*');a=p.parse_args()
    summaries=[]
    model_hash=hashlib.sha256((ROOT/'model.py').read_bytes()).hexdigest()
    for case in study_cases():
        if a.only and case['name'] not in a.only:continue
        dest=a.output/case['name']
        if a.resume and (dest/'summary.json').exists() and (dest/'environment.json').exists():
            env=json.loads((dest/'environment.json').read_text())
            existing=json.loads((dest/'parameters.json').read_text())
            if env.get('model_sha256')==model_hash and existing==case['cfg']:
                summaries.append(json.loads((dest/'summary.json').read_text()))
                print('RESUME '+case['name'],flush=True);continue
        print('RUN '+case['name'],flush=True)
        try:
            summaries.append(run_case(output=a.output,**case))
        except (ZeroDivisionError,FloatingPointError,ValueError) as error:
            if not (dest/'failure.json').exists():raise
            summaries.append(json.loads((dest/'failure.json').read_text()))
            print('FAILED '+case['name']+': '+str(error),flush=True)
        (a.output/'study_progress.json').write_text(json.dumps(summaries,indent=2))
    (a.output/'study_summaries.json').write_text(json.dumps(summaries,indent=2))


if __name__=='__main__':main()
