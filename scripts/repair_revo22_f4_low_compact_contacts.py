"""Short side teeth from broad vertical bed fins; never put a fin on a part."""
import sys,json,math
import numpy as np
from build_revo22_fins_v3 import *
from check_revo22_f3_layers import check
from o22_cross_section_geometry import polygon
from o22_material_components import material_components
from shapely.geometry import Point
from shapely.ops import nearest_points

def repair_side(pid):
 n=dict(np.load(O/'parts'/f'{pid}.npz'));r=json.loads((O/'design'/f'{pid}.json').read_text());s=solid(n['v'],n['f']);b=solid(n['fin_v'],n['fin_f']) if len(n['fin_f']) else md.Manifold();teeth=solid(n['teeth_v'],n['teeth_f']) if len(n['teeth_f']) else md.Manifold();tm=trimesh.Trimesh(n['v'],n['f'],process=False)
 vols=next((x['volumes'] for x in json.loads((D/'all_protected_volumes.json').read_text())['objects'] if x['part']==r['part']),[]);M=np.array(r['orientation']['matrix']);off=np.array(r['orientation']['source_translation_mm']);ban=md.Manifold();d=json.loads((O/'verification'/f'{pid}_layers.json').read_text());targets=list(d['combined_floating_islands'])
 # Prefer actual printed island positions when this exact orientation was sliced.
 qc=O/'verification'/f'QC_{pid}_ORCA_extrusion_contacts.json';pm=O/'verification'/f'QC_{pid}_ORCA_manifest.json'
 if qc.exists() and pm.exists():
  it=json.loads(pm.read_text())['items'][0];MM=np.array(it['rotation_matrix']);tt=np.array(it['translation_mm'])
  for x in json.loads(qc.read_text())['floating_printed_components']:
   bb=x['bounds_mm'];pts=np.array([[xx,yy,x['z_mm']-.1] for xx in [bb[0],bb[2]] for yy in [bb[1],bb[3]]]);pts=(pts-tt)@MM;q={'z_mm':x['z_mm']-.1,'bounds':[pts[:,0].min(),pts[:,1].min(),pts[:,0].max(),pts[:,1].max()],'from_gcode':True}
   if 'point_mm' in x:q['preferred_point_mm']=((np.array([*x['point_mm'],x['z_mm']-.1])-tt)@MM)[:2].tolist()
   targets.append(q)
 added=[];reasons=__import__('collections').Counter();body_chunks=[b];tooth_chunks=[teeth];projection_cache={};sbb=np.array(s.bounding_box())
 for ti,target in enumerate(targets):
  if ti%100==0:print('CONTACT_PROGRESS',pid,ti,len(targets),'added',len(added),flush=True)
  z=float(target['z_mm']);
  if z>20.0:continue
  bb=target['bounds'];region=md.CrossSection.square([bb[2]-bb[0]+.08,bb[3]-bb[1]+.08]).translate([bb[0]-.04,bb[1]-.04]);cs=s.slice(z)^region
  if cs.is_empty():continue
  poly=polygon(cs);pt=poly.representative_point()
  if 'preferred_point_mm' in target:
   pp=poly.buffer(-.01);pp=pp if not pp.is_empty else poly;pt=nearest_points(pp,Point(target['preferred_point_mm']))[0]
  p=np.array([pt.x,pt.y,z]);done=False
  if not target.get('from_gcode'):
   curr=(s+b+teeth).slice(z)
   nearby=min(curr.decompose(),key=lambda c:np.linalg.norm(np.array(c.bounds())-np.array(bb)))
   if (nearby^((s+b+teeth).slice(max(.01,z-.2)).offset(.025))).area()>1e-5:continue
  for theta in np.arange(0,360,5):
   rad=math.radians(theta);direction=np.array([math.cos(rad),math.sin(rad),0]);tangent=np.array([-direction[1],direction[0],0]);rot=np.array([tangent,-direction,[0,0,1.]]).T
   for dist in np.arange(.6,5.01,.2):
    c=p+direction*dist;c[2]=0;target_h=z+.25;thick=.8 if target_h<12 else 1.2;h=z-1.3*max(.3,dist-thick/2);width=max(1.8,target_h/4)
    if h<.5:continue
    hk=math.ceil(float(h)*2)/2
    if hk not in projection_cache:projection_cache[hk]=(s^box([sbb[0]-1,sbb[1]-1,-.01],[sbb[3]+1,sbb[4]+1,hk])).project()
    xy=np.array([[-width/2,-thick/2],[width/2,-thick/2],[width/2,thick/2],[-width/2,thick/2]])@rot[:2,:2].T+c[:2]
    if (md.CrossSection([xy])^projection_cache[hk]).area()>1e-8:reasons['projected_core_part_collision']+=1;continue
    core=box([-width/2,-thick/2,0],[width/2,thick/2,h]).transform(np.c_[rot,c])
    if (core^s).volume()>1e-8:reasons['core_part_collision']+=1;continue
    if (core^ban).volume()>1e-8:reasons['core_guard_collision']+=1;continue
    if float(core.min_gap(s,.3))<.235:reasons['core_small_clearance']+=1;continue
    # Ray from the body side toward the target identifies the outer surface.
    origin=p+direction*(dist+thick/2+.1);hits,_,_=tm.ray.intersects_location([origin],[-direction],multiple_hits=False)
    if not len(hits):reasons['ray_no_hit']+=1;continue
    hit=hits[0]
    if np.linalg.norm(hit[:2]-p[:2])>(.45 if 'preferred_point_mm' in target else 2.0):reasons['ray_wrong_surface']+=1;continue
    start=c-direction*(thick/2-.3);start[2]=0;length=float(np.dot(start-hit,direction))+.16
    if not .25<length<3.5:reasons['tooth_too_long']+=1;continue
    roof=z+.35;bottom=max(0,h-.75)
    if length/max(.01,z-h)>.9:continue
    prof=md.CrossSection([[[0,bottom],[length,max(0,z-.45)],[length,roof],[0,h+.25]]])
    A=np.array([[-direction[0],direction[1],0],[-direction[1],-direction[0],0],[0,0,1.]])
    tooth=extrude_xz(prof,1.2,0).transform(np.c_[A,start]);bite=float((tooth^s).volume());root=float((tooth^core).volume())
    if bite<.02 or bite>.6 or root<.06:reasons['tooth_contact_geometry']+=1;continue
    early=box([-.01,-.65,0],[max(.01,length-.4),.65,roof+1]).transform(np.c_[A,start])
    if (tooth^s^early).volume()>1e-6:reasons['tooth_contact_before_tip']+=1;continue
    if (tooth^ban).volume()>1e-8:reasons['tooth_guard_collision']+=1;continue
    foot=box([-width/2-2,-thick/2-2,0],[width/2+2,thick/2+2,min(.4,h)]).transform(np.c_[rot,c])
    if (foot^s).volume()>1e-8 or (foot^ban).volume()>1e-8 or float(foot.min_gap(s,.3))<.235:foot=md.Manifold()
    braces=[]
    if h>35:
     for bx in [-width/3,0,width/3]:
      brace=box([bx-.7,-4,0],[bx+.7,4,h-12]).transform(np.c_[rot,c])
      if (brace^s).volume()<1e-8 and (brace^ban).volume()<1e-8 and float(brace.min_gap(s,.3))>.235:braces.append(brace)
     if not braces:reasons['unbraced_tall_blade']+=1;continue
    body=union([core,foot]+braces)
    if str(body.status())!='Error.NoError' or str(tooth.status())!='Error.NoError':continue
    body_chunks.append(body);tooth_chunks.append(tooth);num=len(r['segments'])+1
    r['segments'].append({'number':num,'bounds_mm':list(body.bounding_box()),'height_mm':h,'blade_width_mm':width,'blade_thickness_mm':thick,'teeth_count':1,'brace_count':len(braces),'on_build_plate':True,'vertical_bed_path':True,'min_gap_mm':float(body.min_gap(s,.5)),'removal_vector':[0,0,-1],'side_contact':True,'low_wide_fin':True,'maximum_height_mm':20.,'minimum_width_to_height_ratio':.25})
    r['teeth'].append({'bounds_mm':list(tooth.bounding_box()),'part_bite_mm3':bite,'fin_root_mm3':root,'nominal_tip_penetration_mm':.16,'neck_xy_mm':[1.2,length],'contact_point_mm':hit.tolist(),'fin_number':num,'side_tooth_length_mm':length,'note':'Short, 1.2 mm wide connector from a low broad vertical fin; upright fin body stays directly bed-rooted. Connector slope has at least 1.1 mm vertical rise per mm reach, with part intersection only in the last 0.4 mm of the tip.'})
    added.append(target);done=True;break
   if done:break
 b=union(body_chunks);teeth=union(tooth_chunks)
 r["enclosed_tooth_void_volume_mm3"]=sum(-float(p.volume()) for p in teeth.decompose() if p.volume()<0)
 assert str(b.status())=='Error.NoError' and (b^s).volume()<1e-6
 bad=[{'volume':float(tt.volume()),'root':float((tt^b).volume()),'bite':float((tt^s).volume()),'bounds':list(tt.bounding_box())} for tt in material_components(teeth) if (tt^b).volume()<=.005 or (tt^s).volume()<=.005]
 assert not bad,bad
 n.update(fin_v=vf(b)[0],fin_f=vf(b)[1],teeth_v=vf(teeth)[0],teeth_f=vf(teeth)[1]);np.savez_compressed(O/'parts'/f'{pid}.npz',**n);r.update(support_count=len(r['segments']),min_gap_mm=min([x['min_gap_mm'] for x in r['segments']],default=None),body_part_overlap_mm3=float((b^s).volume()),teeth_part_overlap_mm3=float((teeth^s).volume()),support_volume_mm3=float((b+teeth).volume()),side_contacts_added=added,side_contact_rejections=dict(reasons),side_contact_target_count=len(targets),temporary_void_supports_must_be_removed=True);(O/'design'/f'{pid}.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print('SIDE',pid,'added',len(added),'targets',len(targets),'rejections',dict(reasons),flush=True);check(pid)
if __name__=='__main__':
 for pid in sys.argv[1:]:repair_side(pid)