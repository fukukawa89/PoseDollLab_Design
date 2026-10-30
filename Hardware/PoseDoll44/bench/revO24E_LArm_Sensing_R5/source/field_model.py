"""Numerical surface-charge model of uniform diametric cylinders; NOT a steel FEA."""
from common import *
from design import channels,named_poses,GAP_SHIFT

ph=(np.arange(128)+.5)*2*np.pi/128
zz=(np.arange(20)+.5)*2.5/20-1.25
phi,z=np.meshgrid(ph,zz)
surf=np.array([3*np.cos(phi).ravel(),3*np.sin(phi).ravel(),z.ravel()]).T
weight=(np.cos(phi)*3*(2*np.pi/128)*(2.5/20)).ravel()

def B(point,C,Br=1.3):
    point=np.asarray(point);local=(point-C[:3,3])@C[:3,:3]
    d=local[...,None,:]-surf
    out=Br*1000/(4*np.pi)*np.sum(d*weight[:,None]/np.linalg.norm(d,axis=-1)[...,None]**3,axis=-2)
    return out@C[:3,:3].T

def geometry(q):
    ff=frames(q);ans=[]
    for c in channels():
        A=ff[c['pcb_frame']]@np.linalg.inv(F0[c['pcb_frame']])@c['A']
        M=ff[c['magnet_frame']]@np.linalg.inv(F0[c['magnet_frame']])@c['mag_A']
        M=M@T([0,0,.25 if c['id']=='WD' else 1.75])
        pos=(A@np.array([0,0,.4 if c['id']=='WD' else 4.6+GAP_SHIFT,1]))[:3]
        ans.append((c['id'],A,M,pos))
    return ans

def run():
    cs=geometry({});rows=[]
    for name,A,M,p in cs:
        b=B(p,M);other=sum((B(p,m) for n,a,m,pt in cs if n!=name),start=np.zeros(3))
        rows.append(dict(id=name,own_mT=np.round(A[:3,:3].T@b,4).tolist(),stray_mT=float(np.linalg.norm(other))))
    wd=[]
    for q in np.linspace(-20,30,201):
        gg=geometry({'l_wrist_deviation':float(q)});n,A,M,p=gg[-1]
        b=B(p,M)@A[:3,:3];wd.append([float(q),*b.tolist()])
    v=np.array(wd);slope=np.linalg.norm(np.gradient(v[:,1:],v[:,0],axis=0),axis=1)
    phase_min=[]
    for phase in np.arange(0,360,15):
        vv=[]
        for angle in np.linspace(-20,30,51):
            n,A,M,p=geometry({'l_wrist_deviation':float(angle)})[-1];vv.append(B(p,M@rot([0,0,1],float(phase)))@A[:3,:3])
        phase_min.append(float(np.linalg.norm(np.gradient(vv,axis=0),axis=1).min()))
    worst={c['id']:dict(error_deg=0,pose='') for c in channels()};max_wd_stray=0
    for pose,q in named_poses():
        gg=geometry(q);points=np.array([x[3] for x in gg]);field=sum((B(points,x[2]) for x in gg),start=np.zeros_like(points))
        for i,c in enumerate(channels()[:-1]):
            ref=geometry({c['axis']:q.get(c['axis'],0)});rp=ref[i][3];rb=sum((B(rp,x[2]) for x in ref),start=np.zeros(3))@ref[i][1][:3,:3];b=field[i]@gg[i][1][:3,:3]
            err=abs((np.rad2deg(np.arctan2(b[1],b[0])-np.arctan2(rb[1],rb[0]))+180)%360-180)
            if err>worst[c['id']]['error_deg']:worst[c['id']]=dict(error_deg=float(err),pose=pose)
        wd_i=len(gg)-1;own=B(points[wd_i],gg[wd_i][2]);stray=np.linalg.norm(field[wd_i]-own);max_wd_stray=max(max_wd_stray,float(stray))
    result=dict(status='ANALYTICAL_DESIGN_CHECK_NOT_HARDWARE_QUALIFICATION',Br_assumption_T=1.3,method='uniform cylinder side-surface magnetic charge, 128 circumferential x 20 axial samples',limitations=['Steel screws, magnet grade, package Hall die location, printing errors and cables are not modeled.','Use actual full-assembly forward/reverse calibration; no synthetic curve is released as usable calibration.'],neutral=rows,WD_min_sensitivity_mT_per_deg=float(slope.min()),WD_min_sensitivity_all_magnet_clocks_mT_per_deg=min(phase_min),WD_max_abs_component_mT=float(abs(v[:,1:]).max()),WD_max_stray_norm_mT=max_wd_stray,MT_other_joint_coupling_model=worst,WD_LUT_model_only=wd)
    put(OUT/'verification/magnetic_model.json',result)
    print(json.dumps({k:r for k,r in result.items() if k!='WD_LUT_model_only'},ensure_ascii=False),flush=True)

if __name__=='__main__':run()
