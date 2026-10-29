"""S5-L01 models in the unchanged 24-dimensional canonical ROM.

The polynomial readout spans every degree-3/4 mechanical monomial: pure
configuration terms and terms quadratic in momentum. It is a finite analytic
readout in the v10 sense, enlarged for the 12-coordinate mechanical model;
it is not the old 35-coefficient checkpoint or an unrestricted degree-4 energy.
"""
from __future__ import annotations
import itertools
from pathlib import Path
import sys
import torch
from torch import nn

ROOT=Path(__file__).resolve().parents[2]
S2=ROOT/'stage3/source_inputs/starter/stage2/program/learning'
sys.path.insert(0,str(S2))
from rod_rom import RodROM
from run_learning import ComplexResidual, polynomial_design, labels
from train_spd_complex import MechanicalComplexResidual


class MechanicalPolynomial(nn.Module):
    def __init__(self,n=12,output_scale=1.):
        super().__init__();self.n=n;self.output_scale=float(output_scale)
        for degree in (2,3,4):
            indices=list(itertools.combinations_with_replacement(range(n),degree))
            self.register_buffer(f'index{degree}',torch.tensor(indices,dtype=torch.int64))
        n2=len(self.index2)
        self.c3=nn.Parameter(torch.zeros(len(self.index3)))
        self.c4=nn.Parameter(torch.zeros(len(self.index4)))
        self.c12=nn.Parameter(torch.zeros(n,n2))
        self.c22=nn.Parameter(torch.zeros(n2,n2))

    def forward(self,x):
        q,p=x[:,:self.n],x[:,self.n:]
        q2=q[:,self.index2].prod(-1);p2=p[:,self.index2].prod(-1)
        pure=q[:,self.index3].prod(-1)@self.c3+q[:,self.index4].prod(-1)@self.c4
        kinetic=((q@self.c12+q2@self.c22)*p2).sum(-1)
        return self.output_scale*(pure+kinetic)


def make_model(kind,n,amplitude,hscale,seed):
    torch.manual_seed(seed)
    if kind=='analytic_mechanical4':return MechanicalPolynomial(n,hscale)
    if kind=='complex_hidden':return ComplexResidual(n,48,hscale)
    if kind=='spd_complex':return MechanicalComplexResidual(n,48,amplitude,hscale)
    raise ValueError(kind)


def real_parameter_count(net):
    return sum(p.numel()*(2 if p.is_complex() else 1) for p in net.parameters())


def predict(net,x,batch=128):
    values=[];gradients=[]
    for start in range(0,len(x),batch):
        xx=torch.as_tensor(x[start:start+batch]).clone().requires_grad_(True)
        h=net(xx);g=torch.autograd.grad(h.sum(),xx)[0]
        values.append(h.detach());gradients.append(g.detach())
    return torch.cat(values).numpy(),torch.cat(gradients).numpy()
