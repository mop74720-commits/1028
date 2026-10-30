"""Dual-route budget interfaces and finite-feature bounds for the actual 24D ROM.

The polynomial is loaded from the frozen S5-L01 checkpoint, not retrained. Bounds
are for that learned polynomial on a complex polydisk. They are NOT bounds on
its error relative to the unknown analytic continuation of the true ROM.
Floating evaluations of proved majorants are not interval certificates.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
import itertools
from pathlib import Path
import numpy as np


@dataclass
class MechanicalPolynomialBudget:
    exponents: np.ndarray
    canonical_coefficients: np.ndarray
    coordinate_scale: np.ndarray
    output_scale: float
    n: int

    @classmethod
    def from_checkpoint(cls, checkpoint: dict, coordinate_scale):
        n = int(checkpoint['n'])
        state = checkpoint['state_dict']
        scale = np.asarray(coordinate_scale, dtype=float)
        if checkpoint['kind'] != 'analytic_mechanical4' or scale.shape != (2*n,):
            raise ValueError('Expected frozen mechanical polynomial and its canonical scaling')
        indices = {d: state[f'index{d}'].cpu().numpy() for d in (2,3,4)}
        powers, weights = [], []
        def append(qindices, pindices, weight):
            exponent = np.bincount(list(qindices)+[int(i)+n for i in pindices], minlength=2*n)
            powers.append(exponent)
            weights.append(float(weight))
        for d in (3,4):
            for inds, weight in zip(indices[d], state[f'c{d}'].detach().cpu().numpy()):
                append(inds, [], weight)
        for qi in range(n):
            for pj, pinds in enumerate(indices[2]):
                append([qi], pinds, state['c12'][qi,pj])
        for qi, qinds in enumerate(indices[2]):
            for pj, pinds in enumerate(indices[2]):
                append(qinds, pinds, state['c22'][qi,pj])
        powers = np.asarray(powers, dtype=np.int16)
        hscale = float(checkpoint['output_scale'])
        coefficients = hscale*np.asarray(weights)*np.prod(scale[None,:]**powers, axis=1)
        return cls(powers, coefficients, scale, hscale, n)

    def evaluate(self, z):
        z = np.asarray(z)
        terms = np.prod(z[...,None,:]**self.exponents, axis=-1)
        return terms@self.canonical_coefficients

    def gradient(self, z):
        z = np.asarray(z)
        result = np.zeros(z.shape, dtype=np.result_type(z,float))
        for j in range(2*self.n):
            present = self.exponents[:,j]>0
            powers = self.exponents[present].copy()
            multiplier = powers[:,j].copy()
            powers[:,j] -= 1
            terms = np.prod(z[...,None,:]**powers, axis=-1)
            result[...,j] = terms@(self.canonical_coefficients[present]*multiplier)
        return result

    def majorants(self, radii):
        """Coefficient triangle bounds; Hessian row norm is a real-box SPD gate."""
        r = np.asarray(radii,dtype=float)
        if r.shape != (2*self.n,) or np.any(r<=0) or not np.all(np.isfinite(r)):
            raise ValueError('Each canonical polydisk radius must be finite and positive')
        monomials = np.prod(r[None,:]**self.exponents, axis=1)
        terms = np.abs(self.canonical_coefficients)*monomials
        first = self.exponents.T@terms
        second = self.exponents.T@(terms[:,None]*self.exponents)
        second -= np.diag(first)
        second /= np.outer(r,r)
        # Floating cancellation can only affect exact zeros in this subtraction.
        second = np.maximum(second,0.)
        feature_terms = self.output_scale*np.prod((self.coordinate_scale*r)[None,:]**self.exponents,axis=1)
        return dict(energy=float(terms.sum()), gradient=first/r,
                    hessian=second, Hpp_row_sum_bound=float(second[self.n:,self.n:].sum(axis=1).max()),
                    parameter_feature_l2_bound=float(np.linalg.norm(feature_terms)),
                    coefficient_count=len(terms))

    def momentum_convexity_bound(self, radii, frequencies):
        """Weighted sufficient Legendre domain for learned H2 + polynomial only.

        H2_PP=diag(nu). If ||diag(nu)^(-1/2) P_PP diag(nu)^(-1/2)||_2<b<1,
        the full learned momentum Hessian is positive definite throughout the
        real box. The absolute-entry row bound is sufficient, not necessary.
        """
        nu=np.asarray(frequencies,dtype=float)
        if nu.shape!=(self.n,) or np.any(nu<=0):raise ValueError('Positive physical frequencies required')
        bounds=self.majorants(radii)
        weighted=bounds['hessian'][self.n:,self.n:]/np.sqrt(np.outer(nu,nu))
        b=float(weighted.sum(axis=1).max())
        eigen_lower=(1-b)*(float(nu.min()) if b<=1 else float(nu.max()))
        eigen_lower=max(eigen_lower,float(nu.min())-bounds['Hpp_row_sum_bound'])
        return dict(relative_prior_row_bound=b,positive_definiteness_sufficient=b<1,
                    uniform_eigenvalue_lower_majorant=eigen_lower,
                    statement='learned mechanical polynomial on real box; not true-ROM approximation or global invertibility')


def route_hamiltonians(nominal, true_residual, learned_residual):
    """The fusion's two different conservative targets (ri:hamiltonians)."""
    delta = true_residual-learned_residual
    return dict(compensated=nominal+delta, learned=nominal+learned_residual,
                true=nominal+true_residual, delta=delta)


