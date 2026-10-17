"""Route native-supported contacts onto side faces as well as undersides."""
from pathlib import Path
import sys,json,math,shutil,collections,time,numpy as np,trimesh
from shapely.geometry import LineString
from search_revo22_f5_orientation268 import R,B,O,OLD,put
from build_revo22_fins import solid,vf,box,union,md
from route_revo22_x062244 import tooth,sweep_convex
from o22_material_components import material_components
from build_revo22_f5_magnet340 import run as magnet_guard
from verify_revo22_x062_removal245 import exact_clear

def run(pid,src,label,max_targets=2000,allow_removable_core=False,target_native_height=False,tip_width=None):
 old=O/'candidates'/pid/src;folder=O/'candidates'/pid/label
 if(folder/'parts'/f'{pid}.npz').exists():return json.loads((folder/'design'/f'{pid}.json').read_text())
 for sub in ['parts','design','verification','projects','stl']:(folder/sub).mkdir(parents=True,exist_ok=True)
 n=dict(np.load(old/'parts'/f'{pid}.npz'));d=json.loads((old/'design'/f'{pid}.json').read_text());s=solid(n['v'],n['f']);fin=solid(n['fin_v'],n['fin_f']);ts=solid(n['teeth_v'],n['teeth_f']);gn=np.load(old/'verification/guards.npz');full_guard=solid(gn['v'],gn['f']);magnet_guard(pid);mg=np.load(O/'guards_magnet'/f'{pid}.npz');strict_guard=solid(mg['v'],mg['f']).transform(np.c_[d['f4_to_current_matrix'],d['f4_to_current_translation_mm']]);ban=strict_guard-s;mesh=trimesh.Trimesh(n['v'],n['f'],process=False);fm=trimesh.Trimesh(n['fin_v'],n['fin_f'],process=False)if len(n['fin_f'])else None
 report=json.loads((old/'verification/native_final.json').read_text());it=json.loads((old/'verification/plate_manifest.json').read_text())['items'][0];M=np.array(it['rotation_matrix']);t=np.array(it['translation_mm']);height=float(n['v'][:,2].max());req=[]
 for q in report['external_islands']:
  b=q['bounds_mm'];req.append(((np.array([(b[0]+b[2])/2,(b[1]+b[3])/2,q['z_mm']])-t)@M,True))
 for q in sorted(report['critical_external_runs'],key=lambda q:(q['z_mm'],-q['length_mm'])):
  line=LineString(q['xy_mm']);count=max(1,int(math.ceil(line.length/2.2)))
  for x in [0.,line.length]+list((np.arange(count)+.5)*line.length/count):
   p=line.interpolate(x);req.append(((np.array([p.x,p.y,q['z_mm']])-t)@M,False))
 dirs=[np.array([0.,0.])]+[np.array([math.cos(a),math.sin(a)])for a in np.arange(0,2*np.pi,np.pi/8)];roots=[];teeth=[];records=[];failed=[];seen=[];rr=collections.Counter();rootrecs=d.get('teeth',[])+d.get('local_route_repairs',[])
 allfin=fin;allmaterial=s+fin+ts
 def make_tooth(a,b):
  if tip_width is None:return tooth(a,b)
  xy=np.array([[-1,-1,0],[1,-1,0],[1,1,0],[-1,1,0]])
  middle=a+(b-a)*max(0.,1.-.45/(b[2]-a[2])); return union([md.Manifold.hull_points(np.vstack([xy*.4+a,xy*.4+middle])),md.Manifold.hull_points(np.vstack([xy*.4+middle,xy*(tip_width/2)+b]))])
 def stem_direction(tt,a,b):
  excess=tt-s;direct=a-b;direct/=np.linalg.norm(direct)
  for dr in [direct,np.array([0.,0.,-1.])]:
   if exact_clear(excess,s,dr*(height+80))[0]:return dr
  return None
 for qi,(p,critical)in enumerate(req[:max_targets]):
  if any(np.linalg.norm(p-q)<1.05 for q in seen):continue
  offsets=[(0,0)]+[(r*math.cos(a),r*math.sin(a))for r in[.35,.7,1.05,1.4]for a in np.arange(0,2*np.pi,np.pi/4)]
  candidates=[]
  for dx,dy in offsets:
   hh,_,ff=mesh.ray.intersects_location([[p[0]+dx,p[1]+dy,-.1]],[[0,0,1]],multiple_hits=True)
   for h,f in zip(hh,ff):
    if -.30<=p[2]-h[2]<=3.0 and mesh.face_normals[f,2]<-.15:candidates.append(h)
  side_tips={}
  sample=np.array([[p[0]+dx,p[1]+dy,p[2]-.1+dz]for dx,dy in [(0,0)]+[(r*math.cos(a),r*math.sin(a))for r in [.6,1.3,2.1]for a in np.arange(0,2*np.pi,np.pi/4)]for dz in [0.,.2]])
  closest,dist,face=trimesh.proximity.closest_point(mesh,sample)
  for h,di,fi in zip(closest,dist,face):
   norm=mesh.face_normals[fi]
   if di>1.5 or abs(h[2]-p[2])>.5 or np.linalg.norm(h[:2]-p[:2])>2.6 or norm[2]<-.3 or norm[2]>.8:continue
   key=tuple(np.round(h,6));side_tips[key]=h-norm*.38+np.array([0.,0.,.06]);candidates.append(h)
  unique={tuple(np.round(h,5)):h for h in candidates};candidates=list(unique.values());candidates.sort(key=lambda h:abs(h[2]-p[2])+np.linalg.norm(h[:2]-p[:2])*.1)
  if not candidates:failed.append(dict(p=p.tolist(),reason='No adjacent downward body surface'));continue
  success=False
  for hit in candidates:
   roof=float(hit[2]);b=side_tips.get(tuple(np.round(hit,6)),hit+[0,0,.18]).copy()
   if target_native_height:b[2]=max(b[2],float(p[2])+.3)
   if roof<1.65:continue
   if (tooth(b-[0,0,.12],b,w=tip_width or .8)^ban).volume()>1e-7:continue
   rootspec=[]
   for parent in sorted({tuple(np.round(q['root'],5)):q for q in rootrecs+records}.values(),key=lambda q:np.linalg.norm(np.array(q['root'])[:2]-hit[:2]))[:12]:
    a=np.array(parent['root']);a[2]=max(.12,a[2]);dz=roof-a[2]
    if 1.4<dz<10.5 and np.linalg.norm(a[:2]-hit[:2])<min(7.,dz*.95):rootspec.append((a,None,np.array(parent.get('removal_vector',[0.,0.,-1.]))))
   if fm is not None:
    for seg in sorted(d.get('segments',[]),key=lambda q:abs(q['y']-hit[1]))[:2]:
     xy=np.array([hit[0],seg['y']]);hh,_,_=fm.ray.intersects_location([[*xy,roof-.1]],[[0,0,-1]],multiple_hits=False)
     if len(hh)and 1.5<roof-hh[0,2]<8:rootspec.append((np.r_[xy,max(.12,hh[0,2]-.28)],None,np.array([0.,0.,-1.])))
   for a,core,direction in rootspec:
    tt=make_tooth(a,b);bite=tt^s;bv=float(bite.volume())
    if not .008<bv<(4. if target_native_height else .9) or bite.bounding_box()[2]<roof-1.5:continue
    if(tt^ban).volume()>1e-7:continue
    if (tt-allmaterial).volume()<1e-4:continue
    if(tt^allfin).volume()<.02:continue
    stem=stem_direction(tt,a,b)
    if stem is None:continue
    teeth.append(tt);allmaterial+=tt;records.append(dict(target=hit.tolist(),tip=b.tolist(),root=a.tolist(),neck_xy_mm=[.8,.8],tip_width_mm=tip_width or .8,free_vertical_mm=roof-a[2]-.2,body_overlap_mm3=bv,fin_overlap_mm3=float((tt^allfin).volume()),new_bed_fin=False,removal_vector=direction.tolist(),kind='extractable_void_contact_341',taper_height_mm=.45,stem_removal_vector=stem.tolist(),whole_excess_stem_swept_clear=True));seen.append(p);success=True;break
   if success:break
   for dz in[5.2,7.2,9.2,3.2,1.6]:
    az=roof-dz
    if az<.35:continue
    for dv in dirs:
     reach=min(4.2,dz*.8);a=np.r_[hit[:2]-dv*reach,az];tt=make_tooth(a,b);bite=tt^s;bv=float(bite.volume())
     if not .008<bv<(4. if target_native_height else .9) or bite.bounding_box()[2]<roof-1.5:rr['bite']+=1;continue
     if(tt^ban).volume()>1e-7:rr['tooth_guard']+=1;continue
     if (tt-allmaterial).volume()<1e-4:rr['already_present']+=1;continue
     direction=np.r_[-dv*reach/dz,-1.];direction/=np.linalg.norm(direction);u=dv if np.linalg.norm(dv)>.1 else np.array([1.,0.]);perp=np.array([-u[1],u[0]]);thick=1.2 if az<60 else 1.6 if az<95 else 2.
     for lean in[0.,.4,.75]:
      c=a[:2]-u*lean*az;pts=[]
      bed_center=(n['v'][:,:2].min(0)+n['v'][:,:2].max(0))/2;half_base=np.abs(u)*max(4.5,az*.28)/2+np.abs(perp)*thick/2+.85;c=np.clip(c,bed_center-86+half_base,bed_center+86-half_base)
      if np.linalg.norm(c-a[:2])>az*.8:continue
      for center,z,w in[(c,0.,max(4.5,az*.28)),(a[:2],az+.2,1.9)]:
       for l,k in[(-1,-1),(1,-1),(1,1),(-1,1)]:pts.append([*(center+u*l*w/2+perp*k*thick/2),z])
      core=md.Manifold.hull_points(np.array(pts));core+=core.slice(.1).offset(.8,circular_segments=8).extrude(.4)
      if(core^s).volume()>1e-7:rr['core_body']+=1;continue
      if not allow_removable_core and(core^ban).volume()>1e-7:rr['core_guard']+=1;continue
      if(core^allfin).volume()>1e-7:continue
      if(tt^core).volume()<.02:continue
      if(core^ts).volume()>1e-7:continue
      if(sweep_convex(core,direction*(height+80))^s).volume()>1e-7:rr['withdrawal']+=1;continue
      stem=stem_direction(tt,a,b)
      if stem is None:continue
      roots.append(core);allfin+=core;allmaterial+=core;teeth.append(tt);allmaterial+=tt;records.append(dict(target=hit.tolist(),tip=b.tolist(),root=a.tolist(),neck_xy_mm=[.8,.8],tip_width_mm=tip_width or .8,free_vertical_mm=roof-a[2]-.2,body_overlap_mm3=bv,fin_overlap_mm3=float((tt^core).volume()),new_bed_fin=True,removal_vector=direction.tolist(),kind='extractable_void_contact_341',taper_height_mm=.45,stem_removal_vector=stem.tolist(),whole_excess_stem_swept_clear=True));seen.append(p);success=True;break
     if success:break
    if success:break
   if success:break
  if not success:failed.append(dict(p=p.tolist(),reason='No clear bed route outside functional guards'))
  if qi%40==0:print('F5_ROUTE',pid,label,qi,len(req),'added',len(records),'fins',len(roots),'unrouted',len(failed),flush=True)
 fin=allfin;ts+=union(teeth);ts=ts^box([-1000,-1000,0],[1000,1000,1000]);d['teeth_clipped_at_bed']=True;assert(fin^s).volume()<1e-6 and(ts^ban).volume()<1e-6
 if not allow_removable_core:assert(fin^ban).volume()<1e-6
 for c in material_components(fin):assert c.bounding_box()[2]<1e-6 and(c^ts).volume()>.005
 for c in material_components(ts):assert(c^fin).volume()>.005 and(c^s).volume()>.005
 n['fin_v'],n['fin_f']=vf(fin);n['teeth_v'],n['teeth_f']=vf(ts);np.savez_compressed(folder/'parts'/f'{pid}.npz',**n);shutil.copy2(old/'verification/guards.npz',folder/'verification/guards.npz')
 mv,mf=vf(strict_guard);np.savez_compressed(folder/'verification/strict_magnet_guards.npz',v=mv,f=mf)
 d.update(connector_void_policy='whole_stem_extraction',trial=label,local_route_repairs=d.get('local_route_repairs',[])+records,unrouted_native_targets=failed,support_count=len(material_components(fin)),support_volume_mm3=float((fin+ts).volume()),new_tooth_count=d['new_tooth_count']+len(records),native_previous_label=src,physical_print_tested=False,native_pending=True,removable_core_may_transit_empty_hardware_space=allow_removable_core or d.get('removable_core_may_transit_empty_hardware_space',False));put(folder/'design'/f'{pid}.json',d);put(folder/'verification/construction.json',dict(id=pid,fin_body_intersection_mm3=float((fin^s).volume()),support_guard_intersection_mm3=float(((fin+ts)^ban).volume()),connector_guard_intersection_mm3=float((ts^ban).volume()),temporary_core_guard_intersection_mm3=float((fin^ban).volume()),removable_core_policy=allow_removable_core,all_fins_bed_rooted=True,body_unchanged_from_F4=True,added_teeth=len(records),added_fins=len(roots),unrouted_targets=failed,rejections=dict(rr)));print('F5_ROUTED',pid,label,'added',len(records),'fins',len(roots),'unrouted',len(failed),flush=True);return d
if __name__=='__main__':run(*sys.argv[1:4])
