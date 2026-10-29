"""Engineered air-core loop array; SI units; no measured hardware calibration."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
from scipy.optimize import lsq_linear

MU0_OVER_4PI = 1e-7
INPUT_ORDER = ['Bx','By','Bz','Gxx','Gyy','Gxy','Gxz','Gyz']


def make_array():
    rng = np.random.default_rng(102529)
    directions = rng.normal(size=(12, 3))
    directions /= np.linalg.norm(directions, axis=1)[:, None]
    origin = np.array([0., 0., .1])
    return dict(origin_m=origin.tolist(), centers_m=(origin+.075*directions).tolist(),
                normals=(-directions).tolist(), radius_m=.025, turns=300,
                quadrature_points=256, current_bound_A=2., slew_bound_A_s=20.,
                status='Engineering geometry and ratings; unbuilt and uncalibrated air-core coil benchmark')


def basis(points, config):
    points = np.atleast_2d(points)
    nquad = config['quadrature_points']
    a = (np.arange(nquad)+.5)*2*np.pi/nquad
    out = np.empty((len(points), 3, len(config['centers_m'])))
    for j, (center, normal) in enumerate(zip(config['centers_m'], config['normals'])):
        normal = np.asarray(normal)
        axis = np.eye(3)[np.argmin(np.abs(normal))]
        e1 = np.cross(normal, axis); e1 /= np.linalg.norm(e1)
        e2 = np.cross(normal, e1)
        wire = np.asarray(center)+config['radius_m']*(np.cos(a)[:,None]*e1+np.sin(a)[:,None]*e2)
        dl = config['radius_m']*2*np.pi/nquad*(-np.sin(a)[:,None]*e1+np.cos(a)[:,None]*e2)
        distance = points[:,None,:]-wire[None,:,:]
        denom = np.linalg.norm(distance, axis=2)**3
        if np.any(denom < 1e-15):
            raise ValueError('Evaluation point on or too close to a conductor')
        out[:,:,j] = MU0_OVER_4PI*config['turns']*np.sum(np.cross(dl[None,:,:],distance)/denom[:,:,None],axis=1)
    return out


def local_mapping(config, eps=1e-5):
    origin = np.asarray(config['origin_m'])
    b0 = basis(origin, config)[0]
    grad = np.stack([(basis(origin+eps*np.eye(3)[j],config)[0]-basis(origin-eps*np.eye(3)[j],config)[0])/(2*eps) for j in range(3)],axis=1)
    raw = grad.copy()
    grad = .5*(grad+grad.swapaxes(0,1))
    trace = np.einsum('iia->a',grad)
    grad -= np.eye(3)[:,:,None]*trace[None,None,:]/3
    a = np.vstack([b0,grad[0,0],grad[1,1],grad[0,1],grad[0,2],grad[1,2]])
    defects = dict(raw_divergence_max=float(np.max(np.abs(np.einsum('iia->a',raw)))),
                   raw_curl_max=float(np.max(np.abs(raw-raw.swapaxes(0,1)))))
    return a, defects


def unpack(u):
    u=np.asarray(u)
    g=np.array([[u[3],u[5],u[6]],[u[5],u[4],u[7]],[u[6],u[7],-u[3]-u[4]]])
    return u[:3],g


class CoilAllocator:
    def __init__(self, config=None):
        self.config = make_array() if config is None else config
        self.A,_ = local_mapping(self.config)
        self.scale=np.array([.001]*3+[.03]*5)
        self.currents=np.zeros(self.A.shape[1])
        self.last_time=None

    def allocate(self, requested_u, time_s=None):
        bound=self.config['current_bound_A']
        lo=np.full(self.A.shape[1],-bound); hi=-lo
        if self.last_time is not None and time_s is not None:
            dt=max(0.,float(time_s)-self.last_time)
            if dt==0:
                return self.A@self.currents,self.currents.copy()
            cap=self.config['slew_bound_A_s']*dt
            lo=np.maximum(lo,self.currents-cap);hi=np.minimum(hi,self.currents+cap)
        matrix=np.vstack([self.A/self.scale[:,None],1e-3*np.eye(self.A.shape[1])])
        target=np.r_[np.asarray(requested_u)/self.scale,np.zeros(self.A.shape[1])]
        result=lsq_linear(matrix,target,bounds=(lo,hi),tol=1e-10,lsmr_tol=1e-12,max_iter=100)
        if not result.success:
            raise RuntimeError('Current allocation failed: '+str(result.message))
        self.currents=result.x
        if time_s is not None:self.last_time=float(time_s)
        return self.A@self.currents,self.currents.copy()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=Path('stage2/results/coil'))
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    cfg=make_array();a,defects=local_mapping(cfg)
    rng=np.random.default_rng(102529)
    currents=rng.uniform(-cfg['current_bound_A'],cfg['current_bound_A'],size=(100,12))
    radii=[.001,.003,.005,.01]
    comparison=[]
    for radius in radii:
        directions=rng.normal(size=(100,3));directions/=np.linalg.norm(directions,axis=1)[:,None]
        offsets=radius*directions
        true=np.einsum('pij,pj->pi',basis(np.asarray(cfg['origin_m'])+offsets,cfg),currents)
        affine=[]
        for u,x in zip(currents@a.T,offsets):
            b,g=unpack(u);affine.append(b+g@x)
        error=np.linalg.norm(true-np.asarray(affine),axis=1)
        comparison.append(dict(radius_m=radius,max_abs_T=float(error.max()),rms_abs_T=float(np.sqrt(np.mean(error**2))),
                               relative_l2=float(np.linalg.norm(error)/np.linalg.norm(true))))
    scales=np.array([.001]*3+[.03]*5)
    singular=np.linalg.svd(a/scales[:,None],compute_uv=False)
    summary=dict(input_order=INPUT_ORDER,mapping_units='first 3 T/A; last 5 T/m/A',rank=int(np.linalg.matrix_rank(a/scales[:,None])),
                 scaled_singular_values=singular.tolist(),scaled_condition=float(singular[0]/singular[-1]),
                 maxwell_finite_difference=defects,affine_approximation= comparison,
                 limit='Physical Biot-Savart model with chosen geometry; no manufactured-coil, thermal, mutual-inductance or calibration validation')
    (args.output/'coil_config.json').write_text(json.dumps(cfg,indent=2))
    (args.output/'coil_audit.json').write_text(json.dumps(summary,indent=2))
    np.save(args.output/'field_gradient_per_ampere.npy',a)
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
