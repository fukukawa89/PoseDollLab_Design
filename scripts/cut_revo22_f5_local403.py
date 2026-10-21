import sys,json,numpy as np,shutil,traceback,concurrent.futures
from search_revo22_f5_orientation268 import O,put
from build_revo22_fins import solid,vf,union,box
from o22_material_components import material_components
from verify_revo22_f5_contacts298 import envelope,run as fit
from verify_revo22_f5_geometry292 import run as geo
from audit_revo22_f5_native271 import run as audit
from optimize_revo22_f5_276 import pick
import repair_revo22_f4_guarded_chamfer as ctx

def create(p,src,label,scale=1.):
 a=O/'candidates'/p/src;b=O/'candidates'/p/label
 if(b/'parts'/f'{p}.npz').exists():return True
 n=dict(np.load(a/'parts'/f'{p}.npz'));d=json.loads((a/'design'/f'{p}.json').read_text());s=solid(n['v'],n['f']);ref=solid(n.get('f5_pre_relief_v',n['v']),n.get('f5_pre_relief_f',n['f']));count=len(material_components(s));r=json.loads((a/'verification/native_final.json').read_text());it=json.loads((a/'verification/plate_manifest.json').read_text())['items'][0];parts,key,T=ctx.context(d,p);Ti=np.linalg.inv(T);records=[]
 for q in r['external_islands']+r['critical_external_runs']:
  bb=q['bounds_mm'];pp=(np.array([(bb[0]+bb[2])/2,(bb[1]+bb[3])/2,q['z_mm']-.1])-it['translation_mm'])@np.array(it['rotation_matrix']);roi=box(pp-[.8*scale,.8*scale,.6],pp+[.8*scale,.8*scale,1.2*scale]);rg=roi.transform(Ti[:3,:]);rb=np.array(rg.bounding_box());protection=[]
  for k,other in parts.items():
   if k==key:continue
   ob=np.array(other.bounding_box());sep=np.maximum(np.maximum(ob[:3]-rb[3:],rb[:3]-ob[3:]),0)
   if np.linalg.norm(sep)>.15:continue
   protection.append(envelope(other,rg,margin=.051))
  safe=(rg-union(protection)).transform(T[:3,:]);delta=s^safe;v=float(delta.volume());proposal=s-safe
  if not 1e-5<v<10 or len(material_components(proposal))!=count:print('CUT403_REJECT',p,v,len(material_components(proposal)),flush=True);continue
  if(ref-proposal).volume()>min(80.,ref.volume()*.006):continue
  s=proposal;records.append(dict(kind='localized_unsupported_edge_trim',local_bounds_mm=list(roi.bounding_box()),removed_volume_mm3=v,actual_neighbor_protection_mm=.051,protection_coordinates='assembly world cube',native_issue=q))
 if not records:return False
 for sub in ['parts','design','verification','projects']:(b/sub).mkdir(parents=True,exist_ok=True)
 n.setdefault('f5_pre_relief_v',n['v'].copy());n.setdefault('f5_pre_relief_f',n['f'].copy());n['v'],n['f']=vf(s);fin=solid(n['fin_v'],n['fin_f']);teeth=solid(n['teeth_v'],n['teeth_f']);teeth=union([t for t in material_components(teeth)if(t^s).volume()>.005 and(t^fin).volume()>.005]);fin=union([f for f in material_components(fin)if(f^teeth).volume()>.005]);n['fin_v'],n['fin_f']=vf(fin);n['teeth_v'],n['teeth_f']=vf(teeth);np.savez_compressed(b/'parts'/f'{p}.npz',**n)
 for fn in ['guards.npz','strict_magnet_guards.npz']:
  if(a/'verification'/fn).exists():shutil.copy2(a/'verification'/fn,b/'verification'/fn)
 d.update(trial=label,part_body_modified_from_F4=True,body_rigid_transform_only=False,f5_reliefs=d.get('f5_reliefs',[])+records,f5_edit_budget_mm3=80.,f5_edit_budget_fraction=.006,fit_and_pose_pending=True,support_count=len(material_components(fin)),support_volume_mm3=float((fin+teeth).volume()));put(b/'design'/f'{p}.json',d);print('CUT403_BUILT',p,label,sum(q['removed_volume_mm3']for q in records),flush=True);return True

def run(job):
 p,src=job
 for i in range(6):
  l='cut403_'+str(i)
  if not create(p,src,l,1.):return p,False
  q=audit(p,l)
  if q['native_review_resolved']:
   geo(p,l);assert fit(p,l)['fit_and_pose_geometry_passed'];assert pick(p);return p,True
  src=l
 return p,False
if __name__=='__main__':
 jobs=[('X038','cut388_0')]
 with concurrent.futures.ProcessPoolExecutor(max_workers=3)as ex:
  fs={ex.submit(run,j):j for j in jobs}
  for f in concurrent.futures.as_completed(fs):
   try:print('CUT403_RESULT',f.result(),flush=True)
   except Exception:traceback.print_exc();print('CUT403_ERROR',fs[f],flush=True)
