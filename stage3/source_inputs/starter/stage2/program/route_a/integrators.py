"""Route-A methods with explicit validity domains and measured preparation."""
import numpy as np
from scipy.linalg import expm, sqrtm, solve_sylvester

TOLERANCE = 2e-14

def newton(residual,jacobian,predictor):
    x=predictor.copy()
    for k in range(16):
        r=residual(x); rn=float(np.linalg.norm(r,np.inf))
        if rn<=TOLERANCE:
            return x,{"increment_residual_inf":rn,"Newton_corrections":k}
        x-=np.linalg.solve(jacobian(x),r)
    raise RuntimeError("Newton increment residual did not converge")

def midpoint(x,h,field,jacobian,diagnostics):
    eye=np.eye(len(x))
    residual=lambda u:u-x-h*field((u+x)/2)
    derivative=lambda u:eye-h*jacobian((u+x)/2)/2
    xn,stats=newton(residual,derivative,x+h*field(x))
    tangent=None
    if diagnostics:
        B=h*jacobian((x+xn)/2)/2
        tangent=np.linalg.solve(eye-B,eye+B)
        stats["minimum_Newton_singular_value"]=float(np.linalg.svd(eye-B,compute_uv=False)[-1])
    return xn,tangent,stats

def central4(model,x,h,diagnostics):
    eye=np.eye(len(x))
    inc=lambda u:model.central4(u,h)
    derivative=lambda u:eye-model.central4((u+x)/2,h,True)/2
    xn,stats=newton(lambda u:u-x-inc((u+x)/2),derivative,x+inc(x))
    tangent=None
    if diagnostics:
        B=model.central4((x+xn)/2,h,True)/2
        tangent=np.linalg.solve(eye-B,eye+B)
        stats["minimum_Newton_singular_value"]=float(np.linalg.svd(eye-B,compute_uv=False)[-1])
    return xn,tangent,stats

def gauss4(model,y,h,diagnostics):
    d=len(y); eye=np.eye(d)
    aa=np.array([[.25,.25-np.sqrt(3)/6],[.25+np.sqrt(3)/6,.25]])
    cc=aa.sum(axis=1)
    def values(v):
        yy=v.reshape(2,d)
        return yy,np.array([model.latent_field(x) for x in yy])
    def residual(v):
        yy,ff=values(v); return (yy-y-h*aa@ff).reshape(-1)
    def derivative(v):
        yy=v.reshape(2,d); jj=[model.latent_jac(x) for x in yy]
        return np.block([[(eye if i==j else np.zeros((d,d)))-h*aa[i,j]*jj[j] for j in range(2)] for i in range(2)])
    guess=np.array([y+c*h*model.latent_field(y) for c in cc]).reshape(-1)
    stages,stats=newton(residual,derivative,guess)
    stats["stage_increment_residual_inf"]=stats.pop("increment_residual_inf")
    yy,ff=values(stages); yn=y+h*np.sum(ff,axis=0)/2
    tangent=None
    if diagnostics:
        mat=derivative(stages)
        dy=np.linalg.solve(mat,np.vstack([eye,eye])).reshape(2,d,d)
        tangent=eye+h*sum(model.latent_jac(yy[i])@dy[i] for i in range(2))/2
        stats["minimum_Newton_singular_value"]=float(np.linalg.svd(mat,compute_uv=False)[-1])
    return yn,tangent,stats

