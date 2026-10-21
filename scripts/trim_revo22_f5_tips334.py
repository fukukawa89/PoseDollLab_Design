"""Trim tiny isolated FDM starts in bounded slabs, preserving all assembly contact zones."""
import sys,json,shutil,traceback,concurrent.futures,numpy as np,shapely
from search_revo22_f5_orientation268 import O,put
from build_revo22_fins import solid,vf,union,box,md
from o22_cross_section_geometry import polygon
from o22_material_components import material_components
from verify_revo22_f5_contacts298 import envelope,run as fit
from verify_revo22_f5_geometry292 import run as geo
from audit_revo22_f5_native271 import run as audit
from optimize_revo22_f5_276 import candidates,pick
import repair_revo22_f4_guarded_chamfer as ctx

def create(pid,src,label):
 a=O/'candidates'/pid/src;b=O/'candidates'/pid/label
 if(b/'parts'/f'{pid}.npz').exists():return True
 n=dict(np.load(a/'parts'/f'{pid}.npz'));d=json.loads((a/'design'/f'{pid}.json').read_text());r=json.loads((a/'verification/native_final.json').read_text());it=json.loads((a/'verification/plate_manifest.json').read_text())['items'][0];M=np.array(it['rotation_matrix']);t=np.array(it['translation_mm']);s=solid(n['v'],n['f']);reference=solid(n.get('f5_pre_relief_v',n['v']),n.get('f5_pre_relief_f',n['f']));parts,key,T=ctx.context(d,pid);others=[q.transform(T[:3,:])for k,q in parts.items()if k!=key];count=len(material_components(s));rows=[];lh=d.get('required_layer_height_mm',.2)
 for q in sorted(r['external_islands'],key=lambda q:q['z_mm']):
  bb=q['bounds_mm'];corn=(np.array([[x,y,q['z_mm']-lh/2]for x in[bb[0],bb[2]]for y in[bb[1],bb[3]]])-t)@M;lo=corn.min(0);hi=corn.max(0);point=shapely.Point((lo[:2]+hi[:2])/2);section=polygon(s.slice(float(lo[2])));roi2=shapely.box(lo[0]-.25,lo[1]-.25,hi[0]+.25,hi[1]+.25);local=section.intersection(roi2)
  if local.is_empty or local.area>2.:
   print('TIPS334_SKIP_AREA',pid,local.area,flush=True);continue
  for expand,zheight in[(.15,lh*2.5),(.25,lh*4),(.4,lh*6)]:
   poly=shapely.orient_polygons(local.buffer(expand,quad_segs=4));contours=[]
   for pp in shapely.get_parts(poly):
    if pp.geom_type!='Polygon':continue
    contours.append(np.array(pp.exterior.coords)[:-1]);contours +=[np.array(rr.coords)[:-1]for rr in pp.interiors]
   zlo=lo[2]-lh*.7;cut=md.CrossSection(contours).extrude(zheight+lh*.7).translate([0,0,zlo]);roi=box(np.r_[poly.bounds[:2],zlo],np.r_[poly.bounds[2:],zlo+zheight+lh*.7]);delta=s^cut;rb=np.array(roi.bounding_box());protection=[]
   for other in others:
    ob=np.array(other.bounding_box());sep=np.maximum(np.maximum(ob[:3]-rb[3:],rb[:3]-ob[3:]),0)
    if np.linalg.norm(sep)>.25:continue
    protection.append(envelope(other,roi,margin=.06))
   cut-=union(protection);delta=s^cut;vol=float(delta.volume())
   if not 1e-5<vol<4:
    print('TIPS334_SKIP_VOLUME',pid,vol,flush=True);continue
   proposal=s-cut
   if len(material_components(proposal))!=count:
    print('TIPS334_SKIP_SPLIT',pid,vol,flush=True);continue
   total=float((reference-proposal).volume())
   if total>=min(40.,reference.volume()*.006):continue
   s=proposal;rows.append(dict(kind='trim_isolated_FDM_start',local_bounds_mm=list(roi.bounding_box()),removed_volume_mm3=vol,native_issue=q,actual_neighbor_protection_mm=.06));break
  if rows:break
 if not rows:print('TIPS334_NONE',pid,src,flush=True);return False
 for sub in ['parts','design','verification','projects']:(b/sub).mkdir(parents=True,exist_ok=True)
 n.setdefault('f5_pre_relief_v',n['v'].copy());n.setdefault('f5_pre_relief_f',n['f'].copy());n['v'],n['f']=vf(s);fin=solid(n['fin_v'],n['fin_f']);ts=solid(n['teeth_v'],n['teeth_f']);ts=union([q for q in material_components(ts)if(q^s).volume()>.005 and(q^fin).volume()>.005]);fin=union([q for q in material_components(fin)if(q^ts).volume()>.005]);n['fin_v'],n['fin_f']=vf(fin);n['teeth_v'],n['teeth_f']=vf(ts);np.savez_compressed(b/'parts'/f'{pid}.npz',**n);shutil.copy2(a/'verification/guards.npz',b/'verification/guards.npz');d.update(trial=label,part_body_modified_from_F4=True,body_rigid_transform_only=False,body_f4_faces_identical=False,f5_reliefs=d.get('f5_reliefs',[])+rows,f5_removed_volume_mm3=float((reference-s).volume()),f5_edit_budget_mm3=40.,f5_edit_budget_fraction=.006,fit_and_pose_pending=True,support_count=len(material_components(fin)),support_volume_mm3=float((fin+ts).volume()));put(b/'design'/f'{pid}.json',d);print('TIPS334_BUILT',pid,label,rows[0]['removed_volume_mm3'],flush=True);return True

def run(pid):
 if pick(pid):return(pid,True)
 choices=[q for q in candidates(pid)if list((O/'candidates'/pid/q[2]/'projects').glob('*.3mf'))and float(q[4].get('required_process_overrides',{}).get('min_feature_size','25%').strip('%'))<=100];src=choices[0][2]
 for i in range(10):
  label=f'tips334_{i}'
  if not create(pid,src,label):break
  q=audit(pid,label)
  if q['native_review_resolved']:pick(pid);geo(pid);assert fit(pid)['fit_and_pose_geometry_passed'];return(pid,True)
  src=label
 return(pid,False)
if __name__=='__main__':
 with concurrent.futures.ProcessPoolExecutor(max_workers=3)as ex:
  fs={ex.submit(run,p):p for p in sys.argv[1:]}
  for f in concurrent.futures.as_completed(fs):
   try:print('TIPS334_RESULT',f.result(),flush=True)
   except Exception:traceback.print_exc();print('TIPS334_ERROR',fs[f],flush=True)
