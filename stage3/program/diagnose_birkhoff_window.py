"""Diagnose local applicability of the truncated one-form at the actual ROM state.

Instantaneous eigenvalues of a nonautonomous field are diagnostics, not a
trajectory instability theorem. This calculation does not use any exact flow.
"""
from pathlib import Path
import json
import time
import numpy as np
from birkhoff_rom import LocalBirkhoffROM
from run_birkhoff import chart_jacobian


def main():
    model=LocalBirkhoffROM()
    z=model.bridge.initial_state()
    nu=np.asarray(model.bridge.rom.nu)
    rows=[]
    for t in [0.,.00025,.0005,.001,.004]:
        start=time.perf_counter()
        field=model.approximate_field(t,z)
        field_seconds=time.perf_counter()-start
        start=time.perf_counter()
        matrix=chart_jacobian(model,t,model.chart(z,t))
        elapsed=time.perf_counter()-start
        eig=np.linalg.eigvals(matrix)
        row=dict(time_tau=t,original_fixed_state=z.tolist(),
                 represented_field_norm=float(np.linalg.norm(field)),
                 field_seconds=field_seconds,chart_Jacobian_seconds=elapsed,
                 max_real_eigenvalue=float(eig.real.max()),
                 max_absolute_imaginary_eigenvalue=float(abs(eig.imag).max()),
                 chart_Hessian_condition=float(np.linalg.cond(-model.J@matrix)),
                 eigenvalues_real=eig.real.tolist(),eigenvalues_imag=eig.imag.tolist())
        rows.append(row)
        print(json.dumps({k:v for k,v in row.items() if not isinstance(v,list)}),flush=True)
    # In the diagonal small-amplitude limit H=.5 nu(Q^2+P^2),
    # Hc=.5nu(Q^2+P^2)+2t nu^2 QP+2t gamma nu P^2.
    # After P'=w P, the squared instantaneous eigenvalue is
    # (nu/w)^2 * ((2t nu)^2 - 1 - 4t gamma).
    rates=model.rates
    transitions=(rates+np.sqrt(rates*rates+nu*nu))/(2*nu*nu)
    result=dict(diagnostics=rows,model=model.bridge.metadata(),
                linearized_hamiltonian='Hc=.5 nu(Q^2+P^2)+2t nu^2 QP+2t gamma nu P^2, with P=Pchart/(1+t gamma)',
                linearized_chart_eigenvalue_squared='(nu/(1+t gamma))^2*((2t nu)^2-1-4t gamma)',
                maximum_frequency=float(nu.max()),
                no_drag_transition_tau=float(1/(2*nu.max())),
                per_mode_transition_tau=transitions.tolist(),
                first_linearized_transition_tau=float(transitions.min()),
                interpretation='First-order transport can preserve a well-conditioned two-form while producing a poor represented field. Positive instantaneous real eigenvalues flag strong local stretching; they do not prove nonautonomous trajectory instability or physical robot instability.',
                scope='Fixed original initial state and ideal AD Jacobians. No represented trajectory integration, no exact physical flow, no relaxation of solver tolerances.')
    out=Path(__file__).resolve().parents[1]/'results/birkhoff/window_diagnostic.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