def weighted_gauss4(model,y,h,diagnostics):
    """Gauss RK on the known NONAUTONOMOUS canonical chart, not frozen Central4.

    The local time origin is reset only through the declared block scaling.
    E(t) commutes with the block mass, and potential terms do not cross rate
    blocks. These are essential assumptions, checked by the test definition.
    """
    if model.family!="block_weighted":
        raise ValueError("Known weighted Hamiltonian required")
    n=model.n; d=2*n; eye=np.eye(d)
    aa=np.array([[.25,.25-np.sqrt(3)/6],[.25+np.sqrt(3)/6,.25]])
    cc=aa.sum(axis=1)
    scales=[np.exp(model.rates*c*h) for c in cc]
    def field(u,j):
        E=scales[j]
        return np.r_[(model.Mi@u[n:])/E,-E*model.potential(u[:n])[1]]
    def jacobian(u,j):
        E=scales[j]; H=model.potential(u[:n])[2]
        return np.block([[np.zeros((n,n)),model.Mi/E[:,None]],[-E[:,None]*H,np.zeros((n,n))]])
    def residual(v):
        yy=v.reshape(2,d); ff=np.array([field(yy[j],j) for j in range(2)])
        return (yy-y-h*aa@ff).reshape(-1)
    def derivative(v):
        yy=v.reshape(2,d); jj=[jacobian(yy[j],j) for j in range(2)]
        return np.block([[(eye if i==j else np.zeros((d,d)))-h*aa[i,j]*jj[j] for j in range(2)] for i in range(2)])
    guess=np.array([y+c*h*model.latent_field(y,True) for c in cc]).reshape(-1)
    stages,stats=newton(residual,derivative,guess)
    stats["stage_increment_residual_inf"]=stats.pop("increment_residual_inf")
    yy=stages.reshape(2,d)
    un=y+h*sum(field(yy[j],j) for j in range(2))/2
    pullback=np.diag(np.r_[np.ones(n),np.exp(-model.rates*h)])
    yn=pullback@un; tangent=None
    if diagnostics:
        mat=derivative(stages)
        dy=np.linalg.solve(mat,np.vstack([eye,eye])).reshape(2,d,d)
        tangent=pullback@(eye+h*sum(jacobian(yy[i],i)@dy[i] for i in range(2))/2)
        stats["minimum_Newton_singular_value"]=float(np.linalg.svd(mat,compute_uv=False)[-1])
    return yn,tangent,stats

def prepare(model,method,h,duration,diagnostics=False):
    data={"required_operations":{"expm":0,"sqrtm":0,"Sylvester":0,"scalar_exponentials":0}}
    n=model.n; d=2*n
    if method in ["weighted_chart_midpoint","frozen_current_weighted"]:
        if model.family!="block_weighted":
            raise ValueError("Block weighted structure requires declared block separability")
        data["scale"]=np.diag(np.r_[np.ones(n),np.exp(-model.rates*h/2)])
        data["required_operations"]["scalar_exponentials"]=n
    elif method=="damping_split_midpoint":
        data["scale"]=np.block([[np.eye(n),np.zeros((n,n))],[np.zeros((n,n)),expm(-h/2*model.C0@model.Mi)]])
        data["required_operations"]["expm"]=1
    elif method=="matrix_chart_midpoint":
        if model.family!="linear_known_chart":
            raise ValueError("Matrix-exponential structure only for declared linear conjugacy")
        count=round(duration/h); K0=model.K0; A=model.A; eye=np.eye(d)
        checks={"max_chart_congruence_spectral2":0.,"max_transformed_hamiltonian_spectral2":0.,
                "min_chart_singular_value":np.inf,"max_sqrt_imaginary_part":0.,
                "max_Sylvester_residual_inf":0.,"max_Cayley_residual_inf":0.,"max_chart_update_residual_inf":0.}
        def chart(t,generator=False):
            invflow=expm(-A*t); data["required_operations"]["expm"]+=1
            K=invflow.T@K0@invflow
            BB=np.linalg.solve(K0,K); root=sqrtm(BB)
            data["required_operations"]["sqrtm"]+=1
            imag=float(np.max(np.abs(np.imag(root))))
            if imag>1e-9:
                raise ValueError("No tested real principal square-root chart")
            T=np.asarray(root.real,dtype=float)
            if diagnostics:
                checks["max_chart_congruence_spectral2"]=max(checks["max_chart_congruence_spectral2"],float(np.linalg.norm(T.T@K0@T-K,2)))
                checks["max_sqrt_imaginary_part"]=max(checks["max_sqrt_imaginary_part"],imag)
                checks["min_chart_singular_value"]=min(checks["min_chart_singular_value"],float(np.linalg.svd(T,compute_uv=False)[-1]))
            if not generator:
                return T
            Kdot=-A.T@K-K@A
            Bdot=np.linalg.solve(K0,Kdot)
            Tdot=solve_sylvester(T,T,Bdot); data["required_operations"]["Sylvester"]+=1
            Ti=np.linalg.solve(T,eye); L=Tdot@Ti+T@A@Ti
            if diagnostics:
                checks["max_transformed_hamiltonian_spectral2"]=max(checks["max_transformed_hamiltonian_spectral2"],float(np.linalg.norm(L.T@K0+K0@L,2)))
                checks["max_Sylvester_residual_inf"]=max(checks["max_Sylvester_residual_inf"],float(np.linalg.norm(T@Tdot+Tdot@T-Bdot,np.inf)))
            return T,L
        edges=[chart(k*h) for k in range(count+1)]
        maps=[]; stages=[]
        for k in range(count):
            _,L=chart((k+.5)*h,True)
            cayley=np.linalg.solve(eye-h*L/2,eye+h*L/2)
            update=np.linalg.solve(edges[k+1],cayley@edges[k])
            maps.append(update); stages.append((edges[k],edges[k+1],L))
            if diagnostics:
                checks["max_Cayley_residual_inf"]=max(checks["max_Cayley_residual_inf"],float(np.linalg.norm((eye-h*L/2)@cayley-(eye+h*L/2),np.inf)))
                checks["max_chart_update_residual_inf"]=max(checks["max_chart_update_residual_inf"],float(np.linalg.norm(edges[k+1]@update-cayley@edges[k],np.inf)))
        data.update(maps=maps,chart_checks=checks,chart_stages=stages)
    return data

