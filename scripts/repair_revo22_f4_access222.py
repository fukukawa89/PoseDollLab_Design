"""Build a bounded non-contact access opening with a short broad fin and verify actual contacts and native extrusion."""
from pathlib import Path
import sys,json,numpy as np,math,shapely
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,vf,union,box,md
from o22_material_components import material_components
from o22_reference_mesh import reference_solid
from o22_cross_section_geometry import polygon
from verify_revo22_f4_body_change import check as fit
from trim_revo22_f4_teeth117 import trial as trim
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def trial(pid,parent,label):
 src=O/'candidates'/pid/parent;dst=O/'candidates'/pid/label;n=dict(np.load(src/'parts'/f'{pid}.npz'));d=json.loads((src/'design'/f'{pid}.json').read_text());study=json.loads((src/'verification/access_feasibility221.json').read_text());s=solid(n['v'],n['f']);orig=reference_solid(n,d);best=None
 for opt in study['options']:
  angle=math.radians(opt['angle_deg']);A=np.array([[math.cos(angle),-math.sin(angle),0],[math.sin(angle),math.cos(angle),0],[0,0,1]]);c=np.array(opt['xy_mm']);p=np.array(opt['target']);w=opt['fin_width_mm'];th=opt['fin_thickness_mm'];h=opt['height_mm'];cutter=box([-w/2-.32,-th/2-.32,-.01],[w/2+.32,th/2+.32,h+.32]).transform(np.c_[A,[*c,0.]]);new=s-cutter;core=box([-w/2,-th/2,0],[w/2,th/2,h]).transform(np.c_[A,[*c,0.]]);root=box([-1.2,-.6,h-.25],[1.2,.6,h+.1]).transform(np.c_[A,[*c,0.]]);cap=box([p[0]-.5,p[1]-.6,p[2]-.15],[p[0]+.5,p[1]+.6,p[2]+.3]);tooth=md.Manifold.hull_points(np.r_[vf(root)[0],vf(cap)[0]]);pieces=[];prev=core.slice(.1)
  for z in np.arange(.3,p[2]+.4,.2):
   cs=tooth.slice(float(z))^prev.offset(.195,circular_segments=12)
   if not cs.is_empty():pieces.append(cs.extrude(.200002).translate([0,0,float(z-.100001)]))
   prev=core.slice(float(z))+cs
  tt=union(pieces)^tooth;bite=float((tt^new).volume());sec=polygon(tt.slice(p[2]-.2));cov=sec.intersection(shapely.Point(p[:2]).buffer(.12)).area/(math.pi*.12**2);print('ACCESS222_GROWTH',opt['angle_deg'],h,c.tolist(),bite,cov,flush=True)
  if bite<.015 or cov<.97:continue
  score=opt['removed_volume_mm3'];best=(opt,cutter,new,core,tt);break
 if best is None:print('ACCESS222_NO_INDEPENDENT_CONTACT',flush=True);return
 opt,cutter,new,core,tt=best;assert abs((s-new).volume()-opt['removed_volume_mm3'])<1e-4;assert len(material_components(new))==len(material_components(s));foot=core.slice(.1).offset(1.5,circular_segments=16).extrude(.4);foot=foot-(new^box([-300,-300,0],[300,300,.8])).project().offset(.35,circular_segments=12).extrude(.5);finnew=core+foot;assert(finnew^new).volume()<1e-6 and finnew.min_gap(new,.5)>.235
 fin=solid(n['fin_v'],n['fin_f'])+finnew;teeth=solid(n['teeth_v'],n['teeth_f'])+tt;teeth=union([x for x in material_components(teeth)if(x^new).volume()>.005 and(x^fin).volume()>.005]);fin=union([x for x in material_components(fin)if(x^teeth).volume()>.005]);n['source_f']=n.get('source_f',n['f']);n['v'],n['f']=vf(new);n['fin_v'],n['fin_f']=vf(fin);n['teeth_v'],n['teeth_f']=vf(teeth);n['removed_body_v'],n['removed_body_f']=vf(orig-new);num=len(d['segments'])+1;d['segments'].append({'number':num,'bounds_mm':list(finnew.bounding_box()),'height_mm':opt['height_mm'],'blade_width_mm':opt['fin_width_mm'],'blade_thickness_mm':opt['fin_thickness_mm'],'teeth_count':1,'brace_count':0,'on_build_plate':True,'vertical_bed_path':True,'min_gap_mm':float(finnew.min_gap(new,.5)),'removal_vector':[0,0,-1],'through_permanent_support_access_window':True});d['teeth'].append({'fin_number':num,'bounds_mm':list(tt.bounding_box()),'part_bite_mm3':float((tt^new).volume()),'fin_root_mm3':float((tt^finnew).volume()),'neck_xy_mm':[1,1.2],'nominal_tip_penetration_mm':.3,'contact_point_mm':opt['target'],'short_connector_horizontal_reach_mm':float(np.linalg.norm(np.array(opt['target'])[:2]-opt['xy_mm'])),'connector_rise_mm':opt['target'][2]-opt['height_mm']});d.update(source_mesh_preserved=False,support_count=len(d['segments']),support_volume_mm3=float((fin+teeth).volume()),body_part_overlap_mm3=float((fin^new).volume()));d['body_change']={'kind':'noncontact_support_access_opening','removed_volume_mm3':float((orig-new).volume()),'added_volume_mm3':0.,'source_body_volume_mm3':float(orig.volume()),'assembly_contact_validation_pending':True,'chamfers':[{'kind':'support_access_window','local_bounds_mm':list(cutter.bounding_box()),'removed_volume_mm3':float((s-new).volume()),'read_only_preinspection':opt,'purpose':'A short broad fin begins on the bed and enters through a permanent opening in a non-contact wall. Washer bearing faces and joint axes must pass unchanged contact checks.'}]}
 for sub in['parts','design','verification']:(dst/sub).mkdir(parents=True,exist_ok=True)
 np.savez_compressed(dst/'parts'/f'{pid}.npz',**n);(dst/'design'/f'{pid}.json').write_text(json.dumps(d,indent=2));r=fit(pid,label)
 if r['fit_and_pose_geometry_passed']:trim(pid,label,label+'_self')
if __name__=='__main__':trial(*sys.argv[1:])
