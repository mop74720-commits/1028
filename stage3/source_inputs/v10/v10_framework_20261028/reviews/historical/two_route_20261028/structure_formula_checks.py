"""Small independent algebra checks for the integrated English derivation.

Uses exact rational multivariate polynomials for the Central4 identity;
floating-point FE-derived twist values are diagnostics, not certificates.
"""
from fractions import Fraction as F
from pathlib import Path
import itertools
import json
import numpy as np


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

root = Path(__file__).resolve().parents[1]
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
(root/'reviews/structure_formula_checks.json').write_text(
    json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
