"""Summarize measured outputs without recomputing or altering source data."""
from pathlib import Path
import csv
import hashlib
import json
import math

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/"stage2/results/route_a"
LATEST=ROOT/"stage2/sources/integration_latest/v10_birkhoff_20261028"
OLDER=ROOT/"stage2/sources/integration_older_copy2/v10_framework_20261028"
B=ROOT/"stage2/sources/birkhoff_supplied"

def flatten(x,prefix=""):
    if isinstance(x,dict):
        for k,v in x.items(): yield from flatten(v,prefix+"/"+str(k))
    elif isinstance(x,list):
        for k,v in enumerate(x): yield from flatten(v,prefix+"/"+str(k))
    elif isinstance(x,(int,float)) and not isinstance(x,bool):
        yield prefix,float(x)

def main():
    files=[("B_general",B/"verification_results.json",OUT/"supplied_replay/birkhoff_supplied/verification_results.json"),
           ("B_special",B/"v10_results.json",OUT/"supplied_replay/birkhoff_supplied/v10_results.json")]
    for d,names in [("framework_experiments",["matrix_structure_results","closed_loop_convergence_results","algebraic_defect_results","nonlinear_weighted_results"]),
                    ("general_birkhoff_experiments",["magnetic_method_comparison","synthetic_method_comparison"])]:
        for name in names:
            rel=Path("reproduction")/d/(name+".json")
            files.append((name,LATEST/rel,OUT/"supplied_replay"/rel))
    comparisons=[]
    for name,old,new in files:
        aa=dict(flatten(json.loads(old.read_text())));bb=dict(flatten(json.loads(new.read_text())))
        rows=[]
        for path,v in aa.items():
            if any(s in path.lower() for s in ["/cost/","seconds","/provenance/","build_seconds","processor"]): continue
            if path in bb: rows.append({"path":path,"supplied":v,"rerun":bb[path],"absolute_difference":abs(v-bb[path])})
        top=sorted(rows,key=lambda r:r["absolute_difference"],reverse=True)[:8]
        comparisons.append({"name":name,"compared_numeric_entries":len(rows),"maximum_absolute_difference":top[0]["absolute_difference"] if top else None,"largest_differences":top,
                            "excluded":"Wall times and environment/provenance, which are not repeatable numerical outputs."})
    version=[]
    for folder in ["reproduction/framework_experiments","reproduction/experiments","reproduction/general_birkhoff_experiments"]:
        for p in sorted((LATEST/folder).glob("*.py")):
            old=OLDER/p.relative_to(LATEST)
            version.append({"path":str(p.relative_to(LATEST)),"status":"unchanged" if old.exists() and old.read_bytes()==p.read_bytes() else "changed" if old.exists() else "added",
                            "latest_sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
    original_B=[{"file":p.name,"byte_identical_to_integrated_original":p.read_bytes()==(LATEST/"provenance/material_B_original"/p.name).read_bytes()} for p in sorted(B.iterdir()) if p.is_file()]
    audit={"numerical_replay_comparison":comparisons,"code_inheritance":version,"B_original_preservation":original_B,
           "read_only_source_preservation":json.loads((OUT/"supplied_replay_manifest.json").read_text())["source_unchanged"]}
    (OUT/"replay_and_inheritance_audit.json").write_text(json.dumps(audit,indent=2,ensure_ascii=False)+"\n")
    numeric=[];table=[]
    for p in sorted(OUT.glob("extended_*dof.json")):
        d=json.loads(p.read_text());family=d["parameters"]["family"];n=d["parameters"]["n_coordinates"]
        for method,group in d["methods"].items():
            for r in group["rows"]:
                diag=r["diagnostics"]
                row={"family":family,"n_coordinates":n,"method":method,"h":r["h"],"endpoint_error":r["endpoint_error"],"maximum_grid_error":r["maximum_grid_error"],"maximum_grid_order":r["maximum_grid_order"],
                     "K_defect":diag.get("max_K_defect_spectral2",diag.get("max_sampled_transport_K_defect_spectral2")),"K_metric_scope":diag["structure_scope"],
                     "cold_seconds":r["cost"]["median_cold_seconds"],"required_setup_seconds":r["cost"]["median_setup_seconds"],"warm_cached_seconds":r["cost"]["median_cached_seconds"]}
                numeric.append(row)
                if n==16 and r["h"]==.025: table.append(row)
    with (OUT/"extended_metrics.csv").open("w",newline="") as f:
        wr=csv.DictWriter(f,fieldnames=list(numeric[0]));wr.writeheader();wr.writerows(numeric)
    lines=["# 16自由度共同步长 h=0.025，T=2 的实测汇总","","一般跨块组的 K 缺陷是三个步骤样本最大值，其余为全步最大值；成本为三次中位数，冷启动含图构造。","",
           "| 模型 | 方法 | 全网格最大误差 | 观测阶 | K 缺陷 | 冷启动秒 | 构造秒 | 缓存推进秒 |",
           "|---|---|---:|---:|---:|---:|---:|---:|"]
    for r in table:
        lines.append(f"| {r['family']} | {r['method']} | {r['maximum_grid_error']:.6e} | {r['maximum_grid_order']:.6f} | {r['K_defect']:.6e} | {r['cold_seconds']:.6f} | {r['required_setup_seconds']:.6f} | {r['warm_cached_seconds']:.6f} |")
    (OUT/"summary_tables.md").write_text("\n".join(lines)+"\n")
    print(json.dumps({"replays": [{"name":c["name"],"entries":c["compared_numeric_entries"],"max_abs_difference":c["maximum_absolute_difference"]} for c in comparisons],"new_metric_rows":len(numeric)},ensure_ascii=False,indent=2))

if __name__=="__main__": main()
