"""New one-feature physical residual identification, not a full CHNN retraining.

The manufactured residual is a scalar multiple of a real ROM magnetic potential.
Fit only training labels; evaluate held-out states and compensate via physical Gm.
"""
from pathlib import Path
import hashlib
import json
import time
import numpy as np
import torch
from control_experiments import ROMBridge, integrate, field_limits

ROOT=Path(__file__).resolve().parents[1]


class LearnedPhysicalResidual:
    def __init__(self,bridge,beta_true,beta_hat,template,gamma=.2):
        self.bridge=bridge;self.beta_true=beta_true;self.beta_hat=beta_hat
        self.template=template;self.gamma=gamma

    def evaluate(self,z,policy):
        compensation={'uncompensated_residual':0.,'learned_feature_compensation':self.beta_hat,
                      'true_coefficient_compensation':self.beta_true}[policy]
        actuator=-compensation*self.template
        total=(self.beta_true-compensation)*self.template
        base=self.bridge.field(z,gamma=self.gamma)
        actual=self.bridge.field(z,gamma=self.gamma,u=total)
        return actual,actuator,actual[self.bridge.n:]-base[self.bridge.n:]


def labels(bridge,states,template,beta):
    energy=[];force=[];feature=[];potential=[]
    for z in states:
        h=bridge.hamiltonian(z);hu=bridge.hamiltonian(z,u=beta*template)
        energy.append(hu-h)
        force.append((bridge.field(z,u=beta*template)-bridge.field(z))[bridge.n:])
        feature.append(bridge.magnetic_map(z[:bridge.n])@template)
        potential.append(bridge.hamiltonian(z,u=template)-h)
    return np.array(energy),np.array(force),np.array(feature),np.array(potential)


def main():
    start=time.perf_counter();out=ROOT/'results/control_learning';out.mkdir(parents=True,exist_ok=True)
    torch.set_num_threads(1);bridge=ROMBridge();rng=np.random.default_rng(102533)
    scales=np.tile(.01/np.sqrt(bridge.rom.nu.numpy()),2)
    train=rng.uniform(-1,1,(8,24))*scales
    test=rng.uniform(-1,1,(8,24))*scales
    beta=.2;template=np.array([.0001,-.00006,0.,0.,0.,0.,0.,0.])
    tr=labels(bridge,train,template,beta);te=labels(bridge,test,template,beta)
    coef=float(np.sum(tr[2]*tr[1])/np.sum(tr[2]**2))
    records={}
    for name,data in [('train',tr),('heldout',te)]:
        he,force,feature,potential=data
        residual=coef*feature-force
        records[name]=dict(samples=len(he),force_relative_l2=float(np.linalg.norm(residual)/np.linalg.norm(force)),
            maximum_force_error=float(np.linalg.norm(residual,axis=1).max()),
            energy_rmse=float(np.sqrt(np.mean((coef*potential-he)**2))))
    model=LearnedPhysicalResidual(bridge,beta,coef,template)
    arrays=dict(train_states=train,heldout_states=test,train_force=tr[1],heldout_force=te[1],template_input=template)
    summaries=[]
    # The independent target is the already executed damped ROM with no residual.
    target=np.load(ROOT/'results/control/trajectories.npz')['uncontrolled_state']
    for policy in ('uncompensated_residual','learned_feature_compensation','true_coefficient_compensation'):
        summary,states,inputs=integrate(bridge,model,policy,.004,16)
        summary['maximum_error_to_same_RK4_unperturbed_target']=float(np.linalg.norm(states-target,axis=1).max())
        summary['target_caveat']='same numerical time grid/algorithm; cancellation consistency, not an independent continuous-reference error'
        arrays[policy+'_states']=states;arrays[policy+'_actuator_input']=inputs;summaries.append(summary)
    # Local port reachability: the deliberately manufactured potential belongs
    # to the magnetic span; arbitrary inertial/phase residuals need not do so.
    z0=bridge.initial_state();g=bridge.magnetic_map(z0[:12])
    cancellation=g@((beta-coef)*template)
    report=dict(status='executed',label_protocol='new noiseless exact-ROM evaluations at 8 uniform training and 8 independently drawn held-out states; random seed102533; no time trajectories used for fitting',
      model='one real scalar coefficient of an explicitly manufactured conservative magnetic-potential feature; not a complete complex CHNN',
      residual_potential='delta H(z)=beta [H(z,u_template)-H(z,0)]',beta_true=beta,beta_fitted=coef,
      input_template_SI=template.tolist(),scores=records,
      actuator_limits=field_limits(bridge,-coef*template),
      uncancelled_actual_magnetic_force_norm=float(np.linalg.norm(cancellation)),trajectories=summaries,
      missing_full_CHNN='Frozen complex_seed1025.pt, learning_data.npz, learning_summary.json and analytic_coefficients.npy absent from supplied lightweight tree; old results not promoted to current verification.',
      limitation='Single-feature noiseless identification with a disturbance chosen inside the magnetic image. No unknown inertia/damping identification, noise robustness, coil-realized compensation, CHNN accuracy, or long-time robot performance claim.',
      elapsed_seconds=time.perf_counter()-start,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (out/'learning_results.json').write_text(json.dumps(report,indent=2));np.savez_compressed(out/'learning_data_and_trajectories.npz',**arrays)
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