def step(model,method,z,k,h,data,diagnostics=True):
    n=model.n
    if method=="ordinary_midpoint_eq36":
        return midpoint(z,h,model.field,model.jac,diagnostics)
    y,E=model.chart(z,True) if diagnostics else (model.chart(z),None)
    if method=="canonical_chart_midpoint":
        yn,Dy,stats=midpoint(y,h,model.latent_field,model.latent_jac,diagnostics)
    elif method=="canonical_chart_central4":
        yn,Dy,stats=central4(model,y,h,diagnostics)
    elif method=="gauss4_chart":
        yn,Dy,stats=gauss4(model,y,h,diagnostics)
    elif method=="weighted_chart_gauss4":
        yn,Dy,stats=weighted_gauss4(model,y,h,diagnostics)
    elif method in ["weighted_chart_midpoint","damping_split_midpoint","frozen_current_weighted"]:
        S=data["scale"]; u=S@y
        frozen=model.currents(y[:n]) if method=="frozen_current_weighted" else None
        field=lambda x:model.latent_field(x,True,frozen)
        jac=lambda x:model.latent_jac(x,True,frozen)
        un,Du,stats=midpoint(u,h,field,jac,diagnostics)
        yn=S@un; Dy=None if not diagnostics else S@Du@S
        if diagnostics and frozen is not None:
            mid=(u+un)/2
            Fi=np.vstack([np.zeros((n,2)),model.port_force(mid[:n])])
            ki=np.hstack([model.current_jacobian(y[:n]),np.zeros((2,n))])
            extra=np.linalg.solve(model.I2-h*jac(mid)/2,h*Fi@ki)
            Dy += S@extra
    elif method=="matrix_chart_midpoint":
        Dy=data["maps"][k]; yn=Dy@y
        stats={"increment_residual_inf":None,"Newton_corrections":None}
    else:
        raise ValueError(method)
    zn,inverse_stats=model.inverse_chart(yn)
    if diagnostics:
        stats.update(inverse_stats)
        stats["inverse_coordinate_total_residual_inf"]=float(np.linalg.norm(model.chart(zn)-yn,np.inf))
        if method=="matrix_chart_midpoint":
            T0,T1,L=data["chart_stages"][k]
            u0=T0@y; u1=T1@model.chart(zn)
            stats["linear_chart_increment_residual_inf"]=float(np.linalg.norm(u1-u0-h*L@((u0+u1)/2),np.inf))
        _,En=model.chart(zn,True)
        D=np.linalg.solve(En,Dy@E)
    else:
        D=None
    return zn,D,stats
