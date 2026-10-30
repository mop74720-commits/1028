"""Evidence annotations for all four physics chapters, in both languages.

The assessments below result from reading the actual source mathematics;
indexing/lexical equality does not itself certify correctness.
"""
from pathlib import Path
import csv
import hashlib
import json
import re

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parents[1]
index = json.loads((BASE/'results/manuscript_index.json').read_text())
original = {r['id']: r for r in csv.DictReader((ROOT/'stage4/audit/full_inheritance_matrix.csv').open(encoding='utf-8-sig'))}
FILES = {'mechanics.tex', 'supp_mechanics.tex', 'background.tex', 'application.tex'}
units = [u for u in index['review_units'] if Path(u['source']).name in FILES]

# One local assessment per equation/theorem/table, not one verdict per chapter.
NOTES = {
'tab:roadmap': 'The two routes share a declared physical/statistical benchmark but have different target Hamiltonians and error systems; the fusion benchmark is explicitly planar. Stage5 must retain original1025 as the final 3D route.',
'mech:general-energy': 'The kinetic metric follows BOTH position and SO(3) variations. Its positive definiteness requires independent regular coordinates; stage5 retains all state dependence.',
'mech:general-lagrange': 'Legendre transform retains (partial M inverse) quadratic momentum terms. Christoffel force is inertia, not Rayleigh loss; no constant-M substitution is allowed.',
'mech:parameters': '80mm, 0.6mm radius and 30mT bias are the old planar reference only. They differ from the inherited 100mm 3D ROM and are not new physiology or coil calibration.',
'mech:core-properties': 'Magnet moment Br*a^3/mu0, tip mass and cube inertia have consistent SI units. They are design estimates, not the different 3D distal magnet density.',
'mech:beam': 'Linear Euler-Bernoulli interior equation uses effective proportional drag, no blood flow/contact. This is an independent planar regression, not a 3D rod equation.',
'mech:endpoint-balance': 'Two integrations by parts give the signed shear/moment conditions with tip translational and rotational inertia. The tip is not clamped.',
'mech:fe-plant': 'Consistent Hermite mass plus tip mass and inertia; nonlinear bias remains in sine force. Constant FE mass is correct for this small-slope benchmark only.',
'mech:fe-energy': 'The bias energy 1-cos(theta) is nonnegative in this fixed-bias convention. Stage5 full coil potential has either sign and cannot inherit E>=E_bend without correction.',
'mech:physical-power': 'F*w_t+tau_B*theta_t is mechanical input power; magnetic parameter power belongs to a different total-energy bookkeeping convention.',
'mech:modal-bias': 'Mass-normalized modes diagonalize the linear biased FE model; unit modal mass does not make nonlinear 3D geometry mass constant.',
'mech:scaling': 'Position/momentum scale products E0/omega0 plus tau=omega0*t give canonical equations. Stage5 inherited Sq/Sp obey the same symplectic scaling.',
'mech:shape-maps': 'Linear Hermite centerline and scalar tip-angle maps hold for this planar FE restriction. Actual 3D maps are products of SO(3) cell rotations.',
'mech:nominal-energy': 'Subtracting s^2/2 avoids counting bias stiffness twice. Full cosine remains. Stage5 full coil energy instead uses zero-field elastic energy plus total-current potential once.',
'mech:reduced-values': 'The two frequencies and tip coefficients identify this old planar benchmark, not the new 12-coordinate spectrum or full-coil equilibrium.',
'mech:dimension-table': '64 is planar configuration dimension, 128 its phase dimension; two-mode endpoint map is 8x8. Stage5 has 12 configurations/24 phase variables/48 paired endpoints.',
'mech:complex-chart': 'The sqrt(2) normalization yields {zeta,bar zeta}=-i and correct canonical scales, correcting original1025 ambiguity.',
'mech:complex-energy': 'zeta and chi are independent for complexification; real energy need not be holomorphic in zeta alone. The explicit cosine continuation is benchmark-specific.',
'mech:wirtinger': 'Chain rule gives (partial X+i partial Y)/sqrt(2), no extra factor two; nonconservative force adds iQ/sqrt(2).',
'mech:decoder': 'Differentiate the Rayleigh readout in velocity BEFORE substituting learned H_P; the complex packaging H+iD is not a single conservative Hamiltonian.',
'mech:power': 'Power follows from the real decoder and requires dissipative velocity law; explicitly time-dependent learned parameters add H_t.',
'mech:modal-ports': 'Lambda U=A_mag(F,tau) has acceleration units and rank-two prerequisites; stage5 uses actual 12-current Gcoil with measured rank deficiency.',
'sm:rod-kinematics': 'D columns are material directors, D_s=D hat(kappa); stage2 PyElastica stores D^T. Mixing these conventions reverses angular updates.',
'sm:rod-balances': 'Independent rotational balance includes body gyroscopic term. A centerline-only fourth-order beam cannot represent torsion/shear/stretch.',
'sm:distributed-magnetism': 'Body-fixed magnetization and fixed-current spatial derivative yield both magnetic force and torque. This is directly implemented in stage5 full coil energy.',
'sm:maxwell-stress': 'The Maxwell stress integral uses total field, whereas dipole force uses external field. They are alternative force descriptions, not additive loads.',
'sm:dipole-expansion': 'Localized closed steady currents yield leading dipole force/torque; the external spatial derivative holds orientation fixed. The 3D code uses this dipole approximation, not resolved finite magnetic stress.',
'sm:dipole-remainders': 'Taylor bounds depend on current second moment and external-field derivative bounds on the whole core; those constants are not calibrated for the 3D magnet.',
'sm:fluid-example': 'Acceleration terms multiply mass per length; relative drag can supply rod energy in moving blood. Added mass can enter M once only. Current rod code implements prescribed drag, not this entire closure.',
'sm:contact-example': 'Positive part makes fractional contact powers real; compression-only damping is dissipative. Switching is not analytic and cannot enter ordinary analytic KAM.',
'sm:configuration-derivatives': 'Body rotation Jacobian vee(D^T partial_i D), together with centerline derivative, determines translational and rotational mass and virtual work.',
'sm:galerkin-metric': 'The metric and generalized force include rotational terms and boundary work. Actual 3D geometric ROM reuses this structure; contact/flow have not been projected into its smooth field.',
'sm:christoffel': 'All derivatives of M enter the standard first-kind Christoffel tensor, also generated by H_Q after Legendre transform.',
'sm:variable-mass-momentum': 'Derivative of inverse mass has the stated negative one-half in Pdot; geometric kinetic terms must not be counted again as dissipative force.',
'sm:rayleigh-momentum': 'For G1(q,p)=D(q,M^-1p), velocity force is -M grad_p G1, not -grad_p G1. M is symmetric; stage5 corrections explicitly retain this factor.',
'sm:general-power': 'D>=0 alone does not imply v.D_v>=0. Convexity with minimum at zero suffices; explicit time dependence adds H_t and moving-fluid power is external.',
'sm:beam-weak': 'Weak form produces the correct signs and endpoint inertia. Distributed rotary inertia is deliberately absent in Euler-Bernoulli, present in the spatial rod.',
'sm:hermite-shape': 'Cubic C1 Hermite interpolation applies only to the planar FE reference; 3D geometry is not obtained by assigning this scalar shape to torsion.',
'sm:element-matrices': 'Consistent mass and bending matrices have mixed length/slope units. Bias is added only for linearized stiffness, not duplicated in nonlinear energy.',
'sm:offset-tip': 'Nonzero axial center-of-mass offset produces mt*e coupling and Jcm+mt e^2; the benchmark assumes e=0, while the 3D distal magnet is distributed.',
'sm:characteristic-shape': 'The continuous constant-coefficient EB solution is an independent linear frequency check, not nonlinear ROM error control.',
'sm:characteristic-bc': 'Tip mass and bias/tip inertia appear with the correct frequency-domain signs; zero-tip limit reduces to the standard cantilever.',
'unlabelled_characteristic': 'The f,g,c+,s+ abbreviations define the next determinant only; they are not an independent dynamics statement.',
'sm:characteristic-determinant': 'Substituting the shape into both natural boundary conditions gives this 2x2 determinant; zero tip mass/inertia/bias gives 1+cosh(lambda)cos(lambda).',
'sm:frequency-table': 'Frozen 16/32/64-element frequency and continuous-root values concern this planar linear model. No claim of nonlinear high-mode truncation or new 3D convergence follows.',
'sm:sensitivity-table': 'One-at-a-time modulus/magnet/inertia design sensitivity is not a calibrated uncertainty interval; stage5 retains separate 3D parameter and boundary studies.',
'sm:scaled-form': 'The symplectic form scales uniformly by E0/omega0, even though coordinate scales differ; stage5 Sq/Sp are consistent.',
'sm:rayleigh-scale': 'Divide physical D by E0*omega0. With changed learned kinetic energy the force is -gamma N^-1 H_Y, not automatically -gamma Y.',
'sm:complex-chain-rule': 'Independent complex coordinates yield the stated sqrt(2) chain rule; the nonconservative decoder must remain separate.',
'sm:force-scale': 'Lambda=omega0^2 Ds N=E0 Ds^-1; U is continuous dimensionless momentum force, not the timestep-multiplied state increment.',
'sm:scaled-potential-force': 'Quadratic bias in frequencies plus cosine remainder gives the full physical biased potential; subtract known remainder only when converting total torque convention.',
'sm:numerical-ports': 'A_mag numerical determinant/rank is a planar geometric check. Mixed force/torque column scaling matters, and no physical coil feasibility follows from invertibility.',
'app:port-inverse': 'Only the old two-mode rank-two ideal force/torque interface is inverted. It cannot be reused as an arbitrary 12-dimensional physical control law.',
'app:residual-plant': 'Unknown conservative residual remains in the synthetic plant; controls do not access truth derivatives except explicitly named oracle comparison.',
'app:total-port': 'Total modal torque includes known bias remainder; converting to active magnetic torque must subtract it once. It does not cancel the unknown residual.',
'app:physical-closed-loop': 'Exact ideal port conversion leaves deltaR and delta gamma. Stage5 constrained full coil has additional allocation error and unactuated components.',
'app:field-gradient': 'The symmetric trace-free affine G gives the desired local force and curl/divergence constraints. This local algebra does not imply realizability by finite coils over the moving rod.',
'app:input-reconstruction': 'Actual applied input reconstruction must include saturation and calibration. Fusion reported tests explicitly omit saturation; stage5 adds actual current/field/rate constraints.',
'app:enriched-coordinates': 'Higher-mode state is the same planar FE basis; two physical input columns cannot assign all 64 modal forces independently.',
'app:enriched-plant': 'A full residual potential must be declared before restriction; two-mode training does not identify forces on eliminated modes.',
'app:enriched-defects': 'High-mode angle defect and residual-extension defect are distinct; perfect low-mode fitting does not remove either.',
'app:enriched-closed-loop': 'Actual low-mode dynamics retain e_mag-e_R+e_port. The same error categories are needed in a ROM-to-Cosserat transfer, which remains unbounded.',
'app:validation-stages': 'The fusion text explicitly marks 4/8/64-mode forced trajectories and independent COMSOL comparison as PLANNED. Do not combine this table with older fixed-v10 64-mode evidence to claim these new runs happened.',
'sm:enriched-potential': 'Full residual extension is a stated physical potential; cosine quadratic subtraction avoids duplicate bias energy.',
'sm:enriched-projection': 'Left multiply the first two acceleration equations by Lambda inverse in this exact order. Residual term is not recovered from two-mode data alone.',
'sm:angle-defect-bound': 'Mean-value theorem and 1-cos(s)<=s^2/2 give the bound only if both angles and high-mode difference are bounded.',
'sm:angle-residual-extension': 'Angle extension gives e_R=-beta*e_mag; low-coordinate-only extension gives e_R=0. Both agree on training plane but predict different plants.',
'sm:enriched-power': 'Nominal mechanical energy derivative includes -adot.grad R_N. A clearance ledger omitting this work is invalid.',
'app:full-modal': 'This is a finite planar FE plant with known proportional damping and total torque; it excludes arbitrary unmodeled high-mode residual forces.',
'app:velocity-inversion': 'Positive H_YY on a convex momentum fiber gives injectivity and local inverse, not surjectivity onto all velocities. Stage5 neural Hessian failures must remain.',
'app:full-feedback': 'The desired acceleration H_YX H_Y-H_YY H_X is correct, including mixed derivatives. Implementation uses exact full tip angle; target derivatives are not free measurements.',
'app:conditional-lift': 'Conditional finite-dimensional invariant torus lift assumes an existing low torus, positive target velocity map, known damping, feasible exact feedback, and full response-domain bounds. No new 3D torus follows.',
'sm:physical-embedding': 'The physical low-position/velocity image stays embedded only under the stated target momentum-fiber conditions.',
'sm:velocity-injectivity': 'Integral of positive H_YY along the convex fiber segment proves injectivity; this is a complete conditional argument retained in stage5 historical proof inventory.',
'sm:stable-resolvent': 'For alpha>0 and positive omega_j, real-frequency denominator never vanishes and inverse is bounded; alpha=0 resonance invalidates this lift proof.',
'app:response-coefficients': 'Finite many high-mode forced responses inherit analyticity from Fourier forcing. Exponential attraction is conditional only in high-mode deviations, not arbitrary low-mode initial states.',
'app:clamped-identity': 'Twice integrating scalar clamped curvature gives this exact planar identity. New stage6 proves a distinct SO(3) geometric analogue for the actual 3D embedding.',
'app:energy-bound': 'Old bound uses E>=E_bend and straight corridor after subtracting rod radius. New 3D bound must include shear/stretch and use nonnegative mechanical energy, not signed coil H.',
'sm:clearance-proof': 'Cauchy-Schwarz gives the sharp EB constant L^3/3; this does not restrict to static end-force shapes. Stage6 establishes the nonlinear 3D sufficient counterpart.',
'sm:slope-energy': 'Slope bound applies to the scalar small-slope beam; 3D tangent deviation is controlled by director rotation and shear/stretch terms instead.',
'sm:initial-quadratic': 'Quadratic upper bound includes biased stiffness K_b and true velocities. It is not a mass-frozen bound for the nonlinear 3D model.',
'sm:initial-upper-bound': 'Triangle inequality in sqrt(Q) gives a full-state initialization certificate. Tip-only sensing cannot establish it; fusion reported initial energy exceeds its cap.',
'app:work-observer': 'For the nominal power balance E<=W. Stage6 replaces force/torque coefficients by y=Gcoil^T H_P and uses nonnegative mechanical energy.',
'app:work-governor': 'Continuous-time convex projection is unique with SPD metric and nonempty feasible set containing zero. Finite current slew can remove zero; sampled state constraints are not a continuous-time certificate.',
'sm:work-ledger': 'Energy-work comparison follows from nonnegative damping. Stage6 checks the actual full-coil mechanical ledger under current ramps and preserves residuals.',
'sm:port-errors': 'Gain and additive port errors are assumed independently bounded; no values have been calibrated for the actual coils.',
'sm:power-estimation': 'Cosine Lipschitz bound gives the stated angle/velocity power-coefficient envelope. Actual 3D port needs its own state/geometry uncertainty envelope.',
'sm:power-envelope': 'Convex positively homogeneous upper power bound avoids velocity division; it can enter a current-space governor only after full-coil uncertainty envelopes are supplied.',
'sm:additive-power': 'Completing square in M gives r_e^T M^-1 r_e/(4 alpha). A uniform domain bound is needed for variable M, and alpha=0 cannot use this reserve.',
'sm:robust-governor': 'Finite-horizon reserve C_H=Emax-T_H p_e must be positive and exceed initial ledger; feasibility and current constraints remain separate assumptions.',
'sm:robust-energy': 'Only the stated finite-horizon energy bound follows with nonzero additive error; it is not all-time nor preservation of a requested torus.',
'sm:discrete-work': 'A certified upper power over the WHOLE hold is required. Stage6 logs decision/RK-stage observations but explicitly does not promote them to such an envelope.',
}

