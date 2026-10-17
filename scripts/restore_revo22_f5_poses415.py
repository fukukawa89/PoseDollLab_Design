import sys,json,numpy as np,shutil
from search_revo22_f5_orientation268 import O,B,OLD,put
from build_revo22_fins import solid,vf,box,union
from verify_revo22_f5_contacts298 import envelope,run as fit
from verify_revo22_f5_geometry292 import run as geo
from audit_revo22_f5_native271 import run as audit
from optimize_revo22_f5_276 import pick
import repair_revo22_f4_guarded_chamfer as ctx
import build_revo22_assembly as assembly
p='X046';src='cap396_0';label='contact415';a=O/'candidates'/p/src;b=O/'candidates'/p/label;d=json.loads((a/'design'/f'{p}.json').read_text());n=dict(np.load(a/'parts'/f'{p}.npz'));old=np.load(OLD/'parts'/f'{p}.npz');parts,key,T=ctx.context(d,p);_,meta,base,*_=ctx.CACHE;Ti=np.linalg.inv(T);ref=solid(old['v'],old['f']).transform(np.c_[d['f4_to_current_matrix'],d['f4_to_current_translation_mm']]).transform(Ti[:3,:]);s=solid(n['v'],n['f']).transform(Ti[:3,:]);roi=union([box(q['local_bounds_mm'][:3],q['local_bounds_mm'][3:])for q in d.get('f5_reliefs',[])+d.get('f5_additions',[])]).transform(Ti[:3,:]);f0,o0=assembly.owners(base);pr=assembly.profile;poses={'base':base,'neutral':pr['neutral_raw_deg'],'default':json.loads((B/'profiles/default_pose.json').read_text())['raw_deg']}
for rawkey,lim in pr['raw_limits_deg'].items():
 for name,val in zip(['min','max'],lim):
  pp=pr['neutral_raw_deg'].copy();pp[rawkey]=val;poses[rawkey+'/'+name]=pp
rng=np.random.default_rng(22)
for i in range(12):poses['combined_'+str(i)]={k:float(rng.uniform(*v))for k,v in pr['raw_limits_deg'].items()}
flags=json.loads((a/'verification/f5_fit_and_pose.json').read_text())['sampled_valid_pose_contact_changes'];seen=set();protect=[]
for row in flags:
 f,o=assembly.owners(poses[row['pose']])
 def transform(k):
  m=meta[k];return f[m['body']]@np.linalg.inv(f0[m['body']])if m['owner']=='rigid_frame'else o[(m['module'],m['owner'])]@np.linalg.inv(o0[(m['module'],m['owner'])])
 rel=np.linalg.inv(transform(key))@transform(row['part']);token=(row['part'],tuple(np.round(rel,8).flat))
 if token in seen:continue
 seen.add(token);env=envelope(parts[row['part']].transform(rel[:3,:]),roi,margin=.052);protect.append(env);print('POSE_RESTORE415',row['part'],row['pose'],float(env.volume()),flush=True)
protected=union(protect);s=((s-protected)+(ref^protected)).transform(T[:3,:])
for sub in ['parts','design','verification','projects']:(b/sub).mkdir(parents=True,exist_ok=True)
n['v'],n['f']=vf(s);np.savez_compressed(b/'parts'/f'{p}.npz',**n)
for fn in ['guards.npz','strict_magnet_guards.npz']:
 if(a/'verification'/fn).exists():shutil.copy2(a/'verification'/fn,b/'verification'/fn)
d.update(trial=label,sampled_pose_contact_regions_restored=True);put(b/'design'/f'{p}.json',d);q=audit(p,label)
if q['native_review_resolved']:
 geo(p,label);assert fit(p,label)['fit_and_pose_geometry_passed'];assert pick(p)
print('POSE_RESTORE415_RESULT',q['native_review_resolved'],flush=True)
