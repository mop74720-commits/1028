"""Formula and protected-translation checks for the Direction-I framework.

Default: exact-polynomial algebra, the new magnetic Central4 derivatives, and
source-label checks for all five English theory files.  Translation is pending
unless --check-translation is explicitly supplied after the English freeze.

With --check-translation, compare every display/inline math block literally
(after TeX comments and line-ending normalization), label/reference/citation
commands, and begin/end environment order in the five EN/ZH file pairs.
Whitespace-insensitive math equality is also reported, but does not relax the
literal check. This does not certify translation of prose or a KAM threshold.

Usage:
  python3 reviews/structure_formula_checks.py
  python3 reviews/structure_formula_checks.py --check-translation
"""
from fractions import Fraction as F
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import itertools
import json
import re
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
THEORY_FILES = (
    'structure.tex', 'controlled_analysis.tex', 'kam.tex',
    'supp_structure.tex', 'extension_tracking_theory.tex',
)
EXPECTED_LABELS = {
    'structure.tex': ('struct:endpoint-proposition', 'struct:lifted-generator',
                      'struct:matrix-elimination', 'struct:route-a-control'),
    'controlled_analysis.tex': ('ctrl:midpoint', 'ctrl:weighted-midpoint',
                                'ctrl:convergence', 'ctrl:global-error'),
    'kam.tex': ('kam:closed-budget', 'kam:map-theorem', 'kam:map-smallness'),
    'supp_structure.tex': ('ss:projection', 'ss:inexact-solve',
                           'ss:central4-magnetic', 'ss:map-kam'),
    'extension_tracking_theory.tex': ('struct:route-b-control',
        'struct:route-b-error', 'struct:route-b-oracle', 'ss:tracking',
        'kam:route-budgets', 'kam:flow-theorem'),
}

class P:
    def __init__(self, terms=0):
        self.c = ({k: F(v) for k, v in terms.items() if v}
                  if isinstance(terms, dict)
                  else ({(0, 0, 0, 0): F(terms)} if terms else {}))

    def __add__(self, other):
        other = other if isinstance(other, P) else P(other)
        c = self.c.copy()
        for k, v in other.c.items():
            c[k] = c.get(k, F(0)) + v
        return P(c)

    __radd__ = __add__

    def __neg__(self):
        return P({k: -v for k, v in self.c.items()})

    def __sub__(self, other):
        return self + (-other if isinstance(other, P) else -P(other))

    def __mul__(self, other):
        other = other if isinstance(other, P) else P(other)
        c = {}
        for a, va in self.c.items():
            for b, vb in other.c.items():
                k = tuple(x + y for x, y in zip(a, b))
                c[k] = c.get(k, F(0)) + va * vb
        return P(c)

    __rmul__ = __mul__

    def __pow__(self, n):
        ans = P(1)
        for _ in range(n):
            ans = ans * self
        return ans

    def diff(self, i):
        c = {}
        for k, v in self.c.items():
            if k[i]:
                power = list(k)
                power[i] -= 1
                c[tuple(power)] = v * k[i]
        return P(c)


def jmul(v):
    return [v[2], v[3], -v[0], -v[1]]


def matvec(a, v):
    return [sum((aij * vj for aij, vj in zip(row, v)), P()) for row in a]


