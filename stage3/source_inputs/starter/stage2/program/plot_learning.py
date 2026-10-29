"""Plot frozen-model confirmation data without rerunning any fit."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
METRIC='canonical_z_gradient_and_tau_vector_field_relative_l2'


def main():
    out=ROOT/'results'/'figures';out.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9.5,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,2,figsize=(8,4.5),sharey=True)
    palette=['#64748B','#D08B37','#27658B','#7F4D84']
    records=[]
    for ax,group,title in zip(axes,['main','stress'],['Local amplitude 0.08','Stress amplitude 0.35']):
        d=json.loads((ROOT/'results'/'learning_confirmation'/group/'confirmation_summary.json').read_text())
        spd=json.loads((ROOT/'results'/'learning_spd'/'confirmation'/f'{group}_summary.json').read_text())
        for j,(label,key) in enumerate([('Quadratic','linear'),('48 features','analytic'),('Complex NN','complex'),('SPD complex','spd')]):
            for k,split in enumerate(['test','ood']):
                if key in ['linear','analytic']:values=[d['baselines'][split][key][METRIC]]
                elif key=='complex':values=[m['splits'][split][METRIC] for m in d['complex_checkpoints']]
                else:values=[spd['splits'][split][METRIC]]
                median=float(np.median(values))*100;lo=min(values)*100;hi=max(values)*100
                xpos=j+(-.18 if k==0 else .18)
                ax.bar(xpos,median,width=.31,color=palette[j],alpha=1. if k==0 else .42,
                       edgecolor=palette[j],hatch='' if k==0 else '//')
                if len(values)>1:ax.errorbar(xpos,median,yerr=[[median-lo],[hi-median]],fmt='none',ecolor='black',capsize=3,lw=1)
                records.append(dict(group=group,model=label,split=split,median_percent=median,seed_range_percent=[lo,hi]))
        ax.set_title(title,loc='left',fontweight='bold')
        ax.set_xticks(range(4),['Quadratic','48 fixed\nfeatures','Complex\nNN','SPD\ncomplex'])
        ax.set_yscale('log');ax.set_ylim(.8,200);ax.set_yticks([1,2,5,10,20,50,100,200],['1','2','5','10','20','50','100','200'])
        ax.grid(axis='y',which='major',alpha=.2);ax.set_axisbelow(True)
    axes[0].set_ylabel('Canonical vector-field relative L2 error (%)')
    from matplotlib.patches import Patch
    fig.legend(handles=[Patch(facecolor='#64748B',label='Independent test, 2048 states'),Patch(facecolor='#CBD5E1',edgecolor='#64748B',hatch='//',label='OOD, 1024 states')],
               loc='upper center',bbox_to_anchor=(.5,.88),ncol=2,frameon=False,fontsize=8.8)
    fig.suptitle('Frozen models on a new independent data seed',x=.08,y=.99,ha='left',fontsize=12,fontweight='bold')
    fig.text(.08,.025,'Complex NN: range of 3 seeds. SPD: 1 seed. Different capacities; no complex-vs-real advantage is inferred.',fontsize=8.1)
    fig.subplots_adjust(top=.76,bottom=.17,left=.09,right=.985,wspace=.10)
    fig.savefig(out/'learning_confirmation.png',dpi=200)
    fig.savefig(out/'learning_confirmation.pdf')
    (out/'learning_confirmation_plot_data.json').write_text(json.dumps(records,indent=2))


if __name__=='__main__':main()
