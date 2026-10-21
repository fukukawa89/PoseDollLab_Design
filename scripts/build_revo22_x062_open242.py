"""X062 only: open underside combs with long cuttable teeth and checked extraction."""
from pathlib import Path
import sys,json,hashlib,math
import numpy as np
import trimesh
from shapely.geometry import LineString
from build_revo22_fins import solid,vf,box,union,cs_union,slab,project_xz,extrude_xz,sweep2d,md,write_stl
from o22_cross_section_geometry import polygon
from o22_material_components import material_components
R=Path(__file__).resolve().parents[1];B=R/'Hardware/PoseDoll44/bench/revO22';OLD=B/'O22F4_Compact';S=B/'a1mini_fins_v4/x062_trial242'
ROT=np.array([[.7719488505585549,-.054390986496201985,.6333534500650453],[.5124410658247703,.64282034196701,-.5693734820043779],[-.37616369598580235,.7640835219669289,.5240965991884651]])
def put(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(label):
 global ROT
 if len(sys.argv)>2:
  idx=int(sys.argv[2]);rr=json.loads((R/'.local/x062_orientation242.json').read_text());zz=np.array(next(q['z']for q in rr if q['index']==idx));xx=np.array([1.,0,0]);xx-=zz*np.dot(xx,zz);xx/=np.linalg.norm(xx);yy=np.cross(zz,xx);ROT=np.array([xx,yy,zz])@ROT
 folder=S/'candidates/X062'/label
 for sub in ['parts','design','verification','projects','stl']:(folder/sub).mkdir(parents=True,exist_ok=True)
 n=np.load(OLD/'parts/X062.npz');old=json.loads((OLD/'design/X062.json').read_text());v=n['v']@ROT.T;off=-v.min(0)+[0,0,6];v+=off
 orient=old['orientation'];M=ROT@np.array(orient['matrix']);t=ROT@np.array(orient['source_translation_mm'])+off
 s=solid(v,n['f']);mesh=trimesh.Trimesh(v,n['f'],process=False);bb=np.array(s.bounding_box());height=bb[5]
 pitch=7.2;tx=2.4;gap=5.2;thick=1.2;nw=.80;nd=.80
 ys=np.arange(bb[1]+1.2,bb[4]+1.2,pitch);xs=np.arange(bb[0]+.30,bb[3],tx)
 requests=[]
 for row,yc in enumerate(ys):
  for yi,yt in enumerate([yc-2.4,yc,yc+2.4]):
   for x in xs+(yi-1)*.6:requests.append((row,yc,float(x),float(yt)))
 origins=np.array([[x,y,-.1]for _,_,x,y in requests]);dirs=np.tile([0,0,1],(len(origins),1))
 loc,ri,ti=mesh.ray.intersects_location(origins,dirs,multiple_hits=False);targets=[]
 for p,ridx,tidx in zip(loc,ri,ti):
  if mesh.face_normals[tidx,2]>-.45:continue
  row,yc,x,y=requests[ridx];targets.append(dict(row=row,root_y=yc,x=x,y=y,roof=float(p[2]),normal=mesh.face_normals[tidx].tolist()))
 # Explicit foundations for newly appearing disconnected body islands.
 prev=s.slice(.1)
 for zz in np.arange(.3,height,.2):
  cur=s.slice(float(zz));pg=polygon(cur)
  for cc in getattr(pg,'geoms',[pg]):
   if cc.is_empty or cc.area<.03:continue
   if cc.intersection(polygon(prev).buffer(.01)).area>.001:continue
   pp=cc.representative_point();hit,ri2,fi2=mesh.ray.intersects_location([[pp.x,pp.y,-.1]],[[0,0,1]],multiple_hits=False)
   if not len(hit)or abs(hit[0,2]-zz)>.25:continue
   row=int(np.argmin(np.abs(ys-pp.y)));targets.append(dict(row=row,root_y=float(ys[row]),x=float(pp.x),y=float(pp.y),roof=float(hit[0,2]),normal=mesh.face_normals[fi2[0]].tolist(),critical_foundation=True))
  prev=cur
 if label=='open242_c':
  qv=S/'candidates/X062/open242_a/verification';ar=json.loads((qv/'full_bead_contacts_v5.json').read_text());it=json.loads((qv/'plate_manifest.json').read_text())['items'][0];pm=np.array(it['rotation_matrix']);pt=np.array(it['translation_mm']);samples=[]
  for qr in ar['critical_external_runs']:
   line=LineString(qr['xy_mm'])
   for dist in np.arange(.2,line.length,.95):
    p=line.interpolate(float(dist));samples.append((np.array([p.x,p.y,qr['z_mm']])-pt)@pm)
  for qr in ar['external_islands']:
   b=qr['bounds_mm'];samples.append((np.array([(b[0]+b[2])/2,(b[1]+b[3])/2,qr['z_mm']])-pt)@pm)
  for p in samples:
   hit,ri2,fi2=mesh.ray.intersects_location([[p[0],p[1],-.1]],[[0,0,1]],multiple_hits=False)
   if not len(hit)or abs(hit[0,2]-p[2])>1.1:continue
   if min((np.linalg.norm(p[:2]-[a['x'],a['y']])for a in targets),default=100)<.9:continue
   row=int(np.argmin(np.abs(ys-p[1])));targets.append(dict(row=row,root_y=float(ys[row]),x=float(p[0]),y=float(p[1]),roof=float(hit[0,2]),normal=mesh.face_normals[fi2[0]].tolist(),native_foundation=True))
 fins=[];teeth=[];segments=[];tr=[];rejected=[]
 for row,yc in enumerate(ys):
  group=[q for q in targets if q['row']==row];raw=[]
  for q in group:
   x=q['x'];h=min(a['roof']for a in group if abs(a['x']-x)<1.3)-gap
   if h<.45:continue
   half=max(1.3,h*.20);raw.append(md.CrossSection([[(x-half,0),(x+half,0),(x+1.3,h),(x-1.3,h)]]))
  if not raw:continue
  avoid=project_xz(slab(s,yc-thick/2-.20,yc+thick/2+.20,bb)).offset(.35,circular_segments=12)
  profile=cs_union(raw)-sweep2d(avoid,[0,height+5]);profile=cs_union([p for p in profile.decompose()if p.area()>.3 and p.bounds()[1]<1e-6])
  if profile.is_empty():continue
  pg=polygon(profile);core=extrude_xz(profile,thick,float(yc));foot=core.slice(.1).offset(1.8,circular_segments=12).extrude(.4);fin=core+foot
  assert (fin^s).volume()<1e-6
  rowteeth=[];records=[]
  for q in group:
   x=q['x'];roof=q['roof'];g=pg.intersection(LineString([(x,0),(x,height+2)]))
   if g.is_empty:continue
   cap=g.bounds[3];free=roof-cap
   if not 3.8<=free<=9:rejected.append(dict(**q,reason='gap',gap=free));continue
   rootz=max(.4,cap-.30);topz=roof+.18
   corners=np.array([[-nw/2,-nd/2,0],[nw/2,-nd/2,0],[nw/2,nd/2,0],[-nw/2,nd/2,0]])
   a=corners+[x,yc,rootz];b=corners+[x,q['y'],topz];tooth=md.Manifold.hull_points(np.vstack([a,b]));crownbase=a+(b-a)*((roof-.85-rootz)/(topz-rootz));wide=corners.copy();wide[:,0]*=1.4/nw;wide[:,1]*=1.4/nd;bite=float((tooth^s).volume());root=float((tooth^fin).volume())
   if not .005<bite<1.0 or root<.005:rejected.append(dict(**q,reason='bite_or_root',bite=bite,root=root));continue
   under=(tooth^s^box(bb[:3]-[20,20,10],[bb[3]+20,bb[4]+20,roof-1.5])).volume()
   if under>1e-6:rejected.append(dict(**q,reason='premature_contact'));continue
   cutz=roof-1.5;cut=a+(b-a)*((cutz-rootz)/(topz-rootz));stub=md.Manifold.hull_points(np.vstack([a,cut]));sv=vf(stub)[0];swept=md.Manifold.hull_points(np.vstack([sv,sv-[0,0,height+4]]));collision=float((swept^s).volume())
   if collision>1e-6:rejected.append(dict(**q,reason='withdrawal',collision=collision));continue
   rowteeth.append(tooth);records.append(dict(**q,free_vertical_mm=free,free_centerline_mm=math.hypot(free,q['y']-yc),neck_width_mm=nw,neck_depth_mm=nd,bite_mm3=bite,root_overlap_mm3=root,cut_height_mm=cutz,stub_downward_sweep_collision_mm3=collision))
  if not rowteeth:continue
  tu=union(rowteeth);pieces=material_components(fin);fin=union([p for p in pieces if (p^tu).volume()>.005])
  assert (extrude_xz(sweep2d(profile,[0,-height-4]),thick,float(yc))^s).volume()<1e-6
  fins.append(fin);teeth.extend(rowteeth);tr.extend(records);segments.append(dict(row=int(row),y=float(yc),thickness_mm=thick,teeth=len(records),bounds_mm=list(fin.bounding_box()),continuous_downward_extraction_collision_mm3=0))
 fin=union(fins);tooth=union(teeth);roots=material_components(fin);tc=material_components(tooth);checks=[]
 for p in roots:
  rec=dict(bounds_mm=list(p.bounding_box()),bed_contact_mm2=float(p.slice(.1).area()),tooth_overlap_mm3=float((p^tooth).volume()));assert rec['bounds_mm'][2]<1e-6 and rec['bed_contact_mm2']>.01 and rec['tooth_overlap_mm3']>.005;checks.append(rec)
 contact=[]
 for p in tc:
  rec=dict(body_overlap_mm3=float((p^s).volume()),fin_overlap_mm3=float((p^fin).volume()));assert min(rec.values())>.005;contact.append(rec)
 assert (fin^s).volume()<1e-6
 fv,ff=vf(fin);tv,tf=vf(tooth);npz=folder/'parts/X062.npz';np.savez_compressed(npz,v=v,f=n['f'],source_v=n['source_v'],fin_v=fv,fin_f=ff,teeth_v=tv,teeth_f=tf)
 vol=float((fin+tooth).volume());same=bool(np.allclose(n['source_v']@M.T+t,v,atol=1e-7)and np.array_equal(n['f'],np.load(npz)['f']))
 data=dict(id='X062',part='frame/clavicle_r',trial=label,orientation=dict(matrix=M.tolist(),source_translation_mm=t.tolist(),size_mm=(v.max(0)-v.min(0)).tolist()),source_mesh_preserved=True,part_body_modified=False,required_layer_height_mm=.2,required_initial_layer_height_mm=.2,required_wall_generator='arachne',fuse_print_geometry=True,style='independent_open_underside_combs',nominal_pitch_mm=pitch,fin_thickness_mm=thick,neck_dimensions_mm=[nw,nd],nominal_tooth_free_length_mm=gap,support_count=len(roots),segments=segments,teeth=tr,rejected_targets=rejected,support_volume_mm3=vol,previous_support_volume_mm3=194203.47766082024,part_volume_mm3=float(s.volume()),physical_print_tested=False,user_reported_previous_C03_stable_but_difficult_to_cut_and_remove=True,status='Construction candidate; native audit pending')
 put(folder/'design/X062.json',data)
 put(folder/'verification/geometry.json',dict(source_mesh_preserved=same,part_body_modified=False,assembly_and_pose_geometry_unchanged=same,fin_body_overlap_mm3=float((fin^s).volume()),bed_rooted_components=checks,tooth_components=contact,continuous_downward_fin_and_clipped_stub_extraction_checked=True,minimum_tooth_free_height_mm=min(t['free_vertical_mm']for t in tr),neck_dimensions_mm=[nw,nd],support_volume_mm3=vol,support_reduction_percent=100*(1-vol/194203.47766082024),geometric_constraints_passed=same,parts_npz_sha256=sha(npz),physical_print_tested=False,force_simulation_performed=False))
 for name,obj in [('body',s),('fins',fin),('teeth',tooth),('combined',s+fin+tooth)]:write_stl(folder/'stl'/f'X062_{name}.stl',obj)
 print('OPEN242_BUILT',label,'roots',len(roots),'teeth',len(tr),'volume_mm3',vol,'reduction_pct',100*(1-vol/194203.47766082024),'rejected',len(rejected),'source_identical',same,flush=True)
if __name__=='__main__':run(sys.argv[1])