def algebra_checks(root):
    x = [P({tuple(int(i == j) for j in range(4)): 1}) for i in range(4)]
    x1, x2, y1, y2 = x
    h = (F(1, 2) * (x1**2 + 2*x2**2 + y1**2 + 2*y2**2)
         + F(1, 7)*x1**2*x2 + F(2, 9)*x1*y1*y2
         + F(1, 11)*(x1+x2)**4)
    grad = [h.diff(i) for i in range(4)]
    a = [[h.diff(i).diff(j) for j in range(4)] for i in range(4)]
    f = jmul(grad)
    df = [[f[i].diff(j) for j in range(4)] for i in range(4)]
    q = sum((f[i]*a[i][j]*f[j] for i in range(4) for j in range(4)), P())
    left = jmul([q.diff(i) for i in range(4)])
    ff = [sum((f[i].diff(j).diff(k)*f[j]*f[k]
               for j in range(4) for k in range(4)), P()) for i in range(4)]
    dfdf = matvec(df, matvec(df, f))
    identity = [not (left[i] - (ff[i] - 2*dfdf[i])).c for i in range(4)]
    assert all(identity)

    t = x1
    z = F(1, 2)*(t+F(1, 12)*t**3)
    phase = 2*(z-F(1, 3)*z**3+F(1, 5)*z**5)
    phase6 = P({k: v for k, v in phase.c.items() if sum(k) <= 6})
    assert not (phase6-(t-F(1, 120)*t**5)).c

    data = json.loads((root/'reproduction/new_baseline.json').read_text())
    d = np.asarray(data['reduced']['d'], dtype=float)
    nu = np.asarray(data['reduced']['nu'], dtype=float)
    a0 = -np.array([[d[0]**4, 2*d[0]**2*d[1]**2],
                    [2*d[0]**2*d[1]**2, d[1]**4]])/8
    divisors = [(float(abs(np.dot(k, nu))), list(k))
                for k in itertools.product(range(-4, 5), repeat=2)
                if 0 < sum(abs(ki) for ki in k) <= 4]
    result = {
        'central4_identity': 'J grad(f^T hessian(h) f) = f_second[f,f] - 2 (f_prime)^2 f',
        'central4_exact_rational_polynomial_components_pass': identity,
        'test_hamiltonian': '(x1^2+2*x2^2+y1^2+2*y2^2)/2+x1^2*x2/7+2*x1*y1*y2/9+(x1+x2)^4/11',
        'harmonic_phase_through_degree6': 't-t^5/120',
        'A_nominal': a0.tolist(),
        'detA_nominal': float(np.linalg.det(a0)),
        'sigma_min_A_nominal': float(np.linalg.svd(a0, compute_uv=False)[-1]),
        'min_finite_divisor_order4': min(divisors),
        'scope': 'Algebra checks and floating-point parameter evaluation; no rigorous complex norm, observation defect, KAM threshold or torus certificate.'
    }
    return result


def magnetic_central4_checks(data):
    """Differentiate the scalar correction independently by complex steps."""
    nmat = np.diag(data['reduced']['nu'])
    d = np.asarray(data['reduced']['d'], dtype=float)
    j = np.block([[np.zeros((2, 2)), np.eye(2)],
                  [-np.eye(2), np.zeros((2, 2))]])
    records = []
    for kappa in (0.8, 1.0, 1.2):
        for z in (np.array([.17, -.11, .09, .04]),
                  np.array([-.31, .23, -.08, .13])):
            def ingredients(state):
                x, y = state[:2], state[2:]
                s0 = d@x
                u = nmat@x+kappa*(np.sin(s0)-s0)*d
                a = nmat+kappa*(np.cos(s0)-1)*np.outer(d, d)
                v = nmat@y
                return s0, u, a, v, d@v

            def scalar(state):
                _, u, a, v, _ = ingredients(state)
                return v@a@v+u@nmat@u

            def correction(state):
                s0, u, a, v, b = ingredients(state)
                return np.r_[2*nmat@a@v,
                    kappa*np.sin(s0)*b*b*d-2*a@nmat@u]

            s0, u, a, v, b = ingredients(z)
            nd = nmat@d
            qx = -2*kappa*np.sin(s0)*b*np.outer(nd, d)
            qy = 2*nmat@a@nmat
            px = (kappa*(np.cos(s0)*b*b+2*np.sin(s0)*(d@nmat@u))
                  *np.outer(d, d)-2*a@nmat@a)
            py = 2*kappa*np.sin(s0)*b*np.outer(d, nd)
            jac = np.block([[qx, qy], [px, py]])
            step = 1e-25
            cs_grad = np.empty(4)
            cs_jac = np.empty((4, 4))
            for col in range(4):
                zz = z.astype(complex)
                zz[col] += 1j*step
                cs_grad[col] = np.imag(scalar(zz))/step
                cs_jac[:, col] = np.imag(correction(zz))/step
            gradient_error = float(np.max(np.abs(j@cs_grad-correction(z))))
            jac_error = float(np.max(np.abs(cs_jac-jac)))
            hamiltonian_defect = float(np.max(np.abs(jac.T@j+j@jac)))
            scale = max(1., float(np.max(np.abs(jac))))
            passed = (gradient_error <= 2e-12*scale
                      and jac_error <= 2e-12*scale
                      and hamiltonian_defect <= 2e-12*scale)
            records.append({'kappa': kappa, 'state': z.tolist(),
                'gradient_max_error': gradient_error,
                'jacobian_max_error': jac_error,
                'hamiltonian_jacobian_max_defect': hamiltonian_defect,
                'scale': scale, 'passed': bool(passed)})
    return {'method': 'Complex-step derivative of f^T hessian(h) f and of its correction vector; sampled floating-point diagnostic.',
            'cases': records, 'passed': all(x['passed'] for x in records)}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def escaped(text, pos):
    backslashes = 0
    pos -= 1
    while pos >= 0 and text[pos] == '\\':
        backslashes += 1
        pos -= 1
    return bool(backslashes % 2)


