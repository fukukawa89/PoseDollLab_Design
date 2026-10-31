"""F2: direct-to-bed broad vertical fins, positive-volume breakaway teeth.
Geometric construction only; no claim of FEM or physical qualification.
"""
from pathlib import Path
import sys,json,math,time,argparse,collections
import numpy as np
import manifold3d as md
from pack_revo22_a1mini import read_mesh
from build_revo22_fins import solid,vf,box,union,cs_union,protected,slab,project_xz,extrude_xz,strip_targets,sweep2d,polygon,write_stl,intervals,exit_clear
R=Path(__file__).resolve().parents[1];B=R/'Hardware/PoseDoll44/bench/revO22';O=B/'a1mini_fins_v3';D=B/'a1mini_supports/design'
sys.path.insert(0,str(R/'.local/fins-deps'))
from shapely.geometry import LineString
import trimesh
GAP=.28
AXIS=None
FACE_FILTER=None
PITCH_OVERRIDE=None
THICKNESS_OVERRIDE=None
NORMAL_THRESHOLD=-.7071
SEGMENT_OVERRIDE=None

def choose(pid):
 d=json.loads((O/'orientation'/f'{pid}.json').read_text());rank=d['ranked_candidates'];best=rank[0]['score']
 if pid=='X046':return min(rank,key=lambda c:c['size_mm'][2])
 candidates=[c for c in rank if c['score']<=best*1.55+400 and c['bed_contact_projection_mm2']>=3]
 if not candidates:candidates=rank[:5]
 return min(candidates,key=lambda c:c['score']*(1+2/(c['bed_contact_projection_mm2']+1)+(.04 if max(abs(np.array(c['gravity_in_source'])))<.999999 else 0))+150*c['size_mm'][2]**2)

