"""Preserve all 115 audited rows and append evidence-specific stage5 states.

Nothing is upgraded merely by importing this table.  Optional JSON updates
must target explicit IDs and appended fields; the 21 original columns remain
byte-for-value identical after CSV parsing.  See --help for the JSON contract.
"""
from __future__ import annotations
import argparse
import ast
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
STAGE=Path(__file__).resolve().parents[1]
BASE=ROOT/'stage4/audit/full_inheritance_matrix.csv'
ERRORS=ROOT/'stage4/audit/proof_errors_and_corrections.md'
SIX=('material_exists','mentioned_in_latest','full_derivation_inherited',
     'algorithm_reused','verified_on_3d','generalization_proved')
NEW=['stage5_status',*[f'stage5_{key}' for key in SIX],
     'stage5_source_code','stage5_proof','stage5_evidence','stage5_missing','stage5_next_action']
FUNCTIONS={
 'E01':'corrected_morison_transverse', 'E02':'contact_penalty;regularized_friction',
 'E03':'darboux_perpendicular', 'E04':'complex_coordinates;wirtinger_real_energy;complex_hamiltonian_rhs',
 'E05':'complex_energy_rate_squared;complex_hamiltonian_rhs',
 'E06':'gradient_integrability_defect;birkhoff_field',
 'E07':'endpoint_compatibility_defect;endpoint_gradient_jacobian;reconstruct_flow_jacobian',
 'E08':'central_generator_coefficients', 'E09':'fixed_endpoint_rhs;original_endpoint_matrix',
 'E10':'gradient_integrability_defect', 'E11':'midpoint_linear_mechanical_step;mechanical_field',
 'E12':'twoform_from_oneform_jacobian;twoform_evaluation',
 'E13':'birkhoff_field_from_negative_D;time_compatibility_defect',
 'E14':'transported_volume_ratio', 'E15':'torus_primitive_periods',
 'E16':'rayleigh_force_from_momentum_gradient',
}
CLASSIFICATIONS={
 'E01':'confirmed_error：量纲与相对流体速度项',
 'E02':'confirmed_error：非整数幂的非实活跃分支',
 'E03':'conditional_sign_error_and_model_reduction：需固定Darboux约定；中心线不能恢复独立扭转',
 'E04':'confirmed_normalization_inconsistency：部分双错抵消轨迹不能一概判错',
 'E05':'confirmed_omission_and_loss_inconsistency：守恒假设缺失',
 'E06':'confirmed_compatibility_error：候选混合偏导矛盾',
 'E07':'missing_hypotheses_and_overstrong_inverse：端点适配/横截必须补充，Hessian无需可逆',
 'E08':'confirmed_index_error_in_statement：原稿后附已有正确递推，予以恢复',
 'E09':'confirmed_chain_rule_error：分量/负号',
 'E10':'confirmed_sign_and_integrability_error：改符号仍不恢复梯度',
 'E11':'confirmed_matrix_order_error：第三阶段完整变质量残差已正确修复，继续复用',
 'E12':'confirmed_factor_inconsistency：闭性机制及原后附因子2观察仍有效',
 'E13':'confirmed_sign_inconsistency：原p1120时间相容式本身正确，予以保留',
 'E14':'overstrong_claim：时变结构体积并非欧氏体积',
 'E15':'incorrect_exact_symplectic_statement_and_missing_period_argument：辛体积结论不受影响',
 'E16':'confirmed_general_variable_mass_interpretation_error：旧补充材料正确公式恢复',
}
STATEMENTS={
 'E01':'f=ρAP⊥a_f+ρC_A AP⊥(a_f−a)+ρC_D D |P⊥(u−v)|P⊥(u−v)/2；各项为N/m。',
 'E02':'δ=(−g)_+；V_c=kδ^(a+1)/(a+1)；F_n=kδ^a∇g；相对切向摩擦功≤0。',
 'E03':'约定t_s=u×t时u_perp=t×t_s；独立材料标架与扭转/角动量不能从中心线恢复。',
 'E04':'ξ=(q+ip)/√2；∂_barξ=(∂q+i∂p)/√2；ξdot=−iH_barξ+iQ/√2。',
 'E05':'|d[√2(H+iP)]/dt|²=2(Hdot²+Pdot²)；损失和推进须用相同Wirtinger导数。',
 'E06':'K=Daᵀ−Da；Kf=∇B+a_t；必须先满足混合偏导和时间输运相容。',
 'E07':'E*d(hatw·dw)=Ω_t−Ω_s，CM+D可逆；N=(AM+B)(CM+D)^−1对称；完整联合逆重构，不要求N可逆。',
 'E08':'固定w下c_(r+1)=[τ^r]Ψ(g,w,Dg,s+τ;s)/(r+1)，含Ψ_N[D c_j]链式项。',
 'E09':'固定负端时hatwdot=(pdot_+,qdot_+)；wdot=(qdot_+/2,−pdot_+/2)；g_t=hatwdot−N wdot。',
 'E10':'P=−p_mid时阻尼候选(−Q+γP,−P)仍非梯度；改用合法相容图或明确拒收。',
 'E11':'E=h²K_sM^−1/4+hCM^−1/2；(I+E)p_+=(I−E)p_-−hK_sq_-+hF；变质量用完整未知中点残差。',
 'E12':'Ω=d(a·dz)=½Σ_ij K_ij dz_i∧dz_j；闭性与非退化分开。',
 'E13':'若D=−∇B−a_t则f=−K^−1D；K_t=Dbᵀ−Db，其中b=Kf。',
 'E14':'Φ*Ω_t=Ω_s及加权体积保持；detDΦ sqrt(|detK_t|)/sqrt(|detK_s|)=1。',
 'E15':'β=F*λ−I·dθ闭但可有周期2πI0；管域上F*λ=(I+I0)·dθ+dS，不能无条件称相对I·dθ恰当。',
 'E16':'G(q,p)=D(q,M^−1p)时Q_R=−Mᵀ∇pG；一般H_pp可逆时为−H_pp^−T∇pG。',
}
MISSING={
 'E01':'血管限域Morison标定、附加质量与真实载荷投影未由本恒等式测试完成',
 'E02':'柔性壁参数、严格接触/切换良定性与全杆验证需独立证据',
 'E03':'完整杆到Kirchhoff ROM的误差和伸长剪切影响仍待证明',
 'E04':'完整网络新训练与复域误差需要独立结果，复坐标修正不是KAM证书',
 'E05':'真实开放系统训练损失与控制链的采用状态等待统一结果',
 'E06':'实际一般三维场的相容输运构造及表示误差等待输运模块结果',
 'E07':'实际图端点匹配/横截范围和统一逆界等待图算法证据；24D代数测试不等于全域证明',
 'E08':'符号低维递推可运行；实际24D高阶生成和域/成本须分别验证',
 'E09':'实际时间图显式时间导数与闭环端点实现等待其他模块结果',
 'E10':'不相容候选已被拒绝；实际非比例场须先有合法图和标量生成函数',
 'E11':'常矩阵消元仅对应线性分支；真实变质量闭环由完整隐式残差验收',
 'E12':'闭性恒等式不保证全域非退化；实际图须给域/条件数证据',
 'E13':'实际闭环输运误差须独立测量；符号一致不等于原场表示准确',
 'E14':'仅已定义非退化局部流的加权体积结论；无任意耗散系统欧氏体积或KAM结论',
 'E15':'旧冻结TeX不改；论文采用修正并保留体积有效部分；没有新增三维KAM证书',
 'E16':'真实模型须使用物理速度耗散；一般学习Hpp反解和全域条件另证',
}
REPAIR_COLS=['id','original_location','audit_source','original_audit_record',
             'defect_classification','corrected_statement','correction_status',
             'proof','source_code','tests','execution_status','execution_evidence',
             'adopted_by_stage5_modules','remaining_or_missing','scope',
             *[f'stage5_{key}' for key in SIX]]

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def source_locations(rows, repairs):
    """Resolve actual stage5 Python anchors, rather than trusting prose labels."""
    located=[]; parsed={}
    for table,data,columns in (
        ('inheritance_update',rows,('stage5_source_code',)),
        ('repair_status',repairs,('source_code','tests')),
    ):
        for row in data:
            for column in columns:
                for filename,anchor in re.findall(
                    r'(stage5/[\w/.-]+\.py)(?:#([\w]+))?',row.get(column,'')):
                    path=ROOT/filename
                    if not path.exists():raise ValueError(f'{row["id"]}: missing code {filename}')
                    if filename not in parsed:
                        tree=ast.parse(path.read_text())
                        definitions={node.name:node.lineno for node in ast.walk(tree)
                                     if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
                        parsed[filename]=(definitions,sha(path))
                    definitions,code_sha=parsed[filename]
                    if anchor and anchor not in definitions:
                        raise ValueError(f'{row["id"]}: nonexistent code anchor {filename}#{anchor}')
                    located.append(dict(table=table,id=row['id'],column=column,
                        path=filename,anchor=anchor or None,
                        line=definitions[anchor] if anchor else 1,sha256=code_sha))
    return located

def build_repairs():
    report_path=STAGE/'results/corrected_identities/latest.json'
    report=json.loads(report_path.read_text()) if report_path.exists() else {'records':[]}
    records=report.get('records',[])
    rows=[]
    for line_number,line in enumerate(ERRORS.read_text().splitlines(),1):
        match=re.match(r'\| (E\d\d) \| ([^|]+) \|',line)
        if not match:continue
        eid=match[1]
        record=next((r for r in records if '.test_'+eid+'_' in r['test']),None)
        rows.append(dict(id=eid,original_location=match[2].strip(),
            audit_source=f'stage4/audit/proof_errors_and_corrections.md:{line_number}',
            original_audit_record=line,defect_classification=CLASSIFICATIONS[eid],
            corrected_statement=STATEMENTS[eid],
            correction_status='可执行修正与证明已落地；真实研究链采用状态待汇总',
            proof='stage5/proofs/corrected_mathematics.md',
            source_code='; '.join('stage5/program/corrected_identities.py#'+name
                                  for name in FUNCTIONS[eid].split(';')),
            tests='stage5/tests/test_corrected_identities.py#'+(
                record['test'].rsplit('.',1)[-1] if record else 'test_'+eid),
            execution_status=record['status'] if record else 'not_executed',
            execution_evidence='stage5/results/corrected_identities/latest.json' if record else '',
            adopted_by_stage5_modules='pending：不得以独立恒等式测试代替物理模块实际采用',
            remaining_or_missing=MISSING[eid],scope='本条数学修正的明确局部/条件范围；不升级全FSI/生理/KAM',
            stage5_material_exists='yes：源位置、共享实现、证明与测试',
            stage5_mentioned_in_latest='yes：本阶段修正证明',
            stage5_full_derivation_inherited='yes：修正所需推导完整恢复；外部定理适用假设明列',
            stage5_algorithm_reused='shared_function_implemented；物理模块采用待汇总',
            stage5_verified_on_3d='pending：独立物理/图模块的新证据；此处代数测试不等同完整三维实验',
            stage5_generalization_proved='conditional：见证明；不是全物理目标完成'))
    assert {r['id'] for r in rows}==set(FUNCTIONS)
    return rows

def apply_updates(rows, updates, allowed, id_key='id'):
    index={row[id_key]:row for row in rows}
    for row_id,fields in updates.items():
        if row_id not in index:raise ValueError(f'unknown row ID {row_id}')
        unknown=set(fields)-set(allowed)
        if unknown:raise ValueError(f'{row_id}: cannot update protected/unknown columns {sorted(unknown)}')
        if not all(isinstance(v,str) for v in fields.values()):
            raise ValueError('CSV updates require string values, preserving explicit evidence distinctions')
        for key in ('stage5_evidence','execution_evidence'):
            evidence=fields.get(key,'')
            for path in re.findall(r'stage5/[^\s;，；#（）]+',evidence):
                path=re.sub(r':\d+(?:-\d+)?$','',path).rstrip('.,')
                if not (ROOT/path).exists():raise ValueError(f'{row_id}: evidence file absent: {path}')
        index[row_id].update(fields)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--updates',action='append',default=[],help=
        'JSON {"inheritance":{"B01":{"stage5_status":"...",...}},"repairs":{"E01":{"correction_status":"...",...}}}. Repeated files apply in order.')
    args=parser.parse_args()
    with BASE.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f);old_fields=list(reader.fieldnames);old_rows=list(reader)
    if len(old_rows)!=115 or len(old_fields)!=21:raise ValueError('audited baseline dimensions changed')
    before=sha(BASE)
    rows=[{**row,**{key:'pending：等待本轮实际证据逐条汇总' for key in NEW}} for row in old_rows]
    repairs=build_repairs()
    input_updates=[]
    for filename in args.updates:
        path=Path(filename);update=json.loads(path.read_text())
        unknown=set(update)-{'inheritance','repairs','note'}
        if unknown:raise ValueError(f'unknown update sections: {unknown}')
        apply_updates(rows,update.get('inheritance',{}),NEW)
        apply_updates(repairs,update.get('repairs',{}),set(REPAIR_COLS)-{'id','original_location','audit_source','original_audit_record'})
        input_updates.append(dict(path=str(path),sha256=sha(path)))
    for old,new in zip(old_rows,rows):
        assert all(old[k]==new[k] for k in old_fields),'baseline fields must not be overwritten'
    locations=source_locations(rows,repairs)
    for name,columns,data in [('inheritance_update.csv',old_fields+NEW,rows),
                              ('repair_status.csv',REPAIR_COLS,repairs)]:
        with (STAGE/name).open('w',newline='',encoding='utf-8-sig') as f:
            writer=csv.DictWriter(f,fieldnames=columns);writer.writeheader();writer.writerows(data)
    assert before==sha(BASE)
    summary=dict(command=[sys.executable,*sys.argv],timestamp_utc=datetime.now(timezone.utc).isoformat(),
        audited_baseline='f3aa09c',baseline_file=str(BASE.relative_to(ROOT)),baseline_sha256=before,
        original_rows_preserved=len(rows),original_columns_preserved=old_fields,
        stage5_rows_updated=sum(row['stage5_status']!='pending：等待本轮实际证据逐条汇总' for row in rows),
        repair_rows=len(repairs),input_update_manifests=input_updates,
        validated_python_locations=len(locations),
        semantics='Row export is not research completion. Original 21 columns and six audited inheritance states remain unchanged.')
    logdir=STAGE/'results/ledgers';logdir.mkdir(parents=True,exist_ok=True)
    serialized=json.dumps(summary,ensure_ascii=False,indent=2)+'\n'
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    location_record=dict(timestamp_utc=summary['timestamp_utc'],
        command=summary['command'],locations=locations,
        scope='Actual file/function/test line positions at export; no inference of research completion.')
    (logdir/f'source_locations_{stamp}.json').write_text(
        json.dumps(location_record,ensure_ascii=False,indent=2)+'\n')
    (logdir/'source_locations_latest.json').write_text(
        json.dumps(location_record,ensure_ascii=False,indent=2)+'\n')
    (logdir/f'build_{stamp}.json').write_text(serialized)
    (logdir/'latest_build.json').write_text(serialized)
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
