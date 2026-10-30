"""Restore fusion Direction II on the variable-mass 3D ROM and actual coils.

The frozen S5 complex hidden network generates one canonical reference. It was
trained for ideal axial bias; the plant here uses full Biot--Savart bias. No
constant-N cancellation or inverse Legendre map is assumed for this network.
All derivatives/time below use canonical (Q,P), tau=omega0*t_seconds.
"""
from pathlib import Path
import hashlib
import sys
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'stage5/program'))
from coil_rom import CoilROM
from coil_control import CurrentAllocator
from learning_models import make_model

CHECKPOINT = ROOT / 'stage5/results/learning/S5_L01_complex_hidden_seed51001.pt'


class LearnedReference:
    def __init__(self, plant, checkpoint=CHECKPOINT):
        payload = torch.load(checkpoint, map_location='cpu', weights_only=False)
        if payload['kind'] != 'complex_hidden' or payload['n'] != plant.n:
            raise ValueError('Expected the actual S5 complex-hidden 12-coordinate checkpoint')
        self.n = plant.n
        self.net = make_model(payload['kind'], payload['n'], payload['amplitude'],
                              payload['output_scale'], payload['seed'])
        self.net.load_state_dict(payload['state_dict'])
        self.net.eval()
        self.amplitude = payload['amplitude']
        self.scale = torch.cat((torch.sqrt(plant.rom.nu), torch.sqrt(plant.rom.nu))) / self.amplitude
        self.J = plant.J_tensor
        self.metadata = dict(checkpoint=str(checkpoint.relative_to(ROOT)),
            checkpoint_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
            checkpoint_target=payload['target'], network='full complex hidden layers, S5 frozen seed51001',
            normalization='x=diag(sqrt(nu),sqrt(nu))*z/amplitude; differentiate Hhat with respect to z',
            reference='Hhat=.5*amplitude**2*|x|**2+complex_residual(x)',
            plant='full Biot-Savart Hcoil; not the ideal-axial-bias target of Hhat',
            hessian_scope='canonical reference flow uses no inversion of learned momentum Hessian')

    def hamiltonian_tensor(self, z):
        x = self.scale * z
        return .5 * self.amplitude**2 * (x*x).sum() + self.net(x[None, :])[0]

    def field_tensor(self, z):
        return self.J @ torch.func.grad(self.hamiltonian_tensor)(z)

    def field(self, z):
        return self.field_tensor(torch.as_tensor(z)).detach().numpy()

    def kinematics(self, z):
        zt = torch.as_tensor(z)
        field = self.field_tensor(zt)
        acceleration = torch.func.jvp(lambda zz:self.field_tensor(zz)[:self.n], (zt,), (field,))[1]
        return field[:self.n].detach().numpy(), acceleration.detach().numpy()


def velocity_tensor(plant, z):
    return torch.linalg.solve(plant.mass_tensor(z[:plant.n]), z[plant.n:])


def acceleration(plant, z, currents=None, gamma=0.):
    zt = plant.tensor(z)
    it = None if currents is None else plant.tensor(currents)
    f = plant.field_tensor(zt, it, gamma)
    return torch.func.jvp(lambda zz:velocity_tensor(plant,zz), (zt,), (f,))[1].detach().numpy()


def tracking_request(plant, reference, z, zr, kp=1., kd=2., gamma=0.):
    """Exact-model full-force request; only allocation turns it into real input.

    desired=M(Q)[a_r-kp e-kd e'-a_base]. With residual r=G delta_i-desired,
    e''+kd e'+kp e=M(Q)^-1 r at the decision state. This identity is local,
    does not guarantee reachability, and includes all geometric inertia.
    """
    n = plant.n
    v = velocity_tensor(plant,plant.tensor(z)).detach().numpy()
    vr, ar = reference.kinematics(zr)
    abase = acceleration(plant,z,gamma=gamma)
    e = z[:n]-zr[:n]
    edot = v-vr
    desired_acceleration = ar-kp*e-kd*edot
    mass = plant.mass(z[:n])
    desired = mass@(desired_acceleration-abase)
    return desired, dict(position_error=e, velocity_error=edot, reference_velocity=vr,
        reference_acceleration=ar, base_acceleration=abase, desired_acceleration=desired_acceleration,
        mass=mass)


def identity_diagnostics(plant, reference, z, zr, current, kp=1., kd=2., gamma=0.):
    desired, d = tracking_request(plant,reference,z,zr,kp,kd,gamma)
    actual = acceleration(plant,z,current,gamma)
    residual = plant.current_port(z[:plant.n])@(current-plant.bias_currents)-desired
    lhs = actual-d['reference_acceleration']+kd*d['velocity_error']+kp*d['position_error']
    rhs = np.linalg.solve(d['mass'],residual)
    return dict(identity_absolute_residual=float(np.linalg.norm(lhs-rhs)),
        identity_relative_residual=float(np.linalg.norm(lhs-rhs)/max(1.,np.linalg.norm(lhs),np.linalg.norm(rhs))),
        force_residual_norm=float(np.linalg.norm(residual)), acceleration_disturbance_norm=float(np.linalg.norm(rhs)),
        constant_mass_substitution_error=float(np.linalg.norm(plant.mass(np.zeros(plant.n))@(d['desired_acceleration']-d['base_acceleration'])-desired)))