def make(pid,it,vols):
 srcv,f=read_mesh(B/it['source_3mf']);ori=choose(pid);M=np.array(ori['matrix']);t=np.array(ori['source_translation_mm']);v=srcv@M.T+t;s=solid(v,f);ban=protected(vols).transform(np.c_[M,t]);bb=s.bounding_box()
 tri=v[f];cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);areas=np.linalg.norm(cross,axis=1);nz=cross[:,2]/np.maximum(areas,1e-20)
 faces=np.where((nz<(-.3 if FACE_FILTER is not None else NORMAL_THRESHOLD))&(tri[:,:,2].max(axis=1)>.6))[0]
 if FACE_FILTER is not None:faces=np.intersect1d(faces,FACE_FILTER)
 tris=tri[faces]
 # Bed-accessible fin panels. No lateral route around an intervening part is allowed.
 tm=trimesh.Trimesh(v,f,process=False)
 chunks=[];allteeth=[];records=[];rejected=collections.Counter()
 height=float(bb[5]);thick=1.2 if height<45 else 1.6 if height<65 else 2.4
 pitch=PITCH_OVERRIDE or (3.0 if height<45 else 5.0)
 if THICKNESS_OVERRIDE is not None:thick=THICKNESS_OVERRIDE
 # Explicit region prescriptions: transverse blade orientation chosen for long frames.
 axis=AXIS if AXIS is not None else (90 if pid in ['W016','W017','W006','W007'] else 0)
 if axis:
  az=math.radians(axis);A=np.array([[math.cos(az),-math.sin(az),0],[math.sin(az),math.cos(az),0],[0,0,1]],float);v=v@A.T;s=s.transform(np.c_[A,[0,0,0]]);ban=ban.transform(np.c_[A,[0,0,0]]);tris=tris@A.T;tm=trimesh.Trimesh(v,f,process=False);bb=s.bounding_box()
 else:A=np.eye(3)
 def to_out(q):return q.transform(np.c_[A.T,[0,0,0]])
 toothrecs=[]
 critical=[];prev=s.slice(.1)
 for zz in np.arange(.3,bb[5],.2):
  cur=s.slice(float(zz))
  for cc in cur.decompose():
   if cc.area()>.03 and (cc^prev.offset(.02)).area()<1e-7:
    pp=polygon(cc).representative_point();critical.append((pp.x,pp.y,float(zz)))
  prev=cur
 regular=list(np.arange(bb[1]+thick/2+.25,bb[4]-.25,pitch));ys=sorted(set(round(float(yy),5) for yy in regular+([c[1] for c in critical] if FACE_FILTER is None else [])))
 for row,y in enumerate(ys):
  nearby_critical=[c for c in critical if abs(c[1]-y)<.01]
  target=strip_targets(tris,y)
  if target.is_empty():continue
  silhouette=project_xz(slab(s,y-thick/2-GAP,y+thick/2+GAP,bb)).offset(GAP,circular_segments=12)
  no=project_xz(slab(ban,y-thick/2-.1,y+thick/2+.1,bb)) if not ban.is_empty() else md.CrossSection()
  avoid=silhouette+no
  shadow=sweep2d(avoid,[0,height+5]);clear=target-shadow
  # Shorter independent segments keep removal practical; high panels get wider roots.
  segment=SEGMENT_OVERRIDE or (14 if height<45 else 22 if height<65 else 36)
  for x0 in np.arange(bb[0]-.5,bb[3],segment+1.2):
   window=md.CrossSection.square([segment,height+5]).translate([x0,0])
   for cs in (clear^window).decompose():
    if cs.area()<1:continue
    poly=polygon(cs);lo=poly.bounds
    h=lo[3];w=lo[2]-lo[0]
    if lo[1]>.001:rejected['not_vertical_bed_reachable']+=1;continue
    if w<max(1.4,h/4):rejected['narrow_high_panel']+=1;continue
    # Eliminate tall narrow crests. Every band above z must provide >=z/4 breadth.
    # Trim only the slender top fringe; retain the broad vertical panel below it.
    # Rejecting a whole sloping panel because its final tip narrows caused F2 gaps.
    trim_h=h
    for z in np.arange(5,h,.5):
     spans=intervals(cs,float(z));width=sum(r-l for l,r in spans)
     if width<min(2.4,z/6):trim_h=float(z)-.05;break
    if trim_h<h:
     cs=cs^md.CrossSection.square([w+2,trim_h]).translate([lo[0]-1,0])
     if cs.is_empty():continue
     poly=polygon(cs);lo=poly.bounds;h=lo[3];w=lo[2]-lo[0]
    core=extrude_xz(cs,thick,float(y));toothlist=[];tr=[]
    xs=list(np.arange(lo[0]+.45,lo[2]-.3,1.8))+[c[0] for c in nearby_critical if lo[0]+.25<c[0]<lo[2]-.25]
    for x in sorted(set(round(float(xx),5) for xx in xs)):
     cut=poly.intersection(LineString([(x,0),(x,height+2)]))
     if cut.is_empty:continue
     z=float(cut.bounds[3])
     if z<.35:continue
     # Vertical ray finds first physical part surface above this bed column.
     hit,ri,fi=tm.ray.intersects_location(np.array([[x,y,-.1]]),np.array([[0,0,1.]]),multiple_hits=False)
     if not len(hit):continue
     roof=float(hit[0,2]);length=roof-z
     if not .1<length<3.5:continue
     # Contact tip follows the actual hit triangle plane, avoiding deep edge bites.
     face=tm.triangles[int(fi[0])];normal=tm.face_normals[int(fi[0])]
     if abs(normal[2])<.15:continue
     corners=np.array([[xx,yy] for xx in [x-.35,x+.35] for yy in [y-.4,y+.4]])
     tops=roof-((corners-np.array([x,y]))@normal[:2])/normal[2]+.16
     bottom=max(0,z-.4)
     if tops.min()<=bottom+.2:continue
     tooth=md.Manifold.hull_points(np.vstack([np.c_[corners,np.full(4,bottom)],np.c_[corners,tops]]))
     bite=float((tooth^s).volume());root=float((tooth^core).volume())
     if bite<.018 or bite>.35 or root<.06 or (tooth^ban).volume()>1e-7:continue
     toothlist.append(tooth);tr.append({'bounds_mm':list(to_out(tooth).bounding_box()),'part_bite_mm3':bite,'fin_root_mm3':root,'nominal_tip_penetration_mm':.16,'neck_xy_mm':[.7,.8],'contact_point_mm':(np.array([x,y,roof])@A).tolist()})
    minimum=1 if h<12 and w>=2 else 2
    if len(toothlist)<minimum:rejected['insufficient_real_contacts']+=1;continue
    # 0.4-mm foot adheres directly to bed; 2.0-mm expansion prevents a knife-edge base.
    footprint=core.slice(.01).offset(2.,circular_segments=16)
    nearby=project_xz(md.Manifold()) if False else (s^box([bb[0]-5,bb[1]-5,0],[bb[3]+5,bb[4]+5,.7])).project().offset(.4,circular_segments=16)
    foot=(footprint-nearby).extrude(.4)
    if not ban.is_empty():foot=foot-ban
    body=core+foot
    if (body^s).volume()>1e-7 or (body^ban).volume()>1e-7:rejected['collision']+=1;continue
    # Perpendicular buttresses on tall blades broaden the weak bending axis.
    braces=[]
    if h>35:
     for bx in np.arange(lo[0]+2,lo[2]-1,6):
      cut=poly.intersection(LineString([(bx,0),(bx,height+2)]))
      if cut.is_empty:continue
      zh=float(cut.bounds[3]);bh=max(0,zh-1.)
      if bh<8:continue
      for sign in [-1,1]:
       b=box([bx-.7,min(y,y+sign*3.2),0],[bx+.7,max(y,y+sign*3.2),bh])
       if (b^s).volume()<1e-7 and (b^ban).volume()<1e-7 and float(b.min_gap(s,.25))>.2:braces.append(b)
    body=union([body]+braces)
    if len(body.decompose())!=1:rejected['disconnected_foot']+=1;continue
    removal=None
    if exit_clear(core,foot,s,2,-1) and all(exit_clear(br,md.Manifold(),s,2,-1) for br in braces):removal=np.array([0,0,-1.])
    if removal is None:rejected['no_straight_removal']+=1;continue
    chunks.append(to_out(body));allteeth.extend(to_out(t) for t in toothlist)
    index=len(chunks)
    for r in tr:r['fin_number']=index
    toothrecs.extend(tr)
    records.append({'number':index,'bounds_mm':list(to_out(body).bounding_box()),'height_mm':h,'blade_width_mm':w,'blade_thickness_mm':thick,'teeth_count':len(tr),'brace_count':len(braces),'removal_vector':(removal@A).tolist(),'on_build_plate':True,'vertical_bed_path':True,'min_gap_mm':float(body.min_gap(s,.5))})
 bodies=union(chunks);teeth=union(allteeth);part=solid(srcv@M.T+t,f)
 assert (bodies^part).volume()<1e-6
 for c in bodies.decompose():assert c.bounding_box()[2]<1e-5
 for c in bodies.decompose():assert (c^teeth).volume()>.02
 for tt in teeth.decompose():assert (tt^bodies).volume()>.02 and (tt^part).volume()>.01
 vv=srcv@M.T+t
 np.savez_compressed(O/'parts'/f'{pid}.npz',v=vv,f=f,source_v=srcv,fin_v=vf(bodies)[0],fin_f=vf(bodies)[1],teeth_v=vf(teeth)[0],teeth_f=vf(teeth)[1])
 rep={'id':pid,'part':it['part'],'orientation':ori,'source_mesh_preserved':True,'support_count':len(chunks),'segments':records,'teeth':toothrecs,'rejected':dict(rejected),'source_height_mm':float(np.ptp(srcv[:,2])),'new_height_mm':float(np.ptp(vv[:,2])),'min_gap_mm':min([r['min_gap_mm'] for r in records],default=None),'body_part_overlap_mm3':float((bodies^part).volume()),'teeth_part_overlap_mm3':float((teeth^part).volume()),'support_volume_mm3':float((bodies+teeth).volume()),'source_island_targets':len(critical),'note':'Geometric candidate; slicing and removal validation required'}
 (O/'design'/f'{pid}.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding='utf-8')
 return rep

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--id',nargs='*');a=ap.parse_args()
 for d in ['parts','design','verification']:(O/d).mkdir(exist_ok=True)
 u={i['id']:i for p in json.loads((B/'a1mini/manifest.json').read_text())['plates'] if not p['optional'] for i in p['items']}
 vols={i['part']:i['volumes'] for i in json.loads((D/'all_protected_volumes.json').read_text())['objects']}
 for pid,it in u.items():
  if a.id and pid not in a.id:continue
  st=time.time();r=make(pid,it,vols.get(it['part'],[]));print(pid,r['support_count'],len(r['teeth']),r['source_height_mm'],r['new_height_mm'],r['rejected'],round(time.time()-st,1),flush=True)
if __name__=='__main__':main()
