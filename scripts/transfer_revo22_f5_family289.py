"""Transfer a verified fin design between proven congruent bodies, preserving every body mesh."""
import sys,json,copy,shutil,concurrent.futures,numpy as np
from search_revo22_f5_orientation268 import O,OLD,put
from build_revo22_fins import solid,vf,union,md,box
from o22_material_components import material_components
from route_revo22_x062244 import tooth
from build_revo22_f5_precise_guards283 import run as guards
from audit_revo22_f5_native271 import run as audit
from optimize_revo22_f5_276 import pick
from group_revo22_f5_rigid286 import info
import itertools

def fit(a,b,sign=1):
 for sig in itertools.product([-1,1],repeat=3):
  Q=b['U']@np.diag(sig)@a['U'].T
  if np.linalg.det(Q)*sign<0:continue
  off=b['center']-Q@a['center'];s=a['solid'].transform(np.c_[Q,off]);err=float(abs((s-b['solid']).volume())+abs((b['solid']-s).volume()))
  if err<1e-4:return Q,off,err
 raise ValueError((a['id'],b['id'],'not materially congruent'))
def build(pid,ref='X001'):
 if pid==ref:return
 label='family_'+ref
 if (O/'candidates'/pid/label/'parts'/f'{pid}.npz').exists():return label
 a=info(pid);b=info(ref)
 try:Q,t,err=fit(a,b,1);S=np.eye(3)
 except ValueError:Q,t,err=fit(a,b,-1);S=np.diag([-1.,1.,1.])
 sel=json.loads((O/'selections'/f'{ref}.json').read_text());src=O/'candidates'/ref/sel['label'];d=json.loads((src/'design'/f'{ref}.json').read_text());rn=np.load(src/'parts'/f'{ref}.npz');old=json.loads((OLD/'design'/f'{pid}.json').read_text());Q2=S@np.array(d['f4_to_current_matrix'])@Q;t2=S@(np.array(d['f4_to_current_matrix'])@t+np.array(d['f4_to_current_translation_mm']));assert np.linalg.det(Q2)>.999999
 label='family_'+ref;dst=O/'candidates'/pid/label
 for sub in['parts','design','verification','projects']:(dst/sub).mkdir(parents=True,exist_ok=True)
 n=dict(a['n']);n['f4_print_v']=n['v'].copy();n['v']=n['v']@Q2.T+t2
 if d.get('part_body_modified_from_F4',False):
  cert=json.loads((src/'verification/f5_fit_and_pose.json').read_text());assert cert['fit_and_pose_geometry_passed']
  base=solid(b['n']['v'],b['n']['f']).transform(np.c_[d['f4_to_current_matrix'],d['f4_to_current_translation_mm']]);before=solid(n['v'],n['f']);n['f5_pre_relief_v']=n['v'].copy();n['f5_pre_relief_f']=n['f'].copy();rois=union([box(x['local_bounds_mm'][:3],x['local_bounds_mm'][3:])for x in d.get('f5_reliefs',[])+d.get('f5_additions',[])]);delta=union(material_components((base-solid(rn['v'],rn['f']))^rois)).transform(np.c_[S,[0,0,0]]);extra=union(material_components((solid(rn['v'],rn['f'])-base)^rois)).transform(np.c_[S,[0,0,0]]);n['v'],n['f']=vf((before-delta)+extra)
  for rec in d.get('f5_reliefs',[])+d.get('f5_additions',[]):
   bb=np.array(rec['local_bounds_mm']);corn=np.array([[x,y,z]for x in bb[[0,3]]for y in bb[[1,4]]for z in bb[[2,5]]])@S.T;rec['local_bounds_mm']=np.r_[corn.min(0),corn.max(0)].tolist()
  d['f5_removed_volume_mm3']=float((before-solid(n['v'],n['f'])).volume());d['f5_added_volume_mm3']=float((solid(n['v'],n['f'])-before).volume());d['fit_and_pose_pending']=True
 for vk,fk in[('fin_v','fin_f'),('teeth_v','teeth_f')]:n[vk],n[fk]=vf(solid(rn[vk],rn[fk]).transform(np.c_[S,[0,0,0]]))
 body=solid(n['v'],n['f']);fin=solid(n['fin_v'],n['fin_f']);teeth=solid(n['teeth_v'],n['teeth_f']);assert(fin^body).volume()<1e-6;guards(pid);gn=np.load(O/'guards_precise'/f'{pid}.npz');ban=solid(gn['v'],gn['f']).transform(np.c_[Q2,t2]);gv,gf=vf(ban);np.savez_compressed(dst/'verification/guards.npz',v=gv,f=gf)
 strict=ban
 if d.get('connector_void_policy')=='whole_stem_extraction':
  from build_revo22_f5_magnet340 import run as mg
  mg(pid);mn=np.load(O/'guards_magnet'/f'{pid}.npz');strict=solid(mn['v'],mn['f']).transform(np.c_[Q2,t2]);mv,mf=vf(strict);np.savez_compressed(dst/'verification/strict_magnet_guards.npz',v=mv,f=mf)
 dropped=[]
 if (teeth^(strict-body)).volume()>=1e-6:
  rebuilt=[];kept=[]
  for kind in ['teeth','local_route_repairs']:
   rr=[]
   for rec in d.get(kind,[]):
    aa=S@np.array(rec['root']);bb=S@np.array(rec['tip']);tw=rec.get('tip_width_mm',.8);xy=np.array([[-1,-1,0],[1,-1,0],[1,1,0],[-1,1,0]]);rw=rec.get('neck_xy_mm',[.8,.8])[0]/2;th=rec.get('taper_height_mm');mid=aa+(bb-aa)*max(0.,1.-th/(bb[2]-aa[2]))if th else None;mid=bb-np.array([0,0,th]) if rec.get('contact_pad') else mid;tt=union([md.Manifold.hull_points(np.r_[xy*rw+aa,xy*rw+mid]),md.Manifold.hull_points(np.r_[xy*rw+mid,xy*tw/2+bb])])if th else md.Manifold.hull_points(np.vstack([xy*rw+aa,xy*tw/2+bb]));rebuilt.append(tt)
    if (tt^(strict-body)).volume()<1e-6:rr.append(rec);kept.append(tt)
    else:dropped.append(dict(kind=kind,root=rec['root'],tip=rec['tip']))
   d[kind]=rr
  recon=union(rebuilt);assert abs((recon-teeth).volume())+abs((teeth-recon).volume())<1e-4
  teeth=union(kept);fin=union([c for c in material_components(fin)if(c^teeth).volume()>.005]);n['fin_v'],n['fin_f']=vf(fin);n['teeth_v'],n['teeth_f']=vf(teeth)
  d.update(new_tooth_count=sum(len(d.get(k,[]))for k in ['teeth','local_route_repairs']),support_count=len(material_components(fin)),support_volume_mm3=float((fin+teeth).volume()),transfer_contacts_dropped_for_functional_access=dropped)
 assert(teeth^(strict-body)).volume()<1e-6,(pid,'connector guard')
 if not d.get('removable_core_may_transit_empty_hardware_space',False):assert(fin^(ban-body)).volume()<1e-6,(pid,'core guard')
 np.savez_compressed(dst/'parts'/f'{pid}.npz',**n);dd=copy.deepcopy(d);dd.update(id=pid,part=old['part'],trial=label,f4_to_current_matrix=Q2.tolist(),f4_to_current_translation_mm=t2.tolist(),transfer_from=dict(id=ref,label=sel['label'],symmetric_material_difference_mm3=err,support_mirrored=bool(np.linalg.det(S)<0),body_rotation_determinant=float(np.linalg.det(Q2))),guard_policy='actual_hex_precise_283');dd['orientation']['matrix']=(Q2@np.array(old['orientation']['matrix'])).tolist();dd['orientation']['source_translation_mm']=(Q2@np.array(old['orientation']['source_translation_mm'])+t2).tolist();dd['baseline_tooth_record_count']=len(old.get('teeth',[]));dd['baseline_support_volume_mm3']=old['support_volume_mm3']
 for rec in dd.get('teeth',[])+dd.get('local_route_repairs',[]):
  for key in['root','tip','target','removal_vector','stem_removal_vector']:
   if key in rec:rec[key]=(S@np.array(rec[key])).tolist()
 put(dst/'design'/f'{pid}.json',dd);put(dst/'verification/construction.json',dict(body_rigid_transform_only=not dd.get('part_body_modified_from_F4',False),fin_body_intersection_mm3=float((fin^body).volume()),support_guard_intersection_mm3=float(((fin+teeth)^(ban-body)).volume()),transfer=dd['transfer_from']));print('FAMILY_BUILT',pid,ref,flush=True)
 return label

def run(pid):
 label=build(pid)
 if label:
  q=audit(pid,label);pick(pid);return(pid,q['native_review_resolved'],q['external_island_count'],q['critical_external_count'])
if __name__=='__main__':
 ids=sys.argv[1:]or['X002','X004','X007','X008','X009','X010','X012','X014']
 with concurrent.futures.ProcessPoolExecutor(max_workers=3)as ex:
  for q in ex.map(run,ids):print('FAMILY_AUDIT',q,flush=True)
