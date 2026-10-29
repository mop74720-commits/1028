"""Scientific figures from completed JSON only (no new dynamics)."""
from pathlib import Path
import json
import os
os.environ.setdefault("MPLCONFIGDIR",str(Path(__file__).resolve().parents[3]/"stage2/results/route_a/matplotlib_cache"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/"stage2/results/route_a"
LABELS={"ordinary_midpoint_eq36":"Eq.36 / ordinary midpoint","canonical_chart_midpoint":"Point-chart midpoint",
        "canonical_chart_central4":"Point-chart Central4","weighted_chart_midpoint":"Valid weighted midpoint",
        "weighted_chart_gauss4":"Time-dependent chart Gauss4","frozen_current_weighted":"Frozen feedback current",
        "damping_split_midpoint":"Damping split / midpoint","gauss4_chart":"General ODE Gauss4",
        "matrix_chart_midpoint":"Known-linear Birkhoff chart"}
TITLES={"conservative":"Conservative variable-mass system","block_weighted":"Nonproportional block damping",
        "generic_nonproportional":"Generic cross-block damping / potential","linear_known_chart":"Known linear conjugacy"}

def main():
    plt.rcParams.update({"font.size":10,"axes.spines.top":False,"axes.spines.right":False})
    fig,axes=plt.subplots(2,2,figsize=(13,9),constrained_layout=True)
    for ax,family in zip(axes.ravel(),TITLES):
        d=json.loads((OUT/f"extended_{family}_16dof.json").read_text())
        for method,g in d["methods"].items():
            ax.loglog([r["h"] for r in g["rows"]],[r["maximum_grid_error"] for r in g["rows"]],"o-",ms=4,label=LABELS[method])
        ax.set(title=TITLES[family],xlabel="Step h",ylabel="Maximum state error on grid")
        ax.grid(True,which="both",alpha=.18);ax.legend(fontsize=8,loc="best")
    fig.suptitle("16 generalized coordinates (32 phase variables), T = 2; declared synthetic models",fontsize=14)
    fig.savefig(OUT/"route_a_16dof_convergence.png",dpi=180)
    fig.savefig(OUT/"route_a_16dof_convergence.pdf")
    plt.close(fig)
    d=json.loads((OUT/"transport_moser_results.json").read_text())
    fig,axes=plt.subplots(1,2,figsize=(11,4.4),constrained_layout=True)
    for c in d["cases"]:
        ts=[r["time_from_fixed_expansion_origin"] for r in c["rows"]]
        axes[0].loglog(ts,[r["representation_residual_2"] for r in c["rows"]],"o-",label=f"{c['n_coordinates']} coordinates")
        axes[1].semilogx(ts,[r["Moser_numerical_chart_congruence_spectral2"] for r in c["rows"]],"o-",label=f"{c['n_coordinates']} coordinates")
    axes[0].set(title="Representation residual of the ORIGINAL field",xlabel="t from fixed expansion origin",ylabel=r"$\|K_a f-\partial_t R_a-\nabla B_a\|_2$")
    axes[1].set(title="Chart congruence for the APPROXIMATE structure",xlabel="t from fixed expansion origin",ylabel=r"$\|D\chi^T K_0 D\chi-K_a\|_2$")
    for ax in axes:
        ax.set_xticks([.025,.05,.1,.2],["0.025","0.05","0.1","0.2"])
        ax.xaxis.set_minor_formatter(NullFormatter())
        ax.grid(True,alpha=.2);ax.legend()
    fig.suptitle("First transport truncation + numerical Moser chart: two independent errors",fontsize=13)
    fig.savefig(OUT/"route_a_moser_error_separation.png",dpi=180)
    fig.savefig(OUT/"route_a_moser_error_separation.pdf")
    plt.close(fig)

if __name__=="__main__": main()
