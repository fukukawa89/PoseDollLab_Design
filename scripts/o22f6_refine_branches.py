"""Remove complete offending rods, preserving shared roots and other branches."""
import sys,json
import numpy as np
from o22f6_holeclear import SRC,OUT,WORK,solid,vf,md,union,put,save_mesh,material_components,box
from o22f6_route import collect

def rod(q,n,d=None):
 if q.get('mesh_key'):return solid(n[q['mesh_key']+'_v'],n[q['mesh_key']+'_f'])
 if 'root'in q:a=np.array(q['root']);b=np.array(q.get('tip',np.array(q['target'])+[0,0,.24]))
 else:a=np.array([q['x'],q['root_y'],max(.4,q['roof']-q['free_vertical_mm']-.3)]);b=np.array([q['x'],q['y'],q['roof']+.18])
 xy=np.array([[-1,-1,0],[1,-1,0],[1,1,0],[-1,1,0]],float);Q=np.eye(3)
 if d and d.get('tilt_refinement_deg'):
  import trimesh
  for axis,degrees in d['tilt_refinement_deg'].items():Q=trimesh.transformations.rotation_matrix(np.deg2rad(degrees),np.eye(3)['xyz'.index(axis)])[:3,:3]@Q
 w=np.r_[np.array(q.get('neck_xy_mm',[.8,.8]))/2,0];tip=q.get('tip_width_mm',.8)/2
 if q.get('taper_height_mm'):
  middle=a+(b-a)*(1-q['taper_height_mm']/(b[2]-a[2]));top=b+[0,0,q['contact_pad']]if q.get('contact_pad')else b
  return union([md.Manifold.hull_points(np.r_[(xy*w)@Q.T+a,(xy*w)@Q.T+middle]),md.Manifold.hull_points(np.r_[(xy*w)@Q.T+middle,(xy*tip)@Q.T+top])])
 return md.Manifold.hull_points(np.r_[(xy*w)@Q.T+a,(xy*tip)@Q.T+b])

def refine(pid):
 original=np.load(SRC/f'parts/{pid}.npz');d=json.loads((OUT/f'design/{pid}.json').read_text());n=dict(np.load(OUT/f'parts/{pid}.npz'));g=np.load(WORK/f'guards/{pid}.npz');ban=solid(g['v'],g['f']);old=solid(original['teeth_v'],original['teeth_f']);bad=[];good=[];rows=[];uncertain=[]
 all_branches='--all' in sys.argv; reports,_=collect(); qs=reports.get(pid,dict(external_islands=[],critical_external_runs=[]));rois=[]
 for q in qs['external_islands']+qs['critical_external_runs']:
  bb=q['bounds_mm'];z=q['z_mm'];rois.append(box([bb[0]-.2,bb[1]-.2,z-.24],[bb[2]+.2,bb[3]+.2,z+.08]))
 roi=union(rois)
 for field in ['teeth','local_route_repairs']:
  for i,q in enumerate(d.get(field,[])):
   s=rod(q,original,d);difference=max(0.,float((s-old).volume()))
   if difference>1e-4:uncertain.append(dict(field=field,index=i,difference=difference));continue
   if (s^ban).volume()>1e-6 and (all_branches or (s^roi).volume()>1e-5):bad.append(s);rows.append(dict(field=field,index=i,tip=q.get('tip',q.get('target'))))
   else:good.append(s)
 current=solid(n['teeth_v'],n['teeth_f']);cut=union(bad)-union(good);teeth=current-cut;body=solid(n['v'],n['f']);fin=solid(n['fin_v'],n['fin_f']);basevol=float((fin+teeth).volume())
 for step in range(6):
  before=float((fin+teeth).volume());teeth=union([c for c in material_components(teeth)if(c^body).volume()>.001 and(c^fin).volume()>.001]);fin=union([c for c in material_components(fin)if(c^teeth).volume()>.001 and c.bounding_box()[2]<1e-5 and c.slice(.05).area()>.005])
  if before-float((fin+teeth).volume())<1e-6:break
 assert((fin+teeth)^ban).volume()<1e-6;assert len(material_components(body+fin+teeth))==len(material_components(body))
 n['fin_v'],n['fin_f']=vf(fin);n['teeth_v'],n['teeth_f']=vf(teeth);dest=WORK/('refined_scoped' if all_branches else 'refined_current');(dest/'parts').mkdir(parents=True,exist_ok=True);np.savez_compressed(dest/f'parts/{pid}.npz',**n);report=dict(id=pid,removed_full_branch_records=rows,unreconstructed_records=uncertain,removed_teeth_mm3=float((current-teeth).volume()),guard_occupancy_mm3=max(0.,float(((fin+teeth)^ban).volume())));d['f6_whole_branch_removal']=report;put(dest/f'design/{pid}.json',d);put(dest/f'verification/{pid}.json',report);print('BRANCH_REFINE',pid,len(rows),'uncertain',len(uncertain),'removed',report['removed_teeth_mm3'],flush=True)

if __name__=='__main__':
 ids=[x for x in sys.argv[1:] if x!='--all']; ids=ids or ([p.stem for p in sorted((OUT/'parts').glob('*.npz'))] if '--all' in sys.argv else list(collect()[0]))
 import concurrent.futures
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as pool:
  for result in pool.map(refine,ids):pass