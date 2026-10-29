"""The actual 36-dimensional sampled controller map, including current memory."""
import numpy as np
from coil_control import CurrentAllocator, ramp_current


class SampledCurrentMap:
    def __init__(self,model,kind='collocated',interval=.0005,substeps=2,gamma=.2):
        if kind not in ('collocated','damping_compensation'):
            raise ValueError(kind)
        self.model=model;self.kind=kind;self.interval=interval
        self.substeps=substeps;self.gamma=gamma
        self.allocator=CurrentAllocator(model)

    def __call__(self,augmented):
        model=self.model;n=model.n
        z=np.asarray(augmented[:2*n]).copy();previous=np.asarray(augmented[2*n:]).copy()
        dt_seconds=self.interval/model.rom.omega0
        if self.kind=='collocated':
            requested=model.collocated_current_tensor(model.tensor(z)).detach().numpy()
            target,allocation=self.allocator.allocate(z[:n],requested,previous,dt_seconds)
        else:
            target,allocation=self.allocator.allocate_force(z[:n],self.gamma*z[n:],previous,dt_seconds)
        cap=model.coil_config['slew_bound_A_s']*dt_seconds
        bound=model.coil_config['current_bound_A']
        lo=np.maximum(-bound,previous-cap);hi=np.minimum(bound,previous+cap)
        signature=dict(lower=np.flatnonzero(abs(target-lo)<1e-8).tolist(),
                       upper=np.flatnonzero(abs(target-hi)<1e-8).tolist(),
                       allocator_message=allocation['message'])
        h=self.interval/self.substeps
        def field(state,tau):
            current=ramp_current(previous,target,tau,0.,self.interval)
            return model.field(state,current,gamma=self.gamma)
        for k in range(self.substeps):
            t=k*h
            a=field(z,t);b=field(z+h*a/2,t+h/2)
            c=field(z+h*b/2,t+h/2);d=field(z+h*c,t+h)
            z=z+h*(a+2*b+2*c+d)/6
        return np.r_[z,target],dict(allocation=allocation,active_box_signature=signature)


def finite_difference_jacobian(mapping,point,epsilon=1e-6):
    columns=[];signatures=[]
    for k in range(len(point)):
        e=np.zeros_like(point);e[k]=epsilon
        plus,a=mapping(point+e);minus,b=mapping(point-e)
        columns.append((plus-minus)/(2*epsilon))
        signatures.extend([a['active_box_signature'],b['active_box_signature']])
    return np.column_stack(columns),signatures