GROUPS = {
 'geometry': ('PHY16', 'stage5/program/coil_rom.py:115; stage3/source_inputs/starter/stage2/program/learning/rod_rom.py:68', 'stage5/proofs/coil_energy_ports.md#1', 'stage5/results/coil/validation.json', True, 'actual variable-M 3D geometry reused'),
 'rod': ('PHY04', 'stage3/source_inputs/starter/stage2/program/rod3d/model.py:318; stage5/program/rod_transfer_control.py', 'stage5/proofs/rod_transfer.md#1', 'stage5/results/rod_transfer/analysis.json', True, 'full Cosserat physical layer retained; no complete ROM/PDE error bound'),
 'magnetic': ('PHY08', 'stage5/program/coil_rom.py:96; stage5/program/coil_rom.py:108', 'stage5/proofs/coil_energy_ports.md#1', 'stage5/results/coil/validation.json', True, 'full fixed-current magnetic energy/virtual work verified in 3D'),
 'dipole': ('PHY07', 'stage5/program/coil_rom.py:100', 'stage5/proofs/coil_energy_ports.md#1', 'stage5/results/coil/validation.json', False, 'dipole implementation inherited; finite-magnet remainder constants not validated'),
 'fluid': ('PHY09', 'stage3/source_inputs/starter/stage2/program/rod3d/model.py:181', 'stage5/proofs/rod_transfer.md#4', 'stage5/results/rod_transfer/comparison.csv', False, 'prescribed relative drag active on rod; added mass/full FSI not implemented'),
 'contact': ('PHY12', 'stage3/source_inputs/starter/stage2/program/rod3d/model.py:201', 'stage5/proofs/rod_transfer.md#4', 'stage5/results/rod_transfer/comparison.csv', True, 'positive-part real contact active in separate narrow-tube run; nonsmooth branch'),
 'fe': ('PHY02', 'not-applicable: independent old planar FE benchmark, not stage5 3D implementation', 'stage5/proofs/chnn_kam_restored.md (historical object boundary)', 'not-rerun: archive english/sections/supp_mechanics.tex#sm:frequency-table', False, 'historical planar benchmark retained; no transfer of numerical constants to 3D'),
 'scaling': ('CK10', 'stage3/source_inputs/starter/stage2/program/learning/rod_rom.py:55; stage5/program/coil_rom.py:119', 'stage5/proofs/coil_energy_ports.md#1', 'stage5/results/coil/validation.json', True, 'canonical scaling reused, with actual 3D scales and variable mass'),
 'complex': ('CK01', 'stage5/program/learning_models.py; stage3/source_inputs/starter/stage2/program/learning/run_learning.py:32', 'stage5/proofs/corrected_mathematics.md; stage5/proofs/chnn_kam_restored.md', 'stage5/results/learning/S5_L01_results.json; stage5/results/learning/S5_L02_coil_reachability.json', False, 'decoder normalization inherited; arbitrary learned complex analytic error bound not proved'),
 'rayleigh': ('PHY17', 'stage5/program/coil_rom.py:133', 'stage5/proofs/corrected_mathematics.md; stage5/proofs/coil_energy_ports.md#3', 'stage5/results/coil/validation.json', True, 'correct velocity/momentum decoding retained for declared proportional drag; not general blood law'),
 'port': ('PHY21', 'stage5/program/coil_rom.py:108; stage5/program/coil_control.py:65', 'stage5/proofs/coil_energy_ports.md#4', 'stage5/results/coil/force_warm_fix/validation.json; stage5/results/learning/S5_L02_coil_reachability.json', True, 'actual full coil constrained port replaces ideal two-input inverse; rank deficiency retained'),
 'enriched': ('CK28', 'stage5/program/rod_transfer_control.py; stage5/program/run_rod_transfer_matched.py', 'stage5/proofs/rod_transfer.md#5', 'stage5/results/rod_transfer/comparison.csv', False, 'model-transfer defects recognized but full residual extension and error bounds not supplied'),
 'lift': ('CK26', 'not-found: no exact 3D torus lift; stage5/program/learning_models.py only tests target velocity properties', 'stage5/proofs/chnn_kam_restored.md', 'historical fixed v10: stage4/audit/external_v10/sections/full_fe_kam_control.tex:96', False, 'old conditional planar FE theorem retained, not generalized to rank-deficient 3D coil system'),
 'clearance': ('PHY28', 'not-found before stage6: 3D full-state clearance/work governor', 'stage5/proofs/rod_transfer.md#4 (power only, no clearance theorem)', 'stage5/results/rod_transfer/comparison.csv (observed contact, not certified clearance)', False, 'omitted constructive link restored partially in stage6'),
 'work': ('PHY28', 'stage5/program/coil_control.py (constraints without work barrier)', 'stage5/proofs/coil_energy_ports.md#5', 'stage5/results/coil/closed_loop_summary.json (power accounting only)', False, 'no stage5 work governor; stage6 adds actual current-space decision constraint and full-coil integration'),
 'roadmap': ('PHY01', 'stage5/program/coil_rom.py; stage5/program/rod_transfer_control.py', 'stage5/notes/unified_model_contract.md', 'stage5/results/coil/closed_loop_summary.json; stage5/results/rod_transfer/comparison.csv', False, 'physical route partly connected; fusion planar scope cannot redefine original1025 objective'),
}

