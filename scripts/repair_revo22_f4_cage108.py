"""Broad four-sided fin cage with cross ribs, grown solely from the build plate.
Layerwise reachability routes around the original part in 3-D, with no body edits.
"""
from pathlib import Path
import sys,json,numpy as np,trimesh,shapely,math,time
from shapely.geometry import box as rect,Point
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,vf,box,union,md
from o22_cross_section_geometry import polygon
from o22_material_components import material_components
from repair_revo22_f4_envelope80 import cs
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
from refine_revo22_f4_lateral104 import check as refine
from verify_revo22_f4_body_change import check as fit
from verify_revo22_f4_repaired_geometry import check as geom
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'

def trial(pid,parent,label):
 src=O/'candidates'/pid/parent;dst=O/'candidates'/pid/label
 for sub in ['parts','design','verification']:(dst/sub).mkdir(parents=True,exist_ok=True)
 n=dict(np.load(src/'parts'/f'{pid}.npz'));d=json.loads((src/'design'/f'{pid}.json').read_text());s=solid(n['v'],n['f']);fin=solid(n['fin_v'],n['fin_f']);teeth=solid(n['teeth_v'],n['teeth_f']);tm=trimesh.Trimesh(n['v'],n['f'],process=False);aud=src/'verification/full_bead_contacts_v5.json';aud=aud if aud.exists()else src/'verification/full_bead_contacts_v2.json';q=json.loads(aud.read_text());it=json.loads((src/'verification/plate_manifest.json').read_text())['items'][0];M=np.array(it['rotation_matrix']);off=np.array(it['translation_mm']);added=[]
 for issue in q['external_islands']+q['critical_external_runs']:
  bb=issue['bounds_mm'];p=(np.array([(bb[0]+bb[2])/2,(bb[1]+bb[3])/2,issue['z_mm']-.1])-off)@M;region=polygon(s.slice(p[2])).intersection(rect(p[0]-.45,p[1]-.45,p[0]+.45,p[1]+.45))
  if region.is_empty:print('CAGE108_NO_SECTION',pid,p,flush=True);continue
  pp=region.representative_point();p[:2]=[pp.x,pp.y];hits,_,faces=tm.ray.intersects_location([[*p[:2],-.1]],[[0,0,1]],multiple_hits=True);hits=[h for h,f in zip(hits,faces)if tm.face_normals[f,2]<-.15 and p[2]-1.2<h[2]<p[2]+.3]
  if not hits:print('CAGE108_NO_ROOF',pid,p,flush=True);continue
  roof=float(min(hits,key=lambda h:abs(h[2]-p[2]))[2]);height=math.floor((roof-2.4)/.2)*.2;rad=.6*height+4.;limit=rect(p[0]-rad,p[1]-rad,p[0]+rad,p[1]+rad);bodyclip=s^box([p[0]-rad-1,p[1]-rad-1,-.5],[p[0]+rad+1,p[1]+rad+1,roof+1]);previous=None;levels=[];dz=.2;st=time.time()
  fullsize=np.ptp(np.r_[n['v'],n['fin_v'],[[p[0]-rad,p[1]-rad,0],[p[0]+rad,p[1]+rad,height]]],axis=0)
  if max(fullsize[:2])>169:print('CAGE108_BED_REJECT',pid,fullsize,flush=True);continue
  for j,z in enumerate(np.arange(0,height-.001,dz)):
   r=.6*(height-z);outer=rect(p[0]-r-4,p[1]-r-4,p[0]+r+4,p[1]+r+4);inner=rect(p[0]-max(0,r-.8),p[1]-max(0,r-.8),p[0]+max(0,r-.8),p[1]+max(0,r-.8));template=outer.difference(inner).union(rect(p[0]-1.6,p[1]-r-4,p[0]+1.6,p[1]+r+4)).union(rect(p[0]-r-4,p[1]-1.6,p[0]+r+4,p[1]+1.6));slab=bodyclip^box([p[0]-rad-1,p[1]-rad-1,z-.35],[p[0]+rad+1,p[1]+rad+1,z+dz+.35]);blocked=polygon(slab.project()).buffer(.35,quad_segs=6);free=template.difference(blocked);reachable=free if previous is None else free.intersection(previous.buffer(.15,quad_segs=6));reachable=reachable.buffer(-.8,quad_segs=6).buffer(.8,quad_segs=6).intersection(reachable);previous=reachable
   if reachable.is_empty:break
   levels.append(cs(reachable).extrude(dz+.000002).translate([0,0,float(z)]))
   if j%75==0:print('CAGE108_LAYER',pid,j,'area',reachable.area,'s',round(time.time()-st,1),flush=True)
  if len(levels)<int(round(height/dz)):print('CAGE108_NO_ROUTE',pid,p,len(levels),flush=True);continue
  core=union(levels);top_section=polygon(core.slice(height-.05));best=None
  for dx in np.arange(-2.4,2.401,.4):
   for dy in np.arange(-2.4,2.401,.4):
    c=p[:2]+[dx,dy];reach=float(np.linalg.norm([dx,dy]))
    if reach>2.4001:continue
    for a in np.arange(0,np.pi,np.pi/6):
     A=np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]]);rxy=np.array([[x,y]for x in[-.8,.8]for y in[-1.4,1.4]])@A+c;rootpoly=shapely.MultiPoint(rxy).convex_hull
     if rootpoly.difference(top_section).area>.015:continue
     tt=md.Manifold.hull_points(np.array([[xy[0],xy[1],z]for xy in rxy for z in[height-.25,height+.15]]+[[p[0]+x,p[1]+y,z]for x in[-.5,.5]for y in[-.5,.5]for z in[roof+.1,roof+.35]]));bite=float((tt^s).volume());root=float((tt^core).volume())
     if bite<.01 or bite>.85 or root<.1:continue
     if(tt^s^box([-300,-300,0],[300,300,roof-.31])).volume()>1e-6:continue
     if best is None or reach<best[0]:best=(reach,tt,bite,root)
  if best is None:print('CAGE108_NO_SHORT_CONTACT',pid,'top_area',top_section.area,flush=True);continue
  reach,tooth,bite,root=best;print('CAGE108_CONTACT',pid,bite,root,reach,flush=True)
  core=union([c for c in material_components(core)if(c^tooth).volume()>.005]);foot=core.slice(.1).offset(1.5,circular_segments=12).extrude(.4);foot=foot-(s^box([-300,-300,0],[300,300,.8])).project().offset(.35,circular_segments=12).extrude(.5);bod=core+foot
  if float((bod^s).volume())>1e-6 or bod.min_gap(s,.5)<.235:print('CAGE108_COLLISION',pid,flush=True);continue
  ribrecords=[]
  for axis in [0,1]:
   lo=[p[0]-rad-1,p[1]-rad-1,0];hi=[p[0]+rad+1,p[1]+rad+1,height];lo[axis]=p[axis]-1.59;hi[axis]=p[axis]+1.59;rib=core^box(lo,hi);rooted=[c for c in material_components(rib)if c.bounding_box()[2]<1e-5 and c.bounding_box()[5]>height*.5 and c.volume()>height*4];ribrecords.extend({'axis':axis,'volume_mm3':float(c.volume()),'height_mm':float(c.bounding_box()[5]),'bed_area_mm2':float(c.slice(.1).area())}for c in rooted)
  if height>35 and len(ribrecords)<2:print('CAGE108_BRACES_REJECT',pid,ribrecords,flush=True);continue
  fin=fin+bod;teeth=teeth+tooth;num=len(d['segments'])+1;row={'number':num,'bounds_mm':list(bod.bounding_box()),'height_mm':height,'blade_width_mm':2*rad,'blade_thickness_mm':4.,'teeth_count':1,'brace_count':len(ribrecords),'actual_cross_ribs':ribrecords,'on_build_plate':True,'vertical_bed_path':False,'bed_connected_portal':True,'modeled_growth_xy_per_z':.75,'layer_step_mm':.2,'minimum_root_width_mm':3.2,'min_gap_mm':float(bod.min_gap(s,.5)),'three_dimensional_fin_frame':True,'removal_requires_cutting_portal_crown':True,'removal_instruction':'Sever teeth, cut four broad fin panels and transverse ribs into short sections; remove all pieces before assembly.'};d['segments'].append(row);d['teeth'].append({'fin_number':num,'bounds_mm':list(tooth.bounding_box()),'part_bite_mm3':bite,'fin_root_mm3':root,'neck_xy_mm':[1,1],'nominal_tip_penetration_mm':.35,'contact_point_mm':[*p[:2],roof]});added.append(row);print('CAGE108_ADDED',pid,'volume',bod.volume(),'ribs',len(ribrecords),flush=True)
 n['fin_v'],n['fin_f']=vf(fin);n['teeth_v'],n['teeth_f']=vf(teeth);d.update(support_count=len(d['segments']),support_volume_mm3=float((fin+teeth).volume()),three_dimensional_frames108=added);np.savez_compressed(dst/'parts'/f'{pid}.npz',**n);(dst/'design'/f'{pid}.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');print('CAGE108_DONE',pid,len(added),flush=True)
 if not added:return
 if 'body_change'in d:fit(pid,label)
 g=geom(pid,label)
 if not g['geometric_constraints_passed']:return
 run(pid,label);check(pid,label);refine(pid,label)
if __name__=='__main__':trial(*sys.argv[1:])
