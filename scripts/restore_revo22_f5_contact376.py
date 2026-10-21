import sys,json,numpy as np,shutil
from search_revo22_f5_orientation268 import O,OLD,put
from build_revo22_fins import solid,vf,box,union
from verify_revo22_f5_contacts298 import envelope,run as fit
from verify_revo22_f5_geometry292 import run as geo
from optimize_revo22_f5_276 import pick
from audit_revo22_f5_native271 import run as audit
import repair_revo22_f4_guarded_chamfer as ctx
p='P093';a=O/'candidates'/p/'direct372_0';b=O/'candidates'/p/'contact376';n=dict(np.load(a/'parts'/f'{p}.npz'));d=json.loads((a/'design'/f'{p}.json').read_text());o=np.load(OLD/'parts'/f'{p}.npz');ref=solid(o['v'],o['f']).transform(np.c_[d['f4_to_current_matrix'],d['f4_to_current_translation_mm']]);s=solid(n['v'],n['f']);changed=union([box(q['local_bounds_mm'][:3],q['local_bounds_mm'][3:])for q in d.get('f5_reliefs',[])+d.get('f5_additions',[])]);parts,key,T=ctx.context(d,p);Ti=np.linalg.inv(T);s=s.transform(Ti[:3,:]);ref=ref.transform(Ti[:3,:]);changed=changed.transform(Ti[:3,:]);patches=[]
for k,q in parts.items():
 if k==key:continue
 pp=q;bb=np.array(changed.bounding_box());ob=np.array(pp.bounding_box());sep=np.maximum(np.maximum(ob[:3]-bb[3:],bb[:3]-ob[3:]),0)
 if np.linalg.norm(sep)>.25:continue
 z=envelope(pp,changed,margin=.051)
 if z.volume()>1e-7:patches.append(z);print('RESTORE_CONTACT376',k,z.volume(),flush=True)
protect=union(patches);s=((s-protect)+(ref^protect)).transform(T[:3,:])
for sub in ['parts','design','verification','projects']:(b/sub).mkdir(parents=True,exist_ok=True)
n['v'],n['f']=vf(s);np.savez_compressed(b/'parts'/f'{p}.npz',**n);shutil.copy2(a/'verification/guards.npz',b/'verification/guards.npz');shutil.copy2(a/'verification/strict_magnet_guards.npz',b/'verification/strict_magnet_guards.npz');d.update(trial='contact376',contact_zone_restored_mm3=float(protect.volume()));put(b/'design'/f'{p}.json',d)
q=audit(p,'contact376')
if q['native_review_resolved']:
 geo(p,'contact376');assert fit(p,'contact376')['fit_and_pose_geometry_passed'];assert pick(p)
print('CONTACT376_RESULT',p,q['native_review_resolved'],flush=True)
