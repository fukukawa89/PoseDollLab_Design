"""Implement only the two independently inspected, bounded support-access proposals."""
from pathlib import Path
import sys,json,numpy as np,math,concurrent.futures,traceback
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,box,union,vf,md
from o22_material_components import material_components
from o22_reference_mesh import reference_solid
from verify_revo22_f4_body_change import check as fit
from verify_revo22_f4_repaired_geometry import check as geom
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
from refine_revo22_f4_lateral104 import check as refine
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'

def trial(spec):
 pid,parent=spec.split(':');assert(pid,parent)in[('X046','portal88'),('X042','complete58_01')];label='access106';src=O/'candidates'/pid/parent;dst=O/'candidates'/pid/label
 for sub in ['parts','design','verification']:(dst/sub).mkdir(parents=True,exist_ok=True)
 n=dict(np.load(src/'parts'/f'{pid}.npz'));d=json.loads((src/'design'/f'{pid}.json').read_text());study=json.loads((src/'verification/combined_access_windows106.json').read_text());s=solid(n['v'],n['f']);original=reference_solid(n,d);cuts=[];cores=[]
 assert study['maximum_global_XY_section_fraction_removed']<.06 and study['result_components']==study['source_components']==1
 for q in study['options']:
  a=math.radians(q['angle_deg']);A=np.array([[math.cos(a),-math.sin(a),0],[math.sin(a),math.cos(a),0],[0,0,1.]]);w=q['fin_width_mm'];th=q['fin_thickness_mm'];T=np.c_[A,[*q['xy_mm'],0]];cuts.append(box([-w/2-.32,-th/2-.32,-.01],[w/2+.32,th/2+.32,q['height_mm']+.32]).transform(T));cores.append(box([-w/2,-th/2,0],[w/2,th/2,q['height_mm']]).transform(T))
 new=s-union(cuts);delta=original-new;assert abs(delta.volume()-study['combined_total_removed_mm3'])<1e-5;assert delta.volume()<({'X046':71.,'X042':47.}[pid]);assert len(material_components(new))==1 and(new-original).volume()<1e-6;fin=solid(n['fin_v'],n['fin_f']);teeth=solid(n['teeth_v'],n['teeth_f']);rows=[]
 for core,cut,q,issue in zip(cores,cuts,study['options'],study['issues']):
  foot=core.slice(.1).offset(2,circular_segments=16).extrude(.4);foot=foot-(new^box([-300,-300,0],[300,300,.8])).project().offset(.35,circular_segments=12).extrude(.5);finnew=core+foot;tooth=box([q['xy_mm'][0]-.5,q['xy_mm'][1]-.5,q['height_mm']-.25],[q['xy_mm'][0]+.5,q['xy_mm'][1]+.5,q['roof_mm']+.35]);bite=float((tooth^new).volume());root=float((tooth^finnew).volume());assert bite>.005 and root>.005;assert(finnew^new).volume()<1e-6 and finnew.min_gap(new,.5)>.235;fin=fin+finnew;teeth=teeth+tooth;num=len(d['segments'])+1;d['segments'].append({'number':num,'bounds_mm':list(finnew.bounding_box()),'height_mm':q['height_mm'],'blade_width_mm':q['fin_width_mm'],'blade_thickness_mm':q['fin_thickness_mm'],'teeth_count':1,'brace_count':0,'on_build_plate':True,'vertical_bed_path':True,'min_gap_mm':float(finnew.min_gap(new,.5)),'removal_vector':[0,0,-1],'through_permanent_support_access_window':True});d['teeth'].append({'fin_number':num,'bounds_mm':list(tooth.bounding_box()),'part_bite_mm3':bite,'fin_root_mm3':root,'neck_xy_mm':[1,1],'nominal_tip_penetration_mm':.35,'contact_point_mm':[*q['xy_mm'],q['roof_mm']]});rows.append({'kind':'support_access_window','local_bounds_mm':list(cut.bounding_box()),'removed_volume_mm3':float((s^cut).volume()),'native_issue':issue,'read_only_preinspection':q,'purpose':'A broad upright fin grows from the bed through a real clearance opening; no support rests on lower body material.'})
 teeth=union([q for q in material_components(teeth)if(q^new).volume()>.005 and(q^fin).volume()>.005]);fin=union([q for q in material_components(fin)if(q^teeth).volume()>.005]);n['source_f']=n.get('source_f',n['f']);n['v'],n['f']=vf(new);n['fin_v'],n['fin_f']=vf(fin);n['teeth_v'],n['teeth_f']=vf(teeth);n['removed_body_v'],n['removed_body_f']=vf(delta);bc=d.get('body_change',{});bc.update(kind='bounded_nonmating_support_access_windows',removed_volume_mm3=float(delta.volume()),added_volume_mm3=0.,source_body_volume_mm3=float(original.volume()),chamfers=bc.get('chamfers',[])+rows,combined_window_preinspection=study);d.update(source_mesh_preserved=False,body_change=bc,support_count=len(d['segments']),support_volume_mm3=float((fin+teeth).volume()),body_part_overlap_mm3=float((fin^new).volume()),teeth_part_overlap_mm3=float((teeth^new).volume()));np.savez_compressed(dst/'parts'/f'{pid}.npz',**n);(dst/'design'/f'{pid}.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');print('ACCESS106_CREATED',pid,float(delta.volume()),len(rows),flush=True);f=fit(pid,label);g=geom(pid,label)
 if f['fit_and_pose_geometry_passed']and g['geometric_constraints_passed']:
  run(pid,label);check(pid,label);q=refine(pid,label);print('ACCESS106_NATIVE',pid,q['external_island_count'],q['critical_external_count'],flush=True)
if __name__=='__main__':
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as pool:
  for f in concurrent.futures.as_completed([pool.submit(trial,s)for s in sys.argv[1:]]):
   try:f.result()
   except Exception:traceback.print_exc()
