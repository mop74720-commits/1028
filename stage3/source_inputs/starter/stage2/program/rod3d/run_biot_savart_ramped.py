"""Continuous slew-limited currents for the constrained full-coil branch.

Targets are allocated every 2 ms; actual currents ramp linearly to the next
target. Convex sampled field constraints hold along each current segment.
"""
import run_biot_savart_constrained as guard
import model as base
import run_biot_savart as bs
from pathlib import Path
import hashlib
import json
import numpy as np

ROOT=Path(__file__).resolve().parent
OUT=ROOT.parents[1]/'results'/'rod3d'


class RampedEnvironment(guard.ConstrainedCoilEnvironment):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.ramp_start=np.zeros(12);self.ramp_target=np.zeros(12);self.ramp_time=0.
        self.ramp_log=[]

    def evaluate(self,rod,time):
        theta=np.clip((float(time)-self.ramp_time)/self.control_period,0.,1.)
        self.currents=(1-theta)*self.ramp_start+theta*self.ramp_target
        self.held_u=self.allocator.A@self.currents
        return super().evaluate(rod,time)

    def apply_forces(self,system,time=0.):
        index=int(np.floor((float(time)+1e-12)/self.control_period))
        if index>self.control_index:
            control_time=index*self.control_period
            _,requested,_,_=self.desired_command(system,float(time))
            start=self.ramp_target.copy()
            _,target=self.allocator.allocate(requested,control_time)
            self.ramp_start=start;self.ramp_target=target;self.ramp_time=control_time
            self.ramp_log.append(np.r_[control_time,control_time+self.control_period,start,target])
            self.coil_log.append(np.r_[control_time,requested,self.allocator.A@start,start])
            self.control_index=index
        self.last=self.evaluate(system,time)
        self.before_v=system.velocity_collection.copy();self.before_w=system.omega_collection.copy()
        system.external_forces+=self.last[0].sum(axis=0);system.external_torques+=self.last[1].sum(axis=0)
        if self.control_index!=self.last_audit_index:
            b,g=bs.field_gradient(system.position_collection.T,self.wire,self.dl,self.currents,self.prefactor)
            self.audit_rows.append([time,float(np.linalg.norm(b,axis=1).max()),float(np.linalg.norm(g,axis=(1,2)).max()),float(guard.distance_to_wires(system.position_collection.T,self.allocator.config).min())])
            self.last_audit_index=self.control_index


def main():
    base.Environment=RampedEnvironment;base.metrics_snapshot=bs.full_snapshot
    cfg=base.load_config(ROOT/'config_position_feedback.json')
    cfg['controller']['actual_current_reconstruction']='piecewise linear ramp toward each allocated 2ms target; no instantaneous current jumps'
    name='full_biot_savart_tube_constrained_ramped_n32_h10us'
    summary=base.run_case(name,OUT,cfg,32,1e-5,2.,.005,'coil_allocated')
    env=RampedEnvironment.instances[-1];ramps=np.asarray(env.ramp_log)
    slopes=(ramps[:,14:26]-ramps[:,2:14])/(ramps[:,1]-ramps[:,0])[:,None]
    amp=float(np.max(np.abs(ramps[:,2:26])));slew=float(np.max(np.abs(slopes)))
    assert amp<=2.+1e-10 and slew<=20.+1e-8
    continuity=float(np.max(np.abs(ramps[1:,2:14]-ramps[:-1,14:26])))
    np.savetxt(OUT/name/'current_ramps.csv',ramps,delimiter=',',header='start_time_s,end_time_s,'+','.join([f'I_start_{j+1}_A' for j in range(12)]+[f'I_end_{j+1}_A' for j in range(12)]),comments='')
    check=np.asarray(env.audit_rows)
    np.savetxt(OUT/name/'actual_field_at_control_updates.csv',check,delimiter=',',header='time_s,max_B_at_actual_nodes_T,max_G_frobenius_at_actual_nodes_T_per_m,min_distance_actual_nodes_to_wire_m',comments='')
    audit=env.allocator.audit
    audit.update(allocation_calls=env.allocator.solves,optimizer_nonconverged=env.allocator.nonconverged,fallback_to_previous_feasible_current=env.allocator.fallbacks,
                  maximum_normalized_sampled_constraint_violation=env.allocator.max_constraint_violation,
                  actual_node_checks=len(check),max_actual_node_B_T=float(check[:,1].max()),max_actual_node_G_frobenius_T_per_m=float(check[:,2].max()),
                  min_actual_node_distance_to_exact_wire_m=float(check[:,3].min()),
                  actual_current_amplitude_max_A=amp,actual_continuous_current_slew_max_A_per_s=slew,current_continuity_defect_A=continuity,
                  continuous_sampled_field_constraint_argument='Fields and gradients are linear in current; norms are convex. Every point of the line segment between feasible current endpoints remains feasible at each fixed sampled spatial point.',
                  controller_timing='No field through t=2ms; each subsequent 2ms decision is approached by a continuous linear ramp over the next interval.')
    (OUT/name/'workspace_constraint_audit.json').write_text(json.dumps(audit,indent=2))
    summary.update(magnetic_load_evaluation='full Biot-Savart with analytical derivative and sampled-tube constraints, continuous piecewise-linear actual currents',
                   coil_max_current_A=amp,coil_max_slew_A_per_s=slew,actual_current_continuity_defect_A=continuity,
                   true_max_G_at_control_updates_T_per_m=float(check[:,2].max()),true_max_B_at_control_updates_T=float(check[:,1].max()),
                   field_constraints_pass_at_actual_checked_nodes=bool(check[:,1].max()<=.005 and check[:,2].max()<=.03))
    (OUT/name/'summary.json').write_text(json.dumps(summary,indent=2))
    ep=OUT/name/'environment.json';environment=json.loads(ep.read_text())
    environment.update(full_biot_savart_extension_sha256=bs.EXTENSION_SHA256,
                       constrained_extension_sha256=hashlib.sha256((ROOT/'run_biot_savart_constrained.py').read_bytes()).hexdigest(),
                       current_ramp_extension_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                       coil_field_source_sha256=hashlib.sha256((ROOT.parent/'coil_field.py').read_bytes()).hexdigest())
    ep.write_text(json.dumps(environment,indent=2))
    print(json.dumps(audit),flush=True)


if __name__=='__main__':main()
