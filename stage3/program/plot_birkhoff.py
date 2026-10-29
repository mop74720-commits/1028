"""Plot saved, actually completed local experiments without rerunning them."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root=Path(__file__).resolve().parents[1]/'results/birkhoff'
data=json.loads((root/'results_T0.0005.json').read_text())
assert data['status']=='completed'
fig,ax=plt.subplots(1,2,figsize=(10,4),layout='constrained')
d=data['diagnostics']
ax[0].loglog([v['time'] for v in d],[v['representation_residual_2'] for v in d],'o-',label='Representation residual')
ax[0].loglog([v['time'] for v in d],[v['original_field_error_2'] for v in d],'s--',label='Field discrepancy')
ax[0].text(.03,.04,'Chart matching: zero to floating precision\nExterior derivative checked independently',transform=ax[0].transAxes,fontsize=8)
ax[0].set(xlabel='Time from fixed expansion origin',ylabel='Euclidean norm',title='Structure matching does not remove field error')
ax[0].legend(fontsize=8)
for method,color in [('original_midpoint','C0'),('birkhoff_chart_midpoint','C1')]:
    rows=[r for r in data['rows'] if r['method']==method]
    ax[1].loglog([r['h'] for r in rows],[r['error_to_original_max'] for r in rows],'o-',color=color,label=method+' vs original')
    if method.startswith('birkhoff'):
        ax[1].loglog([r['h'] for r in rows],[r['error_to_represented_max'] for r in rows],'s--',color=color,label='Chart vs represented field')
ax[1].set(xlabel='Step in dimensionless time',ylabel='Maximum 24D state error',title='Separate truncation and integration errors')
ax[1].legend(fontsize=7)
for a in ax:a.grid(True,alpha=.25)
fig.savefig(root/'error_separation.png',dpi=180)
fig.savefig(root/'error_separation.pdf')
