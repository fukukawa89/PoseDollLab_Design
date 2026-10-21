import sys,json,numpy as np,trimesh,shutil,traceback,concurrent.futures
from search_revo22_f5_orientation268 import O,put
from build_revo22_fins import solid,vf,md,box,union
from o22_material_components import material_components
from verify_revo22_x062_removal245 import exact_clear
from build_revo22_f5_magnet340 import run as magnet
from audit_revo22_f5_native271 import run as audit
from verify_revo22_f5_geometry292 import run as geo
from verify_revo22_f5_contacts298 import run as fit
from optimize_revo22_f5_276 import pick

def create(p,src,l):
 a=O/'candidates'/p/src;b=O/'candidates'/p/l
 if(b/'parts'/f'{p}.npz').exists():return True
 n=dict(np.load(a/'parts'/f'{p}.npz'));d=json.loads((a/'design'/f'{p}.json').read_text());body=solid(n['v'],n['f']);gg=np.load(a/'verification/guards.npz');full_guard=solid(gg['v'],gg['f'])-body;fin=solid(n['fin_v'],n['fin_f']);ts=solid(n['teeth_v'],n['teeth_f']);mv,mf=vf(fin+ts);mesh=trimesh.Trimesh(mv,mf,process=False);rr=json.loads((a/'verification/native_final.json').read_text());it=json.loads((a/'verification/plate_manifest.json').read_text())['items'][0];M=np.array(it['rotation_matrix']);t=np.array(it['translation_mm']);magnet(p);mg=np.load(O/'guards_magnet'/f'{p}.npz');ban=solid(mg['v'],mg['f']).transform(np.c_[d['f4_to_current_matrix'],d['f4_to_current_translation_mm']]);xy=np.array([[-1,-1,0],[1,-1,0],[1,1,0],[-1,1,0]]);records=[]
 for issue in rr['external_islands']+rr['critical_external_runs']:
  bb=issue['bounds_mm'];pos=(np.array([(bb[0]+bb[2])/2,(bb[1]+bb[3])/2,issue['z_mm']])-t)@M;done=False
  for dz in [.8,1.6,2.4,3.2,4.0,5.2,7.2]:
   sample=pos-[0,0,dz];hit,dist,_=trimesh.proximity.closest_point(mesh,[sample]);root=hit[0];root[2]=max(.12,root[2]-.08)
   if abs(root[2]-sample[2])>1.2 or dist[0]>5.5:continue
   for width in [.8,1.2,1.6,2.0]:
    for zz in [.12,-.05,.3]:
     tip=pos+[0,0,zz];mid=tip-[0,0,.9]
     if mid[2]<=root[2]+.1:continue
     # A narrow stem and gradual small contact pad; no extra fin body.
     pad=union([md.Manifold.hull_points(np.r_[xy*.4+root,xy*.4+mid]),md.Manifold.hull_points(np.r_[xy*.4+mid,xy*(width/2)+tip])]);ov=(pad^body).volume()
     if not .005<ov<4 or (pad^(ban-body)).volume()>1e-6 or(pad^(fin+ts)).volume()<.02 or(pad-body-fin-ts).volume()<1e-4:continue
     good=None
     for dr in [root-tip,np.array([0.,0.,-1.])]+[sign*np.array(d['orientation']['matrix'])[:,axis] for axis in range(3) for sign in [-1.,1.]]+[sign*np.array(d['f4_to_current_matrix'])[:,axis] for axis in range(3) for sign in [-1.,1.]]:
      dr=dr/np.linalg.norm(dr)
      if exact_clear(pad-body,body,dr*220)[0]:good=dr;break
     external_only=(pad^full_guard).volume()<1e-6
     if good is None and not external_only:continue
     if good is None:good=np.array([0.,0.,-1.])
     ts+=pad;records.append(dict(kind='external_cut_contact_409'if external_only else'extractable_void_contact_341',contact_pad=True,target=pos.tolist(),root=root.tolist(),tip=tip.tolist(),neck_xy_mm=[.8,.8],tip_width_mm=width,taper_height_mm=.9,stem_removal_vector=good.tolist(),removal_vector=[0.,0.,-1.],free_vertical_mm=float(tip[2]-root[2]),body_overlap_mm3=float(ov)));done=True;break
    if done:break
   if done:break
  print('CAP409_TARGET',p,pos.tolist(),done,flush=True)
 if not records:return False
 for sub in ['parts','design','verification','projects']:(b/sub).mkdir(parents=True,exist_ok=True)
 n['teeth_v'],n['teeth_f']=vf(ts);np.savez_compressed(b/'parts'/f'{p}.npz',**n);shutil.copy2(a/'verification/guards.npz',b/'verification/guards.npz');mv,mf=vf(ban);np.savez_compressed(b/'verification/strict_magnet_guards.npz',v=mv,f=mf);d.update(trial=l,connector_void_policy='whole_stem_extraction',local_route_repairs=d.get('local_route_repairs',[])+records,new_tooth_count=d['new_tooth_count']+len(records),support_volume_mm3=float((fin+ts).volume()));put(b/'design'/f'{p}.json',d);return True

def run(job):
 p,src=job
 for k in range(3):
  l='cap409_'+str(k)
  if not create(p,src,l):return p,False
  q=audit(p,l)
  if q['native_review_resolved']:
   g=geo(p,l)
   if g['body_change_fit_and_pose_required']:assert fit(p,l)['fit_and_pose_geometry_passed']
   assert pick(p);return p,True
  src=l
 return p,False
if __name__=='__main__':
 jobs=[('P130','ends366_0')]
 with concurrent.futures.ProcessPoolExecutor(max_workers=3)as ex:
  fs={ex.submit(run,j):j for j in jobs}
  for f in concurrent.futures.as_completed(fs):
   try:print('CAP409_RESULT',f.result(),flush=True)
   except Exception:traceback.print_exc();print('CAP409_ERROR',fs[f],flush=True)
