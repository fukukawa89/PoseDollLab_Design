"""Add short broad teeth to existing bed-rooted fin bodies; never root them on a part."""
from pathlib import Path
import sys,json,numpy as np,trimesh,math,concurrent.futures,traceback
from shapely.geometry import LineString,Point,box as rect
from shapely.ops import nearest_points
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,vf,union,box,md
from o22_cross_section_geometry import polygon
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
from refine_revo22_f4_lateral104 import check as refine
from verify_revo22_f4_body_change import check as fit
from verify_revo22_f4_repaired_geometry import check as geom
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'

def trial(spec):
 pid,parent=spec.split(':');label='existing_teeth105';src=O/'candidates'/pid/parent;dst=O/'candidates'/pid/label
 for sub in ['parts','design','verification']:(dst/sub).mkdir(parents=True,exist_ok=True)
 n=dict(np.load(src/'parts'/f'{pid}.npz'));d=json.loads((src/'design'/f'{pid}.json').read_text());s=solid(n['v'],n['f']);fin=solid(n['fin_v'],n['fin_f']);teeth=solid(n['teeth_v'],n['teeth_f']);tm=trimesh.Trimesh(n['v'],n['f'],process=False);aud=src/'verification/full_bead_contacts_v5.json';aud=aud if aud.exists()else src/'verification/full_bead_contacts_v2.json';q=json.loads(aud.read_text());it=json.loads((src/'verification/plate_manifest.json').read_text())['items'][0];M=np.array(it['rotation_matrix']);off=np.array(it['translation_mm']);added=[];seen=[]
 for issue in q['external_islands']+q['critical_external_runs']:
  if 'xy_mm'in issue:
   line=LineString(issue['xy_mm']);targets=[line.interpolate(x)for x in np.linspace(0,line.length,max(2,int(np.ceil(line.length/.65))))]
  else:
   b=issue['bounds_mm'];targets=[Point((b[0]+b[2])/2,(b[1]+b[3])/2)]
  for pp in targets:
   p=(np.array([pp.x,pp.y,issue['z_mm']-.1])-off)@M
   if any(np.linalg.norm(p-x)<.5 for x in seen):continue
   seen.append(p);region=polygon(s.slice(p[2])).intersection(rect(p[0]-.55,p[1]-.55,p[0]+.55,p[1]+.55))
   if region.is_empty:continue
   xy=nearest_points(region.buffer(-.005),Point(p[:2]))[0]if not region.buffer(-.005).is_empty else region.representative_point();p[:2]=[xy.x,xy.y];hits,_,faces=tm.ray.intersects_location([[*p[:2],-.1]],[[0,0,1]],multiple_hits=True);hits=[h for h,f in zip(hits,faces)if tm.face_normals[f,2]<-.15 and p[2]-1.5<h[2]<p[2]+.3]
   if not hits:continue
   roof=float(min(hits,key=lambda h:abs(h[2]-p[2]))[2]);best=None
   for rise in [1.,1.4,1.8,2.4,3.]:
    hz=roof-rise
    if hz<.4:continue
    root_section=polygon(fin.slice(hz-.05));candidates=[]
    if not root_section.is_empty:
     inset=root_section.buffer(-.7)
     if not inset.is_empty:
      npnt=nearest_points(inset,Point(p[:2]))[0];candidates.append(np.array([npnt.x,npnt.y]))
    candidates.extend(p[:2]+dist*np.array([math.cos(a),math.sin(a)])for dist in [0.,.6,1.2,1.8,2.4]for a in np.arange(0,2*math.pi,np.pi/12))
    for c in candidates:
     reach=float(np.linalg.norm(c-p[:2]))
     if reach>2.40001 or reach>rise*.85:continue
     direction=(p[:2]-c)/max(reach,1e-6)
     if reach<1e-5:direction=np.array([1.,0.])
     tangent=np.array([-direction[1],direction[0]])
     for theta in [0,np.pi/2]:
      A=np.array([[math.cos(theta),-math.sin(theta)],[math.sin(theta),math.cos(theta)]])@np.array([direction,tangent]);rootxy=np.array([[x,y]for x in [-.8,.8]for y in[-1.6,1.6]])@A+c
      poly=__import__('shapely').MultiPoint(rootxy).convex_hull
      if poly.difference(root_section).area>.015:continue
      rootpts=np.array([[xy[0],xy[1],z]for xy in rootxy for z in [hz-.25,hz+.15]]);tippts=np.array([[p[0]+x,p[1]+y,z]for x in[-.5,.5]for y in[-.5,.5]for z in[roof+.1,roof+.35]]);tt=md.Manifold.hull_points(np.r_[rootpts,tippts]);bite=float((tt^s).volume());root=float((tt^fin).volume())
      if not .01<bite<.85 or root<.1:continue
      if(tt^s^box([-300,-300,0],[300,300,roof-.31])).volume()>1e-6:continue
      if float((tt-teeth).volume())<.03:continue
      score=reach+rise*.1
      if best is None or score<best[0]:best=(score,tt,bite,root,c,reach,rise)
    if best:break
   if best:
    _,tt,bite,root,c,reach,rise=best;teeth=teeth+tt;rec={'bounds_mm':list(tt.bounding_box()),'part_bite_mm3':bite,'fin_root_mm3':root,'nominal_tip_penetration_mm':.35,'neck_xy_mm':[1,1],'broad_connector_root_xy_mm':[1.6,3.2],'short_connector_horizontal_reach_mm':reach,'connector_rise_mm':rise,'contact_point_mm':[p[0],p[1],roof],'rooted_on_existing_bed_fin':True,'native_issue':issue};d['teeth'].append(rec);added.append(rec);print('EXISTING105_TOOTH',pid,p,reach,rise,flush=True)
 n['teeth_v'],n['teeth_f']=vf(teeth);d.update(support_volume_mm3=float((fin+teeth).volume()),teeth_part_overlap_mm3=float((teeth^s).volume()),existing_fin_teeth105=added);np.savez_compressed(dst/'parts'/f'{pid}.npz',**n);(dst/'design'/f'{pid}.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');print('EXISTING105_COUNT',pid,len(added),flush=True)
 if not added:return
 if (src/'verification/body_change_fit_and_pose.json').exists():
  import shutil;shutil.copy2(src/'verification/body_change_fit_and_pose.json',dst/'verification/body_change_fit_and_pose.json')
 run(pid,label);check(pid,label);q=refine(pid,label)
 if q['native_review_resolved']:
  if 'body_change'in d and not(dst/'verification/body_change_fit_and_pose.json').exists():fit(pid,label)
  geom(pid,label)
if __name__=='__main__':
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as pool:
  for f in concurrent.futures.as_completed([pool.submit(trial,s)for s in sys.argv[1:]]):
   try:f.result()
   except Exception:traceback.print_exc()
