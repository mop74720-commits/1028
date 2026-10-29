"""Plot only newly generated integrator records; never regenerate experiments."""
from pathlib import Path
import json
import os
os.environ.setdefault('MPLBACKEND','Agg')
os.environ.setdefault('MPLCONFIGDIR','/tmp/stage3-matplotlib')
import matplotlib.pyplot as plt

root=Path(__file__).resolve().parents[1]/'results/integrators'
data=json.loads((root/'integrators.json').read_text())
if data.get('status')!='all convergence, residual, reference and applicable structure assertions passed':
    raise RuntimeError('Full integrator experiment has not passed')
fig,axes=plt.subplots(1,2,figsize=(10,4.2),layout='constrained')
for ax,branch in zip(axes,['conservative','damped']):
    for method,rows in data['branches'][branch]['methods'].items():
        ax.loglog([r['step'] for r in rows],[r['maximum_state_error'] for r in rows],
                  'o-',label=f"{method.replace('_',' ')} (p={rows[-1]['observed_order']:.3f})")
    ax.set(title=branch.capitalize(),xlabel='Dimensionless time step',ylabel='Maximum 24D state error')
    ax.grid(True,which='both',alpha=.25)
    ax.legend(fontsize=9)
fig.suptitle('Actual 12-coordinate variable-mass 3D rod ROM; T = 0.004')
for extension in ['png','pdf']:
    fig.savefig(root/f'integrators_convergence.{extension}',dpi=180)
plt.close(fig)