def exact_normalized_momentum_bound(checkpoint, coordinate_scale, radius=Fraction(1,20)):
    """Exact rational Gershgorin check for frozen binary polynomial coefficients.

    This certifies the declared learned point polynomial, not parameter/model
    uncertainty. Its normalized quadratic prior coefficient is float(a**2), as
    used by S5-L01. Momentum quadraticity makes the bound independent of P.
    """
    r=Fraction(radius)
    if r<=0:raise ValueError('Positive rational normalized configuration radius required')
    state=checkpoint['state_dict'];n=int(checkpoint['n'])
    sums=[Fraction(0) for _ in range(n)]
    hscale=Fraction.from_float(float(checkpoint['output_scale']))
    for name,degree in [('c12',1),('c22',2)]:
        weights=state[name].detach().cpu().numpy()
        for pair_index,pair in enumerate(state['index2'].cpu().numpy()):
            total=sum((abs(Fraction.from_float(float(w))) for w in weights[:,pair_index]),Fraction(0))
            total*=hscale*r**degree
            i,j=map(int,pair)
            if i==j:sums[i]+=2*total
            else:sums[i]+=total;sums[j]+=total
    prior=Fraction.from_float(float(checkpoint['amplitude'])**2)
    gaps=[prior-s for s in sums]
    Dp=[Fraction.from_float(float(d)) for d in np.asarray(coordinate_scale)[n:]]
    minimum=min(gaps)
    # Only the positive case allows the min(D^2) lower bound.
    canonical_lower=minimum*(min(d*d for d in Dp) if minimum>=0 else max(d*d for d in Dp))
    return dict(normalized_configuration_radius=str(r),
                normalized_prior_coefficient_exact=str(prior),
                normalized_row_bound_exact=[str(s) for s in sums],
                minimum_normalized_gap_exact=str(minimum),
                canonical_momentum_eigenvalue_lower_exact=str(canonical_lower),
                canonical_momentum_eigenvalue_lower_decimal=float(canonical_lower),
                sufficient_positive_definiteness=minimum>0,
                arithmetic='exact rational on frozen binary coefficients; decimal output is display only',
                scope='learned H2 plus mechanical polynomial; uniform on Q box, every real P; not true-ROM error certificate')


def dual_route_budget(remainder_nominal, remainder_true, feature_bound,
                      coefficient_error_bound, *, common_chart_domain_verified):
    """Never silently substitute training loss for an unknown coefficient bound."""
    if not common_chart_domain_verified:
        raise ValueError('Both chart images must be inside the declared shared complex domain')
    for value in (remainder_nominal,remainder_true,feature_bound):
        if value is None or not np.isfinite(value) or value<0:
            raise ValueError('Separate nonnegative normal-form remainders and feature bound required')
    if coefficient_error_bound is None:
        return dict(status='conditional_missing_coefficient_error_bound',
                    epsilon_A=None, epsilon_B=None, KAM_certificate=False,
                    symbolic_A=f'{remainder_nominal} + {feature_bound} * b',
                    symbolic_B=f'{remainder_true} + {feature_bound} * b')
    if coefficient_error_bound<0 or not np.isfinite(coefficient_error_bound):
        raise ValueError('Coefficient error bound must be finite and nonnegative')
    residual = coefficient_error_bound*feature_bound
    return dict(status='energy_majorant_only_not_KAM_certificate',
                epsilon_A=float(remainder_nominal+residual),
                epsilon_B=float(remainder_true+residual), KAM_certificate=False)


def homological_compatibility(frequencies, degree=4, tolerance=1.e-10):
    """Gate for the old action-only quartic template, not all-order Diophantine proof."""
    nu = np.asarray(frequencies,dtype=float)
    n = len(nu)
    powers = np.asarray([np.bincount(c,minlength=2*n)
                         for c in itertools.combinations_with_replacement(range(2*n),degree)])
    divisors = (powers[:,:n]-powers[:,n:])@nu
    resonant = abs(divisors)<=tolerance
    action = np.all(powers[:,:n]==powers[:,n:],axis=1)
    nonaction = resonant & ~action
    nonzero = abs(divisors[~resonant])
    return dict(dimension=n,degree=degree,monomials=len(powers),
                resonant_count=int(resonant.sum()), action_count=int((resonant&action).sum()),
                nonaction_resonant_count=int(nonaction.sum()), tolerance=tolerance,
                old_action_only_template_compatible=not bool(nonaction.any()),
                minimum_sampled_nonzero_divisor=float(nonzero.min()) if len(nonzero) else None,
                example_nonaction_exponents=powers[nonaction][:6].tolist(),
                all_order_nonresonance_proved=False, KAM_certificate=False)
