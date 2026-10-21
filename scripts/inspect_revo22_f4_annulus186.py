from pathlib import Path
import sys,json,numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,vf,md
from repair_revo22_f4_guarded_chamfer import context
from o22_reference_mesh import reference_solid
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
for spec in sys.argv[1:]:
 pid,label,washerkey=spec.split(':');p=O/'candidates'/pid/label;n=np.load(p/'parts'/f'{pid}.npz');d=json.loads((p/'design'/f'{pid}.json').read_text());parts,key,T=context(d,pid);washer=parts[washerkey];v=vf(washer)[0];center=v.mean(0);eig,Q=np.linalg.eigh(np.cov((v-center).T));axis=Q[:,0];u=Q[:,1];A=np.array([u,np.cross(axis,u),axis]);H=np.eye(4);H[:3,:]=np.c_[A,-A@center];old=reference_solid(n,d).transform((H@np.linalg.inv(T))[:3,:]);new=solid(n['v'],n['f']).transform((H@np.linalg.inv(T))[:3,:]);w=washer.transform(H[:3,:]);wb=w.bounding_box();outer=max(np.linalg.norm(vf(w)[0][:,:2],axis=1));inner=min(np.linalg.norm(vf(w)[0][:,:2],axis=1));rows=[]
 for face in [wb[2]-.002,wb[5]+.002]:
  z0=face-1 if face<wb[2]else face;options=[]
  for rin in np.arange(inner+.15,outer-1.,.1):
   for rout in np.arange(rin+1.,outer-.1,.1):
    ring=(md.Manifold.cylinder(1.,rout,rout,160)-md.Manifold.cylinder(1.02,rin,rin,160).translate([0,0,-.01])).translate([0,0,z0]);missingold=float((ring-old).volume());missingnew=float((ring-new).volume());lost=float(((old-new)^ring).volume())
    if missingold<1e-5 and missingnew<1e-5:options.append({'inner_radius_mm':rin,'outer_radius_mm':rout,'width_mm':rout-rin,'depth_mm':1.,'lost_volume_mm3':lost,'original_void_mm3':missingold,'new_void_mm3':missingnew})
  options.sort(key=lambda v:(-v['width_mm'],-v['outer_radius_mm']));rows.append({'face_z':face,'options':options[:3]})
 out={'id':pid,'label':label,'washer':washerkey,'washer_inner_radius_mm':inner,'washer_outer_radius_mm':outer,'read_only_measurement_no_qualification_changed':True,'faces':rows};(p/'verification/continuous_washer_backing186.json').write_text(json.dumps(out,indent=2));print(json.dumps(out),flush=True)
