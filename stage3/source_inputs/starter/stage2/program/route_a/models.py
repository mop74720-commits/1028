"""Declared high-dimensional mathematical tests, not a calibrated catheter ROM.

The physical coordinates have nonlinear configuration-dependent mass. Two
cosine magnetic-potential ports are retained in every nonlinear test. A known
point transformation is an explicit model assumption, never inferred from a
numerical trajectory. It makes geometry and structural limitations testable.
"""
from dataclasses import dataclass
import numpy as np


@dataclass
class MechanicalTest:
    n: int
    family: str
    a: float = .15
    b: float = .07

    def __post_init__(self):
        n = self.n
        self.eye = np.eye(n)
        self.J = np.block([[np.zeros((n,n)), self.eye], [-self.eye, np.zeros((n,n))]])
        self.K0 = -self.J
        self.I2 = np.eye(2*n)
        half = n//2
        self.M0 = np.diag(1.0+.045*np.arange(n))
        self.Ks = np.diag(1.0+.11*np.arange(n))
        for sl in [slice(0,half), slice(half,n)]:
            self.M0[sl,sl] += .07*np.ones((half,half))/half
            self.Ks[sl,sl] += .09*np.ones((half,half))/half
        self.rates = np.r_[np.full(half,.08), np.full(half,.21)]
        self.C0 = self.M0@np.diag(self.rates)
        self.quartic = .16
        self.d = np.zeros((2,n))
        self.d[0,:half] = np.linspace(.8,1.2,half)
        self.d[1,half:] = np.linspace(1.2,.8,half)
        self.d /= np.linalg.norm(self.d,axis=1)[:,None]
        self.d *= 1.5
        self.phase = np.array([.35,-.45])
        self.current_bias = np.array([.18,.14])
        self.current_gain = np.array([.12,.09])
        self.port_target = np.array([.8,.85])
        if self.family == "conservative":
            self.C0[:] = 0.
        elif self.family == "generic_nonproportional":
            r = np.linspace(.7,1.3,n); r /= np.linalg.norm(r)
            self.C0 += .13*np.outer(r,r)
            self.Ks += .12*np.outer(r,r)
            self.d[0] = 1.5*np.cos(.4*np.arange(n)); self.d[0] /= np.linalg.norm(self.d[0])/1.5
            self.d[1] = 1.5*np.sin(.5*np.arange(n)+.2); self.d[1] /= np.linalg.norm(self.d[1])/1.5
        elif self.family == "linear_known_chart":
            r = np.linspace(.7,1.3,n); r /= np.linalg.norm(r)
            self.M0 += .09*np.outer(r,r)
            self.Ks += .14*np.outer(r,r)
            self.C0 = np.diag(np.linspace(.08,.25,n))+.06*np.outer(r,r)
            self.quartic = 0.
            self.current_bias[:] = 0.
            self.current_gain[:] = 0.
        elif self.family != "block_weighted":
            raise ValueError(self.family)
        self.Mi = np.linalg.solve(self.M0,self.eye)
        self.A = np.block([[np.zeros((n,n)),self.Mi],[-self.Ks,-self.C0@self.Mi]])
        self.z0 = np.r_[.12*np.cos(.7*np.arange(n)),.04*np.sin(.9*np.arange(n)+.1)]

    def point(self,q):
        out=q+self.a*q**3
        out=out.copy(); out[1:]+=self.b*q[:-1]**2
        return out

    def point_D(self,q):
        return np.diag(1+3*self.a*q*q)+np.diag(2*self.b*q[:-1],-1)

    def point_W(self,q):
        # Column i is d(DQ)/dq_i applied to the i-th coordinate basis.
        return np.diag(6*self.a*q)+np.diag(np.full(self.n-1,2*self.b),-1)

    def chart(self,z,derivative=False):
        n=self.n; q,p=z[:n],z[n:]
        D=self.point_D(q)
        P=np.linalg.solve(D.T,p)
        y=np.r_[self.point(q),P]
        if not derivative:
            return y
        DiT=np.linalg.solve(D.T,self.eye)
        c=self.point_W(q).T@P
        E=np.block([[D,np.zeros((n,n))],[-DiT@np.diag(c),DiT]])
        return y,E

    def inverse_chart(self,y):
        n=self.n; q=np.empty(n); maximum_residual=0.; iterations=0
        for i in range(n):
            target=y[i]-(self.b*q[i-1]**2 if i else 0.)
            x=float(target)
            for k in range(30):
                residual=x+self.a*x**3-target
                if abs(residual)<3e-15:
                    break
                x-=residual/(1+3*self.a*x*x)
            else:
                raise RuntimeError("Point inverse failed")
            q[i]=x; maximum_residual=max(maximum_residual,abs(residual)); iterations+=k
        z=np.r_[q,self.point_D(q).T@y[n:]]
        return z,{"inverse_coordinate_residual_inf":maximum_residual,"inverse_Newton_corrections":iterations}

    def potential(self,Q,derivatives=2, frozen_current=None):
        s=self.d@Q+self.phase; cs=np.cos(s); sn=np.sin(s)
        if frozen_current is None:
            currents=self.current_bias-self.current_gain*(cs-self.port_target)
            value=-self.current_bias@cs+.5*np.sum(self.current_gain*(cs-self.port_target)**2)
            wp=currents*sn
            wpp=currents*cs+self.current_gain*sn**2
            wppp=-currents*sn+3*self.current_gain*sn*cs
            wpppp=-currents*cs+self.current_gain*(3*cs**2-4*sn**2)
        else:
            currents=frozen_current
            value=-currents@cs; wp=currents*sn; wpp=currents*cs
            wppp=-currents*sn; wpppp=-currents*cs
        value += .5*Q@self.Ks@Q+self.quartic*np.sum(Q**4)/4
        grad=self.Ks@Q+self.quartic*Q**3+self.d.T@wp
        hess=self.Ks+np.diag(3*self.quartic*Q**2)+(self.d.T*wpp)@self.d
        return value,grad,hess,(wppp,wpppp)

    def currents(self,Q):
        return self.current_bias-self.current_gain*(np.cos(self.d@Q+self.phase)-self.port_target)

    def current_jacobian(self,Q):
        return (self.current_gain*np.sin(self.d@Q+self.phase))[:,None]*self.d

    def port_force(self,Q):
        return -self.d.T*np.sin(self.d@Q+self.phase)

    def latent_field(self,y,conservative=False,frozen_current=None):
        n=self.n; Q,P=y[:n],y[n:]; v=self.Mi@P
        g=self.potential(Q,frozen_current=frozen_current)[1]
        return np.r_[v,-g-(0 if conservative else self.C0@v)]

    def latent_jac(self,y,conservative=False,frozen_current=None):
        A=self.potential(y[:self.n],frozen_current=frozen_current)[2]
        return np.block([[np.zeros((self.n,self.n)),self.Mi],[-A,np.zeros((self.n,self.n)) if conservative else -self.C0@self.Mi]])

    def field(self,z):
        n=self.n; q,p=z[:n],z[n:]
        D=self.point_D(q); W=self.point_W(q)
        P=np.linalg.solve(D.T,p); u=self.Mi@P; v=np.linalg.solve(D,u)
        g=self.potential(self.point(q))[1]
        w=-g-self.C0@u; c=W.T@P
        return np.r_[v,D.T@w+c*v]

    def jac(self,z):
        n=self.n; q,p=z[:n],z[n:]
        D=self.point_D(q); W=self.point_W(q)
        DTinv=np.linalg.solve(D.T,self.eye)
        P=DTinv@p; u=self.Mi@P; v=np.linalg.solve(D,u)
        _,g,A,_=self.potential(self.point(q))
        w=-g-self.C0@u; c=W.T@P
        Pq=-DTinv@np.diag(c); Pp=DTinv
        uq=self.Mi@Pq; up=self.Mi@Pp
        vq=np.linalg.solve(D,uq-W@np.diag(v)); vp=np.linalg.solve(D,up)
        cq=W.T@Pq+np.diag(6*self.a*P); cp=W.T@Pp
        pq=np.diag(W.T@w)+D.T@(-A@D-self.C0@uq)+np.diag(v)@cq+np.diag(c)@vq
        pp=-D.T@self.C0@up+np.diag(v)@cp+np.diag(c)@vp
        return np.block([[vq,vp],[pq,pp]])

    def mass(self,q):
        D=self.point_D(q); return D.T@self.M0@D

    def damping(self,q):
        D=self.point_D(q); return D.T@self.C0@D

    def energy(self,z):
        y=self.chart(z); return .5*y[self.n:]@self.Mi@y[self.n:]+self.potential(y[:self.n])[0]

    def central4(self,y,h,derivative=False):
        if np.any(self.C0):
            raise ValueError("Autonomous Central4 only for conservative case")
        n=self.n; Q,P=y[:n],y[n:]; v=self.Mi@P
        _,g,A,(w3,w4)=self.potential(Q)
        dv=self.d@v
        t3vv=6*self.quartic*Q*v*v+self.d.T@(w3*dv**2)
        corr=np.r_[2*self.Mi@A@v,-t3vv-2*A@self.Mi@g]
        inc=h*np.r_[v,-g]+h**3/24*corr
        if not derivative:
            return inc
        t3v=np.diag(6*self.quartic*Q*v)+(self.d.T*(w3*dv))@self.d
        t4vv=np.diag(6*self.quartic*v*v)+(self.d.T*(w4*dv**2))@self.d
        u=self.Mi@g
        t3u=np.diag(6*self.quartic*Q*u)+(self.d.T*(w3*(self.d@u)))@self.d
        dc=np.block([[2*self.Mi@t3v,2*self.Mi@A@self.Mi],[-t4vv-2*t3u-2*A@self.Mi@A,-2*t3v@self.Mi]])
        return h*self.latent_jac(y,conservative=True)+h**3/24*dc

    def parameters(self):
        cscale=np.sum(self.C0*self.M0)/np.sum(self.M0*self.M0)
        return {"n_coordinates":self.n,"phase_dimension":2*self.n,"family":self.family,
                "M0":self.M0,"C0":self.C0,"Ks":self.Ks,"point_cubic_a":self.a,"point_lower_coupling_b":self.b,
                "quartic_coefficient":self.quartic,"magnetic_port_d":self.d,"phase":self.phase,
                "current_bias":self.current_bias,"current_gain":self.current_gain,"port_target":self.port_target,
                "C_best_scalar_M":cscale,"C_nonproportional_residual_Frobenius":np.linalg.norm(self.C0-cscale*self.M0),
                "minimum_C0_eigenvalue":np.linalg.eigvalsh(self.C0)[0],
                "units":"All parameters dimensionless mathematical test values; two cosine potential ports, no hardware calibration.",
                "point_chart":"Q_i=q_i+a*q_i^3+b*q_(i-1)^2 (predecessor term absent for i=0); P=DQ^(-T)*p",
                "mass_damping":"M(q)=DQ.T*M0*DQ; C(q)=DQ.T*C0*DQ; complete geometric inertia retained"}


def complex_jac(function,z,eps=1e-25):
    return np.column_stack([np.imag(function(z.astype(complex)+1j*eps*np.eye(len(z))[j]))/eps for j in range(len(z))])