def strip_tex_comments(text):
    lines = []
    for line in text.replace('\r\n', '\n').splitlines(keepends=True):
        cut = next((i for i, c in enumerate(line)
                    if c == '%' and not escaped(line, i)), None)
        lines.append(line if cut is None else line[:cut]+'\n')
    return ''.join(lines)


MATH_BEGIN = re.compile(
    r'\\begin\{(equation\*?|align\*?|gather\*?|multline\*?|displaymath|eqnarray\*?)\}'
    r'|\\\[|\\\(|\$\$|\$')
COMMAND = re.compile(
    r'\\(?:label|eqref|ref|citep|citet|cite)\*?\s*'
    r'(?:\[[^\]]*\]\s*)*\{[^{}]*\}')
ENVIRONMENT = re.compile(r'\\(begin|end)\{([^}]+)\}')
LABEL = re.compile(r'\\label\{([^}]+)\}')
REFERENCE = re.compile(r'\\(?:eqref|ref)\{([^}]+)\}')


def protected_content(text):
    """Lexical scan avoids counting nested aligned blocks twice."""
    text = strip_tex_comments(text)
    math = []
    start = 0
    while True:
        match = MATH_BEGIN.search(text, start)
        if match is None:
            break
        if escaped(text, match.start()):
            start = match.end()
            continue
        opener = match.group(0)
        env = match.group(1)
        if env:
            closer, kind = '\\end{'+env+'}', 'display:'+env
        elif opener == r'\[':
            closer, kind = r'\]', 'display:bracket'
        elif opener == r'\(':
            closer, kind = r'\)', 'inline:parenthesis'
        elif opener == '$$':
            closer, kind = '$$', 'display:dollars'
        else:
            closer, kind = '$', 'inline:dollar'
        end = text.find(closer, match.end())
        while end >= 0 and escaped(text, end):
            end = text.find(closer, end+len(closer))
        if end < 0:
            raise ValueError('Unclosed math at line %d (%s)' %
                             (text.count('\n', 0, match.start())+1, opener))
        end += len(closer)
        math.append((kind, text[match.start():end]))
        start = end
    environments = ENVIRONMENT.findall(text)
    stack = []
    for action, env in environments:
        if action == 'begin':
            stack.append(env)
        elif not stack or stack.pop() != env:
            raise ValueError('Mismatched environment: '+env)
    if stack:
        raise ValueError('Unclosed environments: '+repr(stack))
    return {'math': math, 'labels': LABEL.findall(text),
            'commands': COMMAND.findall(text), 'environments': environments,
            'references': REFERENCE.findall(text)}


def mismatch_indices(a, b):
    return [i for i in range(max(len(a), len(b)))
            if i >= len(a) or i >= len(b) or a[i] != b[i]][:20]


def english_source_checks(root):
    freeze_path = root/'provenance/english_master_freeze.json'
    freeze = json.loads(freeze_path.read_text())['files'] if freeze_path.exists() else None
    all_labels = Counter()
    for path in (root/'english').rglob('*.tex'):
        all_labels.update(LABEL.findall(strip_tex_comments(path.read_text())))
    records = {}
    for name in THEORY_FILES:
        path = root/'english/sections'/name
        if not path.exists():
            records[name] = {'passed': False, 'missing_file': True}
            continue
        try:
            data = protected_content(path.read_text())
            missing_anchors = [a for a in EXPECTED_LABELS[name]
                               if a not in data['labels']]
            duplicates = [a for a in data['labels'] if all_labels[a] != 1]
            unresolved = sorted(set(a for a in data['references']
                                    if not all_labels[a]))
            frozen_hash = freeze.get('english/sections/'+name) if freeze is not None else None
            matches_freeze = sha256(path) == frozen_hash if freeze is not None else None
            records[name] = {'sha256': sha256(path),
                'frozen_english_sha256': frozen_hash, 'matches_english_freeze': matches_freeze,
                'display_math_count': sum(k.startswith('display:') for k, _ in data['math']),
                'inline_math_count': sum(k.startswith('inline:') for k, _ in data['math']),
                'label_count': len(data['labels']), 'labels': data['labels'],
                'environment_events': len(data['environments']),
                'missing_required_labels': missing_anchors,
                'duplicate_labels': duplicates, 'unresolved_source_refs': unresolved,
                'passed': not (missing_anchors or duplicates or unresolved)
                          and (freeze is None or matches_freeze)}
        except ValueError as error:
            records[name] = {'passed': False, 'parse_error': str(error)}
    return {'files': records, 'passed': all(x['passed'] for x in records.values()),
            'scope': 'All five English theory files; protected mathematics, expected anchor placement, unique labels, source references and comparison to the English-freeze manifest when present. No PDF compilation.'}


