"""F5 open, bed-rooted comb fins with accessible 0.8 mm long teeth."""
from pathlib import Path
import sys,json,math,collections,time,concurrent.futures,numpy as np,trimesh
from build_revo22_fins import solid,vf,box,union,cs_union,slab,project_xz,extrude_xz,sweep2d,md,write_stl
from o22_cross_section_geometry import polygon
from o22_material_components import material_components
from route_revo22_x062244 import tooth
from search_revo22_f5_orientation268 import R,B,O,OLD,put

def run(pid,label='open_a',rank=0,pitch=7.2,spacing=3.,lift_override=None,precise_guard=False):
 folder=O/'candidates'/pid/label
 if(folder/'parts'/f'{pid}.npz').exists():return json.loads((folder/'design'/f'{pid}.json').read_text())
 for sub in ['parts','design','verification','projects','stl']:(folder/sub).mkdir(parents=True,exist_ok=True)
 n=dict(np.load(OLD/'parts'/f'{pid}.npz'));old=json.loads((OLD/'design'/f'{pid}.json').read_text());ori=json.loads((O/'orientation'/f'{pid}.json').read_text())['ranked'][rank] if rank>=0 else dict(matrix_from_F4=np.eye(3).tolist(),bed_face_mm2=0.,xy_hull_area_mm2=1.);Q=np.array(ori['matrix_from_F4']);v=n['v']@Q.T;lift=0. if ori['bed_face_mm2']>max(8,ori['xy_hull_area_mm2']*.04)else 6.
 if lift_override is not None:lift=lift_override
 off=-v.min(0)+[0,0,lift];v+=off;body=solid(v,n['f']);gn=np.load(O/('guards_precise' if precise_guard else 'guards')/f'{pid}.npz');ban=solid(gn['v'],gn['f']).transform(np.c_[Q,off])-body;mesh=trimesh.Trimesh(v,n['f'],process=False);bb=np.array(body.bounding_box());height=bb[5];gap=5.2;thick=1.2 if height<60 else 1.6 if height<95 else 2.0;teeth=[];records=[];roots=[];segments=[];rejected=collections.Counter()
 # Start with geometric targets at reduced density; add only native-evidence contacts later.
 ys=np.arange(bb[1]+1.2,bb[4]+1.2,pitch);xs=np.arange(bb[0]+.3,bb[3],spacing);req=[(ri,yc,x+(yi-1)*.6,yt)for ri,yc in enumerate(ys)for yi,yt in enumerate([yc-pitch/3,yc,yc+pitch/3])for x in xs]
 targets=[]
 if req:
  hits,rr,ff=mesh.ray.intersects_location([[x,y,-.1]for _,_,x,y in req],np.tile([0,0,1.],(len(req),1)),multiple_hits=False)
  for h,idx,fidx in zip(hits,rr,ff):
   if h[2]<.55 or mesh.face_normals[fidx,2]>-.48:continue
   ri,yc,x,y=req[idx];targets.append(dict(row=ri,root_y=float(yc),x=float(x),y=float(y),roof=float(h[2]),normal=mesh.face_normals[fidx].tolist()))
 prev=polygon(body.slice(.1))
 for zz in np.arange(.3,height,.2):
  cur=polygon(body.slice(float(zz)))
  for cc in getattr(cur,'geoms',[cur]):
   if cc.is_empty or cc.area<.03 or cc.intersection(prev.buffer(.01)).area>.001:continue
   pp=cc.representative_point();hit,rr,ff=mesh.ray.intersects_location([[pp.x,pp.y,-.1]],[[0,0,1]],multiple_hits=False)
   if not len(hit)or abs(hit[0,2]-zz)>.25:continue
   ri=int(np.argmin(abs(ys-pp.y)));targets.append(dict(row=ri,root_y=float(ys[ri]),x=pp.x,y=pp.y,roof=float(hit[0,2]),normal=mesh.face_normals[ff[0]].tolist(),critical_foundation=True))
  prev=cur
 bedblock=(body^box(bb[:3]-[2,2,1],bb[3:]+[2,2,1])).slice(.3).offset(.5,circular_segments=8)if lift==0 else md.CrossSection()
 for ri,yc in enumerate(ys):
  group=[q for q in targets if q['row']==ri];raw=[]
  for q in group:
   h=min(a['roof']for a in group if abs(a['x']-q['x'])<1.25)-gap
   if h<.45:
    if q['roof']<2.:continue
    h=.6
   half=max(1.3,h*.23);x=q['x'];raw.append(md.CrossSection([[(x-half,0),(x+half,0),(x+1.3,h),(x-1.3,h)]]))
  if not raw:continue
  avoid=project_xz(slab(body,yc-thick/2-.2,yc+thick/2+.2,bb)).offset(.35,circular_segments=8)
  if not ban.is_empty():avoid+=project_xz(slab(ban,yc-thick/2-.05,yc+thick/2+.05,bb))
  profile=(cs_union(raw)-sweep2d(avoid,[0,height+5]))^md.CrossSection.square([bb[3]-bb[0]+6,height+5]).translate([bb[0]-3,0]);profile=cs_union([c for c in profile.decompose()if c.area()>.3 and c.bounds()[1]<1e-6])
  if profile.is_empty():continue
  for x0 in np.arange(bb[0]-height*.25-3,bb[3]+height*.25+3,26):
   cs=profile^md.CrossSection.square([24.,height+5]).translate([x0,0])
   for piece in cs.decompose():
    if piece.area()<1 or piece.bounds()[1]>1e-6:continue
    pg=polygon(piece);core=extrude_xz(piece,thick,float(yc));foot=(core.slice(.1).offset(1.1,circular_segments=8)-bedblock).extrude(.4);fin=(core+foot)-ban
    if(fin^body).volume()>1e-6:continue
    fs=[c for c in material_components(fin)if c.bounding_box()[2]<1e-6];fin=union(fs)
    if fin.is_empty():continue
    local=[];recs=[]
    for q in group:
     x=q['x'];h=q['roof'];line=pg.intersection(__import__('shapely').geometry.LineString([(x,0),(x,height+5)]))
     if line.is_empty:continue
     rootz=float(line.bounds[3])-.28;free=h-rootz-.28
     if not 1.1<free<8.8:rejected['free_length']+=1;continue
     a=np.array([x,yc,max(.15,rootz)]);b=np.array([x,q['y'],h+.18]);t=tooth(a,b);bite=t^body;bv=float(bite.volume())
     if not .008<bv<.9 or bite.bounding_box()[2]<h-1.:rejected['body_contact']+=1;continue
     if(t^ban).volume()>1e-7:rejected['protected']+=1;continue
     if(t^fin).volume()<.02:continue
     local.append(t);recs.append(dict(root=a.tolist(),tip=b.tolist(),target=[x,q['y'],h],free_vertical_mm=free,neck_xy_mm=[.8,.8],body_overlap_mm3=bv,fin_overlap_mm3=float((t^fin).volume()),critical_foundation=q.get('critical_foundation',False),kind='comb',row=int(ri)))
    if not local:continue
    tu=union(local);fin=union([c for c in material_components(fin)if(c^tu).volume()>.005]);roots.append(fin);teeth+=local;records+=recs;segments.append(dict(y=float(yc),bounds_mm=list(fin.bounding_box()),nominal_thickness_mm=thick))
 fins=union(roots);ts=union(teeth);assert(fins^body).volume()<1e-6 and((fins+ts)^ban).volume()<1e-6
 for g in material_components(fins):assert g.bounding_box()[2]<1e-6 and(g^ts).volume()>.005
 M=Q@np.array(old['orientation']['matrix']);t=Q@np.array(old['orientation']['source_translation_mm'])+off
 n['f4_print_v']=n['v'].copy();n['v']=v;n['fin_v'],n['fin_f']=vf(fins);n['teeth_v'],n['teeth_f']=vf(ts);np.savez_compressed(folder/'parts'/f'{pid}.npz',**n);gv,gf=vf(ban);np.savez_compressed(folder/'verification/guards.npz',v=gv,f=gf)
 d=dict(id=pid,part=old['part'],trial=label,orientation=dict(matrix=M.tolist(),source_translation_mm=t.tolist(),size_mm=np.ptp(v,axis=0).tolist()),f4_to_current_matrix=Q.tolist(),f4_to_current_translation_mm=off.tolist(),baseline='O22F4_Compact',baseline_source_mesh_preserved=old.get('source_mesh_preserved'),source_mesh_preserved=old.get('source_mesh_preserved'),part_body_modified_from_F4=False,body_f4_faces_identical=True,body_rigid_transform_only=True,required_layer_height_mm=.2,required_initial_layer_height_mm=.2,required_wall_generator='arachne',fuse_print_geometry=True,required_process_overrides={},style='open_bed_rooted_long_tooth_fins',nominal_pitch_mm=pitch,nominal_tooth_spacing_mm=spacing,nominal_tooth_free_height_mm=gap,teeth=records,segments=segments,support_count=len(material_components(fins)),support_volume_mm3=float((fins+ts).volume()),baseline_support_volume_mm3=old['support_volume_mm3'],baseline_tooth_record_count=len(old.get('teeth',[])),new_tooth_count=len(records),lift_mm=lift,orientation_rank=rank,construction_rejections=dict(rejected),physical_print_tested=False,native_pending=True)
 put(folder/'design'/f'{pid}.json',d);put(folder/'verification/construction.json',dict(id=pid,fin_body_intersection_mm3=float((fins^body).volume()),support_guard_intersection_mm3=float(((fins+ts)^ban).volume()),all_fins_bed_rooted=True,body_unchanged_from_F4=True));print('F5_BUILT',pid,label,'height',round(height,1),'lift',lift,'fins',d['support_count'],'teeth',len(records),'volume',round(d['support_volume_mm3']),flush=True);return d
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('ids',nargs='*');ap.add_argument('--label',default='open_a');ap.add_argument('--rank',type=int,default=0);args=ap.parse_args();inv=json.loads((O/'inventory.json').read_text());ids=args.ids or[g[0]for g in inv['groups']if next(x for x in inv['rows']if x['id']==g[0])['has_fins']and g[0]!='X062'];out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=3)as pool:
  futures={pool.submit(run,pid,args.label,args.rank):pid for pid in ids}
  for fut in concurrent.futures.as_completed(futures):
   try:out.append(fut.result());put(O/'build_progress.json',[dict(id=d['id'],label=d['trial'],teeth=d['new_tooth_count'],fins=d['support_count'])for d in out])
   except Exception as e:
    import traceback;traceback.print_exc();print('BUILD_ERROR',futures[fut],repr(e),flush=True)

