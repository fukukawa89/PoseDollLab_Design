from pathlib import Path
import sys,json,numpy as np,math
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,box,union,vf
from o22_reference_mesh import reference_solid
from o22_material_components import material_components
from verify_revo22_f4_body_change import check as fit
from verify_revo22_f4_repaired_geometry import check as geom
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
from refine_revo22_f4_lateral104 import check as refine
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4';pid='X042';src=O/'candidates'/pid/'access106';dst=O/'candidates'/pid/'window_restore109'
for sub in ['parts','design','verification']:(dst/sub).mkdir(parents=True,exist_ok=True)
n=dict(np.load(src/'parts'/f'{pid}.npz'));d=json.loads((src/'design'/f'{pid}.json').read_text());original=reference_solid(n,d);cuts=[];rows=[q for q in d['body_change']['chamfers']if q.get('kind')=='support_access_window']
for row in rows:
 q=row['read_only_preinspection'];a=math.radians(q['angle_deg']);A=np.array([[math.cos(a),-math.sin(a),0],[math.sin(a),math.cos(a),0],[0,0,1.]]);w=q['fin_width_mm'];th=q['fin_thickness_mm'];cuts.append(box([-w/2-.32,-th/2-.32,-.01],[w/2+.32,th/2+.32,q['height_mm']+.32]).transform(np.c_[A,[*q['xy_mm'],0]]))
new=original-union(cuts);delta=original-new;fin=solid(n['fin_v'],n['fin_f']);teeth=solid(n['teeth_v'],n['teeth_f']);print('WINDOW109_RESTORE',float((new-solid(n['v'],n['f'])).volume()),'new_removed',float(delta.volume()),'fin_overlap',float((fin^new).volume()),flush=True);assert(fin^new).volume()<1e-6;assert len(material_components(new))==1;assert delta.volume()<47;teeth=union([q for q in material_components(teeth)if(q^new).volume()>.005 and(q^fin).volume()>.005]);n['v'],n['f']=vf(new);n['removed_body_v'],n['removed_body_f']=vf(delta);n['teeth_v'],n['teeth_f']=vf(teeth);d['body_change'].update(kind='support_access_windows_with_prior_contact_chamfers_restored',removed_volume_mm3=float(delta.volume()),added_volume_mm3=0.,chamfers=rows);np.savez_compressed(dst/'parts'/f'{pid}.npz',**n);(dst/'design'/f'{pid}.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');f=fit(pid,dst.name);g=geom(pid,dst.name)
if f['fit_and_pose_geometry_passed']and g['geometric_constraints_passed']:run(pid,dst.name);check(pid,dst.name);refine(pid,dst.name)
