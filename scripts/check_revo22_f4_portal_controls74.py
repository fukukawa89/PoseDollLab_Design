from pathlib import Path
import sys,json,numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import box,union
from verify_revo22_f4_portal_layers import check
from o22_reference_mesh import reference_solid
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4';base=box([0,0,0],[4,3.2,6])+box([12,0,0],[16,3.2,6]);steps=[]
for i in range(20):
 e=(i+1)*.2;steps.extend([box([0,0,6+i*.2],[4+e,3.2,6+(i+1)*.2]),box([12-e,0,6+i*.2],[16,3.2,6+(i+1)*.2])])
positive=base+union(steps);sudden=base+box([0,0,6],[16,3.2,6.2]);floating=positive+box([20,0,8],[22,3.2,9]);design={'segments':[{'bed_connected_portal':True,'blade_thickness_mm':3.2,'minimum_base_leg_width_mm':4.,'height_mm':10.,'brace_count':0}]};a=check(positive,design);b=check(sudden,design);c=check(floating,design);assert a['passed'] and not b['passed'] and not c['passed'];(O/'portal_layer_controls.json').write_text(json.dumps({'analytical_45_degree_portal':a,'unbacked_horizontal_roof_negative':b,'floating_fin_negative':c,'all_controls_passed':True},indent=2))
p=O/'candidates/P017/exact64';n=dict(np.load(p/'parts/P017.npz'));d=json.loads((p/'design/P017.json').read_text());reference_solid(n,d);bad=dict(n);bad['registered_reference_print_v']=n['registered_reference_print_v'].copy();bad['registered_reference_print_v'][0,0]+=.001;rejected=False
try:reference_solid(bad,d)
except AssertionError:rejected=True
assert rejected;(O/'reference_registration_controls.json').write_text(json.dumps({'valid_registered_reference_accepted':True,'changed_vertex_without_matching_certificate_rejected':rejected},indent=2));print('PORTAL_AND_REFERENCE_CONTROLS_PASS',flush=True)
