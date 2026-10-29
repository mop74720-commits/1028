"""Training/validation-only timing probe; never opens test/OOD labels."""
from pathlib import Path
import json,time,sys
import numpy as np
import torch
from learning_models import RodROM,labels,make_model,real_parameter_count,predict

ROOT=Path(__file__).resolve().parents[2]
torch.set_default_dtype(torch.float64);torch.set_num_threads(1);torch.set_num_interop_threads(1)
out=ROOT/'stage5/results/learning';out.mkdir(parents=True,exist_ok=True)
rng=np.random.default_rng(51001);rom=RodROM();amp=.08
begin=time.perf_counter()
train=labels(rom,rng.uniform(-1,1,(1024,24)),amp)
valid=labels(rom,rng.uniform(-1,1,(256,24)),amp)
np.savez_compressed(out/'S5_L01_training_data.npz',**{'train_'+k:v for k,v in train.items()},**{'valid_'+k:v for k,v in valid.items()})
scale=torch.cat([torch.sqrt(rom.nu)]*2)/amp
hscale=max(np.std(train['h_res']),1e-7)
gscale=max(np.sqrt(np.mean((train['g_res']*scale.numpy())**2)),1e-7)
record={'scope':'train/validation-only timing, no test or OOD generated','dataset_seconds':time.perf_counter()-begin,'hscale':hscale,'gscale_z':gscale,'model':rom.metadata(),'runs':[]}
for kind,lr in [('analytic_mechanical4',.001),('complex_hidden',.003),('spd_complex',.003)]:
    net=make_model(kind,12,amp,hscale,51001);opt=torch.optim.Adam(net.parameters(),lr=lr)
    rr=np.random.default_rng(51001);history=[];start=time.perf_counter()
    for step in range(101):
        idx=rr.integers(0,len(train['x']),128);x=torch.tensor(train['x'][idx],requires_grad=True)
        h=net(x);g=torch.autograd.grad(h.sum(),x,create_graph=True)[0]
        loss=(((g-torch.tensor(train['g_res'][idx]))*scale)/gscale).square().mean()+.15*((h-torch.tensor(train['h_res'][idx]))/hscale).square().mean()
        opt.zero_grad(set_to_none=True);loss.backward();torch.nn.utils.clip_grad_norm_(net.parameters(),10.);opt.step()
        if step%50==0:
            vh,vg=predict(net,valid['x'])
            v=float(np.linalg.norm((vg-valid['g_res'])*scale.numpy())/np.linalg.norm(valid['g_res']*scale.numpy()))
            history.append(dict(step=step,training_loss=float(loss.detach()),validation_residual_canonical_gradient_relative_l2=v))
    row=dict(kind=kind,lr=lr,real_parameters=real_parameter_count(net),seconds=time.perf_counter()-start,history=history)
    record['runs'].append(row);print(json.dumps(row),flush=True)
(out/'S5_L01_pilot.json').write_text(json.dumps(record,indent=2)+'\n')