def translation_checks(root, requested):
    records = {}
    for name in THEORY_FILES:
        en = root/'english/sections'/name
        zh = root/'chinese/sections'/name
        if not requested:
            records[name] = {'english_exists': en.exists(),
                            'chinese_exists': zh.exists(),
                            'status': 'not_checked; translation pending or explicitly not requested'}
            continue
        if not en.exists() or not zh.exists():
            records[name] = {'passed': False, 'missing_files':
                [str(p.relative_to(root)) for p in (en, zh) if not p.exists()]}
            continue
        try:
            a, b = protected_content(en.read_text()), protected_content(zh.read_text())
            math_equal = a['math'] == b['math']
            normalized_a = [(k, re.sub(r'\s+', '', v)) for k, v in a['math']]
            normalized_b = [(k, re.sub(r'\s+', '', v)) for k, v in b['math']]
            labels_equal = a['labels'] == b['labels']
            commands_equal = a['commands'] == b['commands']
            environments_equal = a['environments'] == b['environments']
            records[name] = {'english_sha256': sha256(en), 'chinese_sha256': sha256(zh),
                'english_math_count': len(a['math']), 'chinese_math_count': len(b['math']),
                'display_math_count': sum(k.startswith('display:') for k, _ in a['math']),
                'inline_math_count': sum(k.startswith('inline:') for k, _ in a['math']),
                'math_literal_equal': math_equal,
                'math_whitespace_normalized_equal': normalized_a == normalized_b,
                'ordered_labels_equal': labels_equal,
                'ordered_reference_citation_label_commands_equal': commands_equal,
                'ordered_environment_events_equal': environments_equal,
                'math_mismatch_indices_0based': mismatch_indices(a['math'], b['math']),
                'command_mismatch_indices_0based': mismatch_indices(a['commands'], b['commands']),
                'passed': math_equal and labels_equal and commands_equal and environments_equal}
        except ValueError as error:
            records[name] = {'passed': False, 'parse_error': str(error)}
    return {'requested': requested,
            'status': 'checked' if requested else 'pending; not a translation approval',
            'passed': all(x['passed'] for x in records.values()) if requested else None,
            'files': records,
            'scope': 'Literal protected mathematics and label/reference/citation and environment order only; prose completeness and rendered layout need separate review.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-translation', action='store_true',
                        help='Require all five EN/ZH theory pairs to agree in protected content.')
    parser.add_argument('--output', type=Path,
                        default=ROOT/'reviews/structure_formula_checks.json')
    args = parser.parse_args()
    result = algebra_checks(ROOT)
    baseline = ROOT/'reproduction/new_baseline.json'
    result.update({'revision': 'Direction-I framework, 2026-10-28',
                   'script_sha256': sha256(Path(__file__)),
                   'baseline_sha256': sha256(baseline)})
    result['magnetic_central4_derivatives'] = magnetic_central4_checks(
        json.loads(baseline.read_text()))
    result['english_source_checks'] = english_source_checks(ROOT)
    result['translation_checks'] = translation_checks(ROOT, args.check_translation)
    result['passed'] = (result['magnetic_central4_derivatives']['passed']
        and result['english_source_checks']['passed']
        and (not args.check_translation or result['translation_checks']['passed']))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n')
    print(json.dumps({'passed': result['passed'],
        'english_source_checks': result['english_source_checks']['passed'],
        'magnetic_central4_derivatives': result['magnetic_central4_derivatives']['passed'],
        'translation_checks': result['translation_checks']['status'],
        'translation_passed': result['translation_checks']['passed'],
        'theory_files': list(THEORY_FILES), 'output': str(args.output)}, indent=2))
    if not result['passed']:
        sys.exit(1)


if __name__ == '__main__':
    main()