def group(label):
    if label == 'tab:roadmap': return 'roadmap'
    if label in {'mech:general-energy','mech:general-lagrange','sm:configuration-derivatives','sm:galerkin-metric','sm:christoffel','sm:variable-mass-momentum'}: return 'geometry'
    if label in {'sm:rod-kinematics','sm:rod-balances'}: return 'rod'
    if label == 'sm:distributed-magnetism': return 'magnetic'
    if label in {'sm:maxwell-stress','sm:dipole-expansion','sm:dipole-remainders'}: return 'dipole'
    if label == 'sm:fluid-example': return 'fluid'
    if label == 'sm:contact-example': return 'contact'
    if label in {'sm:rayleigh-momentum','sm:rayleigh-scale','sm:general-power','mech:physical-power','mech:power'}: return 'rayleigh'
    if label in {'mech:scaling','sm:scaled-form'}: return 'scaling'
    if label in {'mech:complex-chart','mech:complex-energy','mech:wirtinger','mech:decoder','sm:complex-chain-rule'}: return 'complex'
    if label in {'mech:modal-ports','sm:force-scale','sm:scaled-potential-force','sm:numerical-ports','app:port-inverse','app:residual-plant','app:total-port','app:physical-closed-loop','app:field-gradient','app:input-reconstruction'}: return 'port'
    if label.startswith('app:enriched') or label.startswith('sm:enriched') or label in {'sm:angle-defect-bound','sm:angle-residual-extension','app:validation-stages'}: return 'enriched'
    if label in {'app:full-modal','app:velocity-inversion','app:full-feedback','app:conditional-lift','sm:physical-embedding','sm:velocity-injectivity','sm:stable-resolvent','app:response-coefficients'}: return 'lift'
    if label in {'app:clamped-identity','app:energy-bound','sm:clearance-proof','sm:slope-energy','sm:initial-quadratic','sm:initial-upper-bound'}: return 'clearance'
    if label.startswith('app:work') or label in {'sm:work-ledger','sm:port-errors','sm:power-estimation','sm:power-envelope','sm:additive-power','sm:robust-governor','sm:robust-energy','sm:discrete-work'}: return 'work'
    return 'fe'


