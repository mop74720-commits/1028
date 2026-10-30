#!/usr/bin/env python3
"""Plot frozen Stage 5 evidence. Does not import or execute scientific solvers.

Run from any directory with a Python providing numpy and matplotlib. All inputs
are repository-relative frozen JSON/CSV. PDF is vector; PNG is a review preview.
Every plotted series is exported with source SHA-256, exact field and selection.
"""
from pathlib import Path
import csv
import hashlib
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

PAPER = Path(__file__).resolve().parents[1]
ROOT = PAPER.parents[1]
OUT = PAPER / "figures"
EVIDENCE = PAPER / "evidence"
SOURCES, SERIES, CLAIMS = {}, [], []
COLORS = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00"]
MARKERS = ["o", "s", "^", "D", "v"]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8,
    "axes.titlesize": 9, "axes.labelsize": 8, "legend.fontsize": 7,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "lines.linewidth": 1.35,
    "lines.markersize": 4, "axes.spines.top": False, "axes.spines.right": False,
    "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.dpi": 220})


def source(relative):
    relative = "stage5/results/" + relative
    path = ROOT / relative
    SOURCES[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    if path.suffix == ".csv":
        with path.open(newline="") as stream:
            return relative, list(csv.DictReader(stream))
    return relative, json.loads(path.read_text())


def record(fig, panel, name, path, field, selection, x, y, xunit, yunit,
           transform="none", xfield="see selection"):
    item = dict(figure=fig, panel=panel, series=name, source_path=path,
                source_sha256=SOURCES[path], fields=field, filter=selection,
                x_field=xfield, x_unit=xunit, y_unit=yunit, transform=transform,
                x=np.asarray(x).tolist(), y=np.asarray(y).tolist())
    SERIES.append(item)
    return np.asarray(x), np.asarray(y)


def claim(identifier, path, field, selection, value, unit, interpretation):
    CLAIMS.append(dict(claim_id=identifier, source_path=path,
        source_sha256=SOURCES[path], field=field, filter=selection,
        value=json.dumps(value), unit=unit, interpretation=interpretation))


def decorate(ax, xlabel=None, ylabel=None):
    ax.grid(True, which="major", alpha=.19, linewidth=.5)
    ax.set_axisbelow(True)
    if xlabel: ax.set_xlabel(xlabel)
    if ylabel: ax.set_ylabel(ylabel)


def steps(ax):
    ax.set_xscale("log", base=2)
    ax.set_xticks([4, 8, 16], ["4", "8", "16"])
    ax.set_xlim(3.6, 17.8)


def save(fig, name):
    fig.savefig(OUT / f"{name}.pdf", metadata={"Creator": "Frozen Stage 5 evidence plotting", "CreationDate": None, "ModDate": None})
    fig.savefig(OUT / f"{name}.png")
    plt.close(fig)


def transport():
    fig, axes = plt.subplots(2, 3, figsize=(7, 4.7), layout="constrained")
    for i, (model, label) in enumerate([("synthetic", "Synthetic load"),
                                      ("fullcoil_collocated", "Full-coil feedback")]):
        path, data = source(f"transport/{model}/inverse_verified.json")
        assert data["status"] == "completed" and data["metadata"]["high_order_ad_backend"] == "inverse"
        for order in data["orders"]:
            color, marker = COLORS[order-1], MARKERS[order-1]
            rr = [r for r in data["native_center"]["rows"] if r["order"] == order]
            rr.sort(key=lambda r:r["time"])
            x, y = record("transport", f"{i}a", f"r={order}", path,
                "native_center.rows[].native_time_jet_field_error_2",
                f"order == {order}; sorted time ascending; fixed cache center",
                [r["time"] for r in rr], [r["native_time_jet_field_error_2"] for r in rr],
                "dimensionless tau", "dimensionless canonical field 2-norm", xfield="native_center.rows[].time")
            axes[i, 0].loglog(x, y, color=color, marker=marker, label=f"r = {order}")
            rr = [r for r in data["rows"] if r["order"] == order]
            for field, ls, suffix in [("error_to_original_max", "-", "original field"),
                                     ("error_to_represented_max", "--", "represented field")]:
                x, y = record("transport", f"{i}b", f"r={order}, {suffix}", path, f"rows[].{field}",
                    f"order == {order}; steps 4,8,16", [r["steps"] for r in rr], [r[field] for r in rr],
                    "step count", "dimensionless canonical state 2-norm", xfield="rows[].steps")
                axes[i, 1].semilogy(x, y, color=color, marker=marker, ls=ls)
            gap = next(r["represented_original_reference_gap"] for r in data["model_gaps"] if r["order"] == order)
            x, y = record("transport", f"{i}b", f"r={order}, continuous representation gap", path,
                "model_gaps[].represented_original_reference_gap", f"order == {order}; constant across grid", [4,16], [gap,gap],
                "step count", "dimensionless canonical state 2-norm", transform="repeat scalar as horizontal reference")
            axes[i, 1].semilogy(x, y, color=color, ls=":", lw=1)
            for field, ls, suffix in [("seconds", "-", "grid total"), ("auxiliary_seconds", "--", "auxiliary chart")]:
                x, y = record("transport", f"{i}c", f"r={order}, {suffix}", path, f"rows[].{field}",
                    f"order == {order}", [r["steps"] for r in rr], [r[field] for r in rr], "step count", "wall seconds", xfield="rows[].steps")
                axes[i, 2].semilogy(x, y, color=color, marker=marker, ls=ls)
        axes[i, 0].set_title(f"({chr(97+3*i)}) {label}: time jet")
        axes[i, 1].set_title(f"({chr(98+3*i)}) Trajectory errors")
        axes[i, 2].set_title(f"({chr(99+3*i)}) Measured cost")
        axes[i, 0].legend(loc="best", frameon=False)
        axes[i, 0].set_xticks([6.25e-5, 1.25e-4, 2.5e-4, 5e-4], ["6.25", "12.5", "25", "50"])
        axes[i, 0].minorticks_off()
        decorate(axes[i, 0], r"Time parameter $\tau$ ($10^{-5}$)", r"$\|f_a-f\|_2$ at cache center")
        decorate(axes[i, 1], "Integration steps", "Maximum state error")
        decorate(axes[i, 2], "Integration steps", "Wall time (s)")
        steps(axes[i, 1]); steps(axes[i, 2])
        claim(f"transport_{model}_elapsed", path, "elapsed_seconds", "completed inverse_verified only", data["elapsed_seconds"], "s", "All coefficient, reference, and grid phases; shared-machine wall time, not speed ranking")
        for r in data["rows"]:
            if r["steps"] == 16:
                for field in ["error_to_original_max", "error_to_represented_max", "observed_order_to_represented", "max_residual_inf"]:
                    claim(f"transport_{model}_r{r['order']}_{field}", path, f"rows[].{field}", f"order={r['order']}; steps=16", r[field], "dimensionless", "Frozen accepted inverse_verified run")
    axes[0,1].legend(handles=[Line2D([],[],color=".2",ls="-",label="Original"),Line2D([],[],color=".2",ls="--",label="Represented"),Line2D([],[],color=".2",ls=":",label="Continuous gap")],frameon=False,loc="lower left")
    axes[0,2].legend(handles=[Line2D([],[],color=".2",ls="-",label="Whole grid"),Line2D([],[],color=".2",ls="--",label="Chart only")],frameon=False,loc="center left")
    save(fig, "transport")


def integrators():
    path, data = source("closed_loop/results.json")
    fig, axes = plt.subplots(2, 3, figsize=(7, 4.3), layout="constrained")
    labels = {"midpoint":"Midpoint", "central4":"Central4", "weighted_midpoint":"Weighted midpoint"}
    titles = ["Fixed current", "Proportional drag", "Collocated feedback"]
    for j, (branch, branch_data) in enumerate(data["branches"].items()):
        for i, (method, rr) in enumerate(branch_data["methods"].items()):
            for k, field in enumerate(["maximum_state_error", "maximum_sampled_weighted_defect_2" if branch == "proportional" else "maximum_sampled_canonical_defect_2"]):
                x, y = record("integrators", f"{k}{j}", labels[method], path,
                    f"branches.{branch}.methods.{method}[].{field}", "all frozen grids; branch-specific reference",
                    [r["steps"] for r in rr], [r[field] for r in rr], "step count", "dimensionless 2-norm", xfield="steps")
                axes[k,j].semilogy(x, y, color=COLORS[i], marker=MARKERS[i], ls=["-","--"][i], label=labels[method])
            for field in ["maximum_state_error", "observed_order", "maximum_sampled_canonical_defect_2", "maximum_sampled_weighted_defect_2", "maximum_increment_residual_inf"]:
                claim(f"integrator_{branch}_{method}_{field}", path,
                    f"branches.{branch}.methods.{method}[].{field}", "steps=16", rr[-1][field], "dimensionless", "T=0.0005 tau; independent reference for this branch")
        axes[0,j].set_title(f"({chr(97+j)}) {titles[j]}")
        axes[0,j].legend(frameon=False,loc="best")
        axes[1,j].set_title(f"({chr(100+j)}) " + ("Exponential-form defect" if branch=="proportional" else r"Canonical $K_0$ defect"))
        for k in [0,1]:
            steps(axes[k,j]); decorate(axes[k,j], "Integration steps", "Maximum state error" if k==0 else "Sampled two-form defect")
        axes[0,j].set_ylim(8e-14, 1e-7)
        axes[1,j].set_ylim(3e-16, 4e-3)
        claim(f"reference_{branch}", path, f"branches.{branch}.reference_refinement_max", "two DOP853 references", branch_data["reference_refinement_max"], "dimensionless canonical state norm", "Reference refinement difference")
    claim("closed_loop_elapsed", path, "elapsed_seconds", "15 method/grid combinations plus 6 references", data["elapsed_seconds"], "s", "Recorded wall time")
    claim("closed_loop_duration", path, "duration_seconds", "all branches", data["duration_seconds"], "s", "Physical time = tau/omega0")
    save(fig, "integrators")


def coil():
    path, data = source("coil/force_warm_fix/validation.json")
    rr = data["same_physical_q_spatial_quadrature"]
    fig, axes = plt.subplots(1,2,figsize=(7,2.8),layout="constrained")
    x,y = record("coil", "a", "Full versus affine force discrepancy", path,
        "same_physical_q_spatial_quadrature[].full_vs_affine_relative", "all rows; same physical q",
        [r["elements"] for r in rr], [100*r["full_vs_affine_relative"] for r in rr], "geometry elements", "%", "multiply relative discrepancy by 100", "same_physical_q_spatial_quadrature[].elements")
    axes[0].plot(x,y,color=COLORS[0],marker="o")
    axes[0].set_xticks(x); axes[0].set_ylim(0,105)
    axes[0].set_title("(a) Common-state force discrepancy")
    decorate(axes[0], "Geometry elements (20 / 40 / 80)", "Full versus affine relative error (%)")
    axes[0].text(.05,.2,"Magnetic quadrature points: 1 / 2 / 4",transform=axes[0].transAxes,fontsize=7)
    for i,r in enumerate(rr):
        sv=np.asarray(r["singular_values"])
        x,y=record("coil","b",f"{r['elements']} elements; rank {r['rank']}",path,
            "same_physical_q_spatial_quadrature[].singular_values",f"elements == {r['elements']}",list(range(1,13)),sv/sv[0],
            "singular-value index (1 based)","relative singular value", "divide each singular value by first")
        axes[1].semilogy(x,y,color=COLORS[i],marker=MARKERS[i],ls=["-","--","-."][i],label=f"{r['elements']} elements; rank {r['rank']}")
    threshold=rr[0]["rank_rcond"]
    record("coil","b","rank threshold",path,"same_physical_q_spatial_quadrature[].rank_rcond","elements=20; all rows share threshold",[1,12],[threshold,threshold],"singular-value index","relative singular value","repeat scalar as horizontal threshold")
    axes[1].axhline(threshold,color=".35",ls=":",lw=1)
    axes[1].text(7.1,threshold*2,"Rank threshold",fontsize=7,color=".3")
    axes[1].set_xticks([1,3,5,7,9,12]); axes[1].legend(frameon=False,loc="lower left")
    axes[1].set_title("(b) Full-coil generalized-force port")
    decorate(axes[1],"Singular-value index",r"$\sigma_j/\sigma_1$")
    save(fig,"coil")


def learning():
    path, rows = source("learning/S5_L01_metrics.csv")
    kinds=["analytic_mechanical4","complex_hidden","spd_complex"]
    labels=["Mechanical\ndictionary", "Complex\nnetwork", "SPD complex\nnetwork"]
    fig,axes=plt.subplots(1,2,figsize=(7,2.9),layout="constrained")
    for i,split in enumerate(["test","OOD"]):
        for j,kind in enumerate(kinds):
            rr=sorted([r for r in rows if r["kind"]==kind and r["split"]==split],key=lambda r:int(r["seed"]))
            xpos=j+(-.15 if i==0 else .15)+np.array([-.035,0,.035])
            for k,field in enumerate(["canonical_field_relative_l2","Hpp_nonpositive_count"]):
                yy=[float(r[field])*(100 if k==0 else 1) for r in rr]
                x,y=record("learning",["a","b"][k],f"{kind}, {split}, three seeds",path,field,
                    f"kind={kind}; split={split}; seeds ascending 51001,51002,51003",xpos,yy,"model category + display offset","%" if k==0 else "nonpositive Hpp samples out of 8",
                    "multiply by 100; x offsets distinguish split and seed" if k==0 else "x offsets distinguish split and seed","kind/seed/split")
                axes[k].scatter(x,y,c=COLORS[i],marker=MARKERS[i],s=26,label=split if j==0 else None,zorder=3)
        for k in [0,1]:
            axes[k].set_xticks(range(3),labels); axes[k].set_xlim(-.5,2.5); axes[k].legend(frameon=False)
    axes[0].set_title("(a) Independent canonical-field error")
    axes[1].set_title(r"(b) Nonpositive $h_{PP}$")
    axes[1].set_yticks(range(0,9,2));axes[1].set_ylim(-.4,8.4)
    decorate(axes[0],None,"Relative field error (%)")
    decorate(axes[1],None,"Count among 8 fixed states per seed")
    save(fig,"learning")


def resonance():
    path,data=source("resonance/S5_R02_results.json")
    fig,axes=plt.subplots(1,2,figsize=(7,2.9),layout="constrained")
    fields=["raw_H4_real","cubic_correction_real","corrected_H4_real"]
    coeff=data["coefficient_of_xi0_squared_chi1_squared"]
    vals=[coeff[f] for f in fields]
    x,y=record("resonance","a","quartic coefficient cancellation",path,
        ";".join("coefficient_of_xi0_squared_chi1_squared."+f for f in fields),"powers=2,0,0,2; accepted reverse-AD calculation",
        [0,1,2],vals,"coefficient contribution","dimensionless normal-form coefficient")
    axes[0].bar(x,y,color=COLORS[:3],width=.55)
    axes[0].set_yscale("symlog",linthresh=.01,linscale=.7)
    axes[0].set_xticks(x,[r"Raw $h_4$", "Cubic bracket", "Corrected"])
    for xx,yy in zip(x,y):
        axes[0].annotate(f"{yy:.6g}",(xx,yy),xytext=(0,5 if yy>0 or yy < -1 else -12),textcoords="offset points",ha="center",fontsize=7,color="white" if yy < -1 else "black")
    axes[0].set_ylim(-2500,2500);axes[0].axhline(0,color=".4",lw=.6)
    axes[0].set_title(r"(a) Resonant $\xi_0^2\chi_1^2$ coefficient")
    decorate(axes[0],None,"Signed coefficient (symlog scale)")
    rr=data["cross_mode_cubic_correction"]
    x,y=record("resonance","b","all canonical bracket channels",path,
        "cross_mode_cubic_correction[].xi0_squared_chi1_squared_correction_real","all 12 modes, including zero contributions",
        [r["mode"]+1 for r in rr],[r["xi0_squared_chi1_squared_correction_real"] for r in rr],"mode index (1 based)","dimensionless normal-form coefficient","add 1 to stored mode index", "cross_mode_cubic_correction[].mode")
    axes[1].bar(x,y,color=COLORS[1],width=.65);axes[1].set_xticks(range(1,13))
    axes[1].set_title("(b) Cross-mode cubic contributions")
    decorate(axes[1],"Canonical bracket channel","Contribution to selected coefficient")
    save(fig,"resonance")


def rod():
    path,rows=source("rod_transfer/comparison.csv")
    rpath,ref=source("rod_transfer/refinement.json")
    fig=plt.figure(figsize=(7,3.0),layout="constrained")
    grid=fig.add_gridspec(1,3,width_ratios=[1.45,1,1])
    axes=[fig.add_subplot(grid[0,i]) for i in range(3)]
    labels=["Nominal 32 / 10", "Port 16 / 5", "Port 32 / 10", "Port 32 / 5", "Port 32 / 2.5", "Port 64 / 5", "Contact 32 / 5"]
    x,y=record("rod","a","seven final cases",path,"tip_rmse_m","all rows, original CSV order; final repaired allocator",
        list(range(len(rows))),[float(r["tip_rmse_m"])*1e3 for r in rows],"case index","mm","multiply m by 1000","case")
    axes[0].barh(x,y,color=[COLORS[0]]+[COLORS[1]]*5+[COLORS[3]])
    axes[0].set_yticks(x,labels);axes[0].invert_yaxis();axes[0].set_xlim(0,.47)
    for xx,yy in zip(x,y):axes[0].text(yy+.005,xx,f"{yy:.4f}",va="center",fontsize=6.5)
    axes[0].set_title("(a) 0.2 s tip tracking")
    decorate(axes[0],"3D tip RMSE (mm)",None)
    for j,inds in enumerate([[0,1],[2,3]],start=1):
        rr=[ref["pairs"][i] for i in inds]
        scale=1e6 if j==1 else 1e9
        x,y=record("rod",chr(97+j),"spatial refinement" if j==1 else "temporal refinement",rpath,
            "pairs[].centerline_time_space_rms_m",f"pair indices {inds}; same reference arclength; adjacent solutions",
            [0,1],[r["centerline_time_space_rms_m"]*scale for r in rr],"adjacent refinement pair","um" if j==1 else "nm",f"multiply m by {scale:g}","pairs[].first/second")
        axes[j].plot(x,y,color=COLORS[j],marker=MARKERS[j])
        axes[j].set_xticks(x,["16–32","32–64"] if j==1 else ["10–5","5–2.5"])
        axes[j].set_xlim(-.2,1.2);axes[j].set_ylim(0,4.2)
        order=ref["observed_space_order" if j==1 else "observed_time_order"]
        axes[j].text(.07,.88,f"Observed p = {order:.3f}",transform=axes[j].transAxes,fontsize=7)
        axes[j].set_title(f"({chr(97+j)}) "+("Space refinement" if j==1 else "Time refinement"))
        decorate(axes[j],"Elements (Δt = 5 µs)" if j==1 else "Step sizes (µs; n = 32)","Centerline RMS difference (µm)" if j==1 else "Centerline RMS difference (nm)")
    save(fig,"rod")


def protocol_claims():
    for model in ["synthetic", "fullcoil_collocated"]:
        path,data=source(f"transport/{model}/inverse_verified.json")
        for key in ["duration_tau", "solver_tolerance"]:
            claim(f"{model}_{key}",path,key,"accepted inverse_verified",data[key],"dimensionless","Frozen numerical budget")
        claim(f"{model}_spatial_cache",path,"cache.spatial_degree","coefficient order ascending",data["cache"]["spatial_degree"],"polynomial degree","Only one-form coefficients are spatially cached")
        for r in data["native_center"]["rows"]:
            if r["time"] == data["duration_tau"]:
                claim(f"{model}_r{r['order']}_center_field",path,"native_center.rows[].native_time_jet_field_error_2",f"order={r['order']}; time=duration_tau",r["native_time_jet_field_error_2"],"dimensionless canonical field norm","Native time-jet error at cache center")
        for r in data["model_gaps"]:
            claim(f"{model}_r{r['order']}_continuous_gap",path,"model_gaps[].represented_original_reference_gap",f"order={r['order']}",r["represented_original_reference_gap"],"dimensionless canonical state norm","Maximum over 65 shared reference times")
        for key in ["rtol", "atol", "max_step"]:
            claim(f"{model}_represented_reference_{key}",path,f"represented_references[].{key}","order=1; coarse then fine",[r[key] for r in data["represented_references"] if r["order"]==1],"dimensionless","Same settings at all transport orders")
        for key in ["seconds", "auxiliary_seconds"]:
            vals=[r[key] for r in data["rows"]]
            claim(f"{model}_grid_{key}_range",path,f"rows[].{key}","all orders and steps; min,max",[min(vals),max(vals)],"s","Range of per-grid measured wall time")
    path,data=source("closed_loop/results.json")
    for key in ["initial_state_amplitude","duration_tau","solver_increment_tolerance","step_counts"]:
        claim(f"direct_{key}",path,key,"all branches",data[key],"dimensionless","Shared initial/grid/solver protocol")
    for key in ["q_dof","phase_dimension","quadrature_elements","E0_J","omega0_rad_s"]:
        claim(f"model_{key}",path,f"model.{key}","full-coil ROM",data["model"][key],"J" if key=="E0_J" else "s^-1" if key=="omega0_rad_s" else "count","Model and unit definition")
    for key in ["quadrature_points"]:
        claim(f"coil_{key}",path,f"model.coil_config.{key}","each of 12 coils",data["model"]["coil_config"][key],"points","Wire quadrature budget")
    for key in ["rtol","atol","max_step"]:
        claim(f"direct_reference_{key}",path,f"branches.conservative.references[].{key}","coarse then fine; same settings for all branches",[r[key] for r in data["branches"]["conservative"]["references"]],"dimensionless","Independent branch-specific DOP853 references")
    path,data=source("transport/inverse_verified_reference_bridge.json")
    for key,unit in [("maximum_bias_change_A","A"),("maximum_new_old_reference_state_difference_2","dimensionless canonical state norm")]:
        claim(key,path,key,"current numeric kernel versus shared prior reference",data[key],unit,"Quantified rounding bridge, not bitwise identity")
    path,data=source("transport/inverse_verified_jsonfixed_domains.json")
    failures=[dict(model=r["model"],order=r["order"],time=r["time"]) for r in data["probes"] if r["status"]=="failed"]
    claim("chart_domain_failures",path,"probes[].model,order,time,status","status=failed",failures,"dimensionless tau","Four actual auxiliary paths left declared radius 0.002")
    claim("chart_probe_counts",path,"probes[].status","all rows; time-parameter probes versus explicit outside-ball tests",[sum(r["status"]!="expected_domain_rejection" for r in data["probes"]),sum(r["status"]=="expected_domain_rejection" for r in data["probes"])],"count","25 time-parameter probes plus 2 expected outside-ball rejections")
    claim("chart_declared_radius",path,"probes[].diagnostics.chi.uniform_ball_sufficient_bounds.radius","first successful probe",data["probes"][0]["diagnostics"]["chi"]["uniform_ball_sufficient_bounds"]["radius"],"dimensionless canonical state norm","Declared Euclidean ball; floating-point sufficient bounds")


def write_evidence():
    exclusions=[]
    for relative,reason in [
        ("transport/synthetic/main.json","Rejected nested forward/reverse solve high-derivative evidence; not plotted"),
        ("transport/fullcoil_collocated/main_adfixed.json","Pre-inverse-verification high-derivative run; not accepted or plotted"),
        ("transport/legacy_status.json","Authoritative legacy status retained; not a plotted accepted result"),
        ("resonance/S5_R02_forward_ad_failed_results.json","Rejected forward-AD quartic calculation; not plotted"),
        ("learning/S5_L02_pre_warmfix_coil_reachability.json","Pre-warmfix allocation failures retained; not plotted as current results"),
        ("rod_transfer/initial_allocator_failure/refinement.json","Pre-repair allocator refinement retained; not plotted as final results")]:
        file=ROOT/"stage5/results"/relative
        if file.exists():
            exclusions.append(dict(source_path=str(file.relative_to(ROOT)),source_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),reason=reason))
    evidence=dict(schema_version=1,base_commit="1c73a580441200d6594e2a2a96374edc1c0e98e6",
        scope="Plot-only reproduction from existing frozen data; no scientific solver or training invoked",
        coordinate_convention="Canonical state/field norms dimensionless unless explicitly marked SI; time tau=omega0*t_seconds",
        sources=SOURCES, excluded_or_historical_sources=exclusions,series=SERIES)
    (EVIDENCE/"plotted_data.json").write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+"\n")
    keys=["figure","panel","series","source_path","source_sha256","fields","filter","x_field","x_unit","y_unit","transform"]
    with (EVIDENCE/"figure_sources.csv").open("w",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=keys);writer.writeheader()
        writer.writerows({k:r[k] for k in keys} for r in SERIES)
    keys=list(CLAIMS[0])
    with (EVIDENCE/"numerical_claims.csv").open("w",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=keys);writer.writeheader();writer.writerows(CLAIMS)


if __name__ == "__main__":
    OUT.mkdir(parents=True,exist_ok=True);EVIDENCE.mkdir(parents=True,exist_ok=True)
    transport();integrators();coil();learning();resonance();rod();protocol_claims();write_evidence()
    print(f"Built six vector PDFs, six previews, and {len(SERIES)} traced series; no scientific runs.")
