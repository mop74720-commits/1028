"""v10 two-mode model as a specialization, using published display precision.
No fitting, COMSOL replay, hardware validation or KAM certification is performed.
"""
from pathlib import Path
import json
import numpy as np
from scipy.integrate import solve_ivp

N=np.diag([1.,6.152117504]); d=np.array([.225670773,.321798806])
gamma=.55558524/11.417287283
J=np.block([[np.zeros((2,2)),np.eye(2)],[-np.eye(2),np.zeros((2,2))]])
K0=-J
z0=np.array([.18,.16,.03,-.02])

def gradV(q):
 s=d@q; return N@q+d*(np.sin(s)-s)
def hessV(q):
 return N+(np.cos(d@q)-1)*np.outer(d,d)
def f(z): return np.r_[N@z[2:],-gradV(z[:2])-gamma*z[2:]]
def jac(z): return np.block([[np.zeros((2,2)),N],[-hessV(z[:2]),-gamma*np.eye(2)]])
def step(z,h,weighted):
 r=np.exp(gamma*h/2) if weighted else None
 zn=z+h*f(z)
 for _ in range(20):
  m=(zn+z)/2
  if weighted:
   residual=np.r_[zn[:2]-z[:2]-h/2*N@(r*zn[2:]+z[2:]/r),
                  r*zn[2:]-z[2:]/r+h*gradV(m[:2])]
   ap=np.block([[np.eye(2),-h*r*N/2],[h*hessV(m[:2])/2,r*np.eye(2)]])
   am=np.block([[-np.eye(2),-h*N/(2*r)],[h*hessV(m[:2])/2,-np.eye(2)/r]])
  else:
   residual=zn-z-h*f(m)
   ap=np.eye(4)-h*jac(m)/2
   am=-np.eye(4)-h*jac(m)/2
  if np.linalg.norm(residual,np.inf)<4e-15: break
  zn-=np.linalg.solve(ap,residual)
 else: raise RuntimeError('Newton failed')
 return zn,-np.linalg.solve(ap,am),float(np.linalg.norm(residual,np.inf))

Tf=5.
ref=solve_ivp(lambda t,z:f(z),[0,Tf],z0,method='DOP853',rtol=3e-13,atol=3e-15)
ref2=solve_ivp(lambda t,z:f(z),[0,Tf],z0,method='DOP853',rtol=7e-14,atol=1e-15)
if not (ref.success and ref2.success): raise RuntimeError('reference integration failed')
result={'scope':'v10 known-kinetic, full-cosine, proportional-damping example; display-precision coefficients.',
        'nu':np.diag(N).tolist(),'d':d.tolist(),'gamma':gamma,'T':Tf,'initial_state':z0.tolist(),
        'reference_tolerance_refinement_endpoint_difference':float(np.linalg.norm(ref.y[:,-1]-ref2.y[:,-1])),
        'results':[]}
for weighted in [False,True]:
 prev=None
 for h in [.04,.02,.01,.005]:
  z=z0.copy(); mxdef=mxres=0.
  for k in range(round(Tf/h)):
   zn,D,res=step(z,h,weighted)
   mxdef=max(mxdef,float(np.linalg.norm(D.T@J@D-np.exp(-gamma*h)*J,2)))
   mxres=max(mxres,res); z=zn
  err=float(np.linalg.norm(z-ref2.y[:,-1])); order=None if prev is None else float(np.log2(prev/err));prev=err
  row={'method':'weighted_midpoint' if weighted else 'ordinary_midpoint','h':h,'endpoint_error':err,
       'order':order,'max_conformal_defect_spectral_2_norm':mxdef,'max_increment_residual':mxres}
  result['results'].append(row);print(row)
(Path(__file__).resolve().parent/'v10_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