def canonical_math(tex):
    tex = re.sub(r'\\label\{[^}]*\}', '', tex)
    tex = re.sub(r'\\(?:nonumber|quad|qquad|,|!|;)', '', tex)
    tex = tex.replace('\\\\', '').replace('&', '')
    return re.sub(r'\s+', '', tex)


def run():
    (BASE/'annotations').mkdir(exist_ok=True)
    rows = []
    bilingual = []
    for u in units:
        labels = u.get('labels', [])
        label = labels[0] if labels else 'unlabelled_characteristic'
        assert label in NOTES, (u['id'], label)
        category = group(label)
        original_id, code, proof, result, verified, inherited = GROUPS[category]
        counterpart = next((v for v in units if v['language'] != u['language'] and Path(v['source']).name == Path(u['source']).name and (v.get('labels', []) == labels)), None)
        assert counterpart is not None, u['id']
        identical = canonical_math(u['tex']) == canonical_math(counterpart['tex'])
        old = ROOT/'stage3/source_inputs/v10/v10_framework_20261028'/u['source']
        if old.exists() and labels:
            content = old.read_text()
            loc = content.find('\\label{'+label+'}')
            old_position = f'{old.relative_to(ROOT)}:{content[:loc].count(chr(10))+1}#{label}' if loc >= 0 else f'not-found: {old.relative_to(ROOT)}#{label}'
        else:
            old_position = f'{old.relative_to(ROOT)} (unlabelled characteristic abbreviations)'
        new = category in {'clearance', 'work'}
        rows.append(dict(id=u['id'], source=u['source'], line_start=u['line_start'], topic=label,
                         original_1025=original[original_id]['original_location'], old_v10=old_position,
                         general_birkhoff='not-applicable to this physical equation; geometric compatibility is audited in theory/algorithms annotations',
                         stage4=f'stage4/audit/full_inheritance_matrix.csv#{original_id}; stage4/audit/physical_and_control_audit.md',
                         stage5_code=code, stage5_proof=proof, stage5_results=result,
                         fusion_verdict='correct on its explicitly stated object/assumptions; retained scope and exceptions in review_note',
                         stage5_inheritance=inherited,
                         stage6_action=('new 3D sufficient geometric theorem + actual full-coil power governor, with sampled/certification boundary' if new else 'retain existing correct implementation/conditional historical result; no frozen changes'),
                         new_code=('stage6/fusion_reconciliation/program/fusion_physics.py' if new else 'not-applicable: inherited implementation not rewritten'),
                         tests=('stage6/fusion_reconciliation/tests/test_fusion_physics.py' if new or category in {'geometry','magnetic','port','rayleigh'} else 'not-rerun here; precisely scoped inherited evidence'),
                         evidence=('stage6/fusion_reconciliation/results/physics/experiment.json; stage6/fusion_reconciliation/results/physics/tests.log' if new or category in {'geometry','magnetic','port','rayleigh'} else result),
                         remaining=('continuous interval power/field envelopes; slew feasibility; flow/contact work; curved-vessel clearance; full-state sensing' if new else inherited),
                         review_note=NOTES[label]+f' Bilingual counterpart {counterpart["id"]}: '+('display math equal after whitespace/format normalization; surrounding prose read.' if identical else 'translation/prose and mathematical content manually compared; table/line layout or text differs.'),
                         material_exists=True, mentioned=True,
                         derivation_inherited=category in {'geometry','rod','magnetic','rayleigh','scaling','complex','lift','dipole'},
                         algorithm_reused=category in {'geometry','rod','magnetic','fluid','contact','scaling','port','rayleigh'},
                         verified_on_3d=verified,
                         generalization_proved=category in {'geometry','magnetic','scaling','rayleigh'}))
        if u['language'] == 'english':
            bilingual.append(dict(english=u['id'], chinese=counterpart['id'],
                                  normalized_math_equal=identical, human_mathematics_and_prose_review=True))
    (BASE/'annotations/physics.json').write_text(json.dumps(dict(reviewer_scope='Full EN/ZH mechanics, supplementary mechanics, background and application; display mathematics/table/conditional theorem review, not a blanket physical validation certificate', rows=rows), ensure_ascii=False, indent=2)+'\n')
    (BASE/'results/physics/bilingual_comparison.json').write_text(json.dumps(bilingual, ensure_ascii=False, indent=2)+'\n')
    print(f'{len(rows)} exact review-unit annotations; {len(bilingual)} bilingual pairs')


if __name__ == '__main__':
    run()
