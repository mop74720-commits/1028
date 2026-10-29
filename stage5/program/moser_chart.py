"""Actual 24D auxiliary Moser flow, inverse, state and time sensitivities.

Only the cached polynomial ONE-FORM enters this auxiliary ODE. Its RHS is not a
physical flow oracle. rho^*K_t=K0 and chi=rho^-1. Finite numerical solve errors
are measured explicitly rather than declared exactly symplectic.
"""
import time
import numpy as np
from scipy.integrate import solve_ivp


class MoserChart:
    def __init__(self,cache,order,*,rtol=2e-11,atol=2e-13,max_step=.25,domain_radius=.002):
        self.cache,self.order=cache,order
        self.d=cache.d
        self.rtol,self.atol,self.max_step=rtol,atol,max_step
        self.domain_radius=domain_radius
        self.calls=0;self.nfev=0;self.seconds=0.

    def auxiliary(self,lam,z,t,derivatives=False,second=False):
        a=self.cache.data(z,t,self.order)
        K=self.cache.K0+lam*(a['K']-self.cache.K0)
        v=np.linalg.solve(K,a['b'])
        if not derivatives:return v,K
        Dv=np.linalg.solve(K,a['Db']-lam*np.einsum('ijk,j->ik',a['DK'],v))
        vt=np.linalg.solve(K,a['bt']-lam*a['Kt']@v)
        if second:
            rhs2=a['Hb']-lam*np.einsum('ilj,lk->ijk',a['DK'],Dv)-lam*np.einsum('ilk,lj->ijk',a['DK'],Dv)
            D2v=np.linalg.solve(K,rhs2.reshape(self.d,-1)).reshape(self.d,self.d,self.d)
            Dvt=np.linalg.solve(K,a['Dbt']-lam*np.einsum('ijk,j->ik',a['DKt'],v)-lam*a['Kt']@Dv-lam*np.einsum('ijk,j->ik',a['DK'],vt))
            return v,K,Dv,vt,D2v,Dvt
        return v,K,Dv,vt

    def map(self,x,t,*,inverse=False,sensitivities=True,diagnostics=False,second=False):
        """inverse=False: rho(y)->z; inverse=True: chi(z)->y."""
        started=time.perf_counter();self.calls+=1
        x=np.asarray(x,dtype=float)
        if sensitivities:
            initial=np.r_[x,np.eye(self.d).reshape(-1),np.zeros(self.d)]
            if second:initial=np.r_[initial,np.zeros(self.d**3+self.d**2)]
        else:initial=x
        samples=[];distances=[]
        def rhs(lam,state):
            z=state[:self.d]
            if sensitivities:
                if second:v,K,Dv,vt,D2v,Dvt=self.auxiliary(lam,z,t,True,True)
                else:v,K,Dv,vt=self.auxiliary(lam,z,t,True)
                R=state[self.d:self.d+self.d*self.d].reshape(self.d,self.d)
                offset=self.d+self.d**2
                wt=state[offset:offset+self.d]
                value=np.r_[v,(Dv@R).reshape(-1),Dv@wt+vt]
                if second:
                    offset+=self.d
                    S=state[offset:offset+self.d**3].reshape(self.d,self.d,self.d)
                    W=state[offset+self.d**3:].reshape(self.d,self.d)
                    Sdot=np.einsum('ia,ajk->ijk',Dv,S)+np.einsum('iab,aj,bk->ijk',D2v,R,R,optimize=True)
                    Wdot=Dv@W+np.einsum('iab,aj,b->ij',D2v,R,wt,optimize=True)+Dvt@R
                    value=np.r_[value,Sdot.reshape(-1),Wdot.reshape(-1)]
            else:
                v,K=self.auxiliary(lam,z,t);value=v
            distance=float(np.linalg.norm(z-self.cache.center));distances.append(distance)
            if distance>=self.domain_radius:
                raise ValueError(f'Moser auxiliary path left declared ball: {distance} >= {self.domain_radius}')
            if diagnostics:samples.append(float(np.linalg.svd(K,compute_uv=False)[-1]))
            return value
        sol=solve_ivp(rhs,(1.,0.) if inverse else (0.,1.),initial,method='DOP853',rtol=self.rtol,atol=self.atol,max_step=self.max_step,dense_output=diagnostics)
        if not sol.success:raise RuntimeError(sol.message)
        self.nfev+=sol.nfev;self.seconds+=time.perf_counter()-started
        end=sol.y[:self.d,-1]
        R=sol.y[self.d:self.d+self.d*self.d,-1].reshape(self.d,self.d) if sensitivities else None
        offset=self.d+self.d**2
        wt=sol.y[offset:offset+self.d,-1] if sensitivities else None
        info=dict(nfev=sol.nfev,seconds=time.perf_counter()-started,max_auxiliary_distance=max(distances),
                  rtol=self.rtol,atol=self.atol,max_lambda_step=self.max_step)
        if second:
            offset+=self.d
            info['_second_state_derivative']=sol.y[offset:offset+self.d**3,-1].reshape(self.d,self.d,self.d)
            info['_mixed_time_state_derivative']=sol.y[offset+self.d**3:,-1].reshape(self.d,self.d)
        if diagnostics:
            lamgrid=np.linspace(0,1,17)
            grid_states=sol.sol(lamgrid)[:self.d].T
            grid_sigmas=[float(np.linalg.svd(self.auxiliary(lam,z,t)[1],compute_uv=False)[-1]) for lam,z in zip(lamgrid,grid_states)]
            bounds=self.cache.ball_bounds(t,self.order,self.domain_radius)
            info.update(minimum_solver_stage_Klambda_singular_value=min(samples),lambda_grid=lamgrid.tolist(),lambda_grid_min_singular_values=grid_sigmas,
                        uniform_ball_sufficient_bounds=bounds,
                        sufficient_stay_in_ball=(np.linalg.norm(x-self.cache.center)+bounds['auxiliary_speed_upper_bound']<self.domain_radius) if bounds['auxiliary_speed_upper_bound'] is not None else False)
        return end,R,wt,info

    def transformed_field(self,t,y,represented):
        z,R,rhot,info=self.map(y,t,sensitivities=True)
        return np.linalg.solve(R,represented(t,z)-rhot)

    def transformed_jacobian(self,t,y,represented):
        z,R,rhot,info=self.map(y,t,sensitivities=True,second=True)
        g=np.linalg.solve(R,represented(t,z)-rhot)
        A=represented.jacobian(t,z)
        S=info.pop('_second_state_derivative');W=info.pop('_mixed_time_state_derivative')
        return np.linalg.solve(R,A@R-W-np.einsum('ikj,k->ij',S,g)),info

    def diagnostics(self,z,t):
        y,Dchi,chit,forward=self.map(z,t,inverse=True,sensitivities=True,diagnostics=True)
        restored,Drho,rhot,backward=self.map(y,t,sensitivities=True,diagnostics=True)
        K=self.cache.data(z,t,self.order)['K']
        return dict(time=t,chart_matching_2=float(np.linalg.norm(Dchi.T@self.cache.K0@Dchi-K,2)),
                    inverse_composition_error_2=float(np.linalg.norm(restored-z)),
                    derivative_inverse_error_2=float(np.linalg.norm(Dchi@Drho-np.eye(self.d),2)),
                    time_inverse_error_2=float(np.linalg.norm(chit+Dchi@rhot)),
                    chart_condition=float(np.linalg.cond(Dchi)),chart_time_derivative_norm=float(np.linalg.norm(chit)),
                    chi=forward,rho=backward)
