"""Independent all-printed fixture and lever with the same stock stack as O11."""
from build_printed_core import *

def main():
 out=H/'bench/revO11';out.mkdir(parents=True,exist_ok=True)
 base=box([-25,-15,0],[25,15,8])-pocket(8)
 for x in (-20,20):base-=cylinder(2.25,-.1,8.1).translate([x,-9,0])
 parts={}
 for n,x in enumerate((-10,10),1):
  M=rot(0,-90);p=[x,0,4]
  base-=pose(cylinder(1.7,-21,19),M,p)
  bolt=cylinder(1.5,-20,15)+cylinder(2.75,15,18)-hex_prism(2.5,16.5,18.1)
  nut=hex_prism(5.5,-17.4,-15)-cylinder(1.55,-17.5,-14.9)
  parts[f'case_M3x35_{n}']=pose(bolt,M,p);parts[f'case_M3_nut_{n}']=pose(nut,M,p)
 parts['printed_base_minus']=base^box([-30,-20,-1],[30,0,9]);parts['printed_base_plus']=base^box([-30,0,-1],[30,20,9])
 lever=cylinder(6,9,12)+box([4,-5,9],[105,5,15])
 lever-=cylinder(6,12,15.1);lever-=cylinder(2.125,8.9,15.1);lever-=cylinder(1.5,8.9,15.1).translate([100,0,0])
 parts['printed_lever']=lever;parts.update(stock_stack(8))
 hits=[]
 for a,b in itertools.combinations(parts,2):
  v=(parts[a]^parts[b]).volume()
  if v>1e-4:hits.append({'pair':[a,b],'volume_mm3':v})
 assert not hits,hits
 np.savez_compressed(out/'parts.npz',**{k:tri(s) for k,s in parts.items()})
 for k,s in parts.items():
  if k.startswith('printed_'):export_stl(out/(k+'.stl'),tri(s))
 loads=OUT/'loads.json'
 rows=[r for c in json.loads(loads.read_text())['characters'] for n,r in c['physical_axes'].items() if n in ('alpha','beta')]
 target=max(r['required_hold_Nm'] for r in rows)/2
 plan={'schema':'o11-printed-stack-v1','parts':{k:record(s) for k,s in parts.items()},'nominal_volume_findings':hits,'generator_sha256':sha(__file__),'stack_generator_sha256':sha(Path(__file__).with_name('build_printed_core.py')),
 'stock_stack_matches_core':True,'printed_base_thickness_mm':8,'reaction_web_mm':3.8,'lever_nominal_arm_mm':100,'custom_metal_parts':0,
 'single_site_screening_target_Nm':target,'target_source_sha256':sha(loads),'target_note':'O11 solid-volume load budget is a screening reference, not full-body qualification; both friction sites must later be tested together.',
 'spring_stack_trials_mm':[1.1,1.0,.9],'spring_point_N':210,'force_is_catalogue_reference_not_measured':True,'drift_screen_deg':.3,'hold_seconds':[60,600,3600],
 'extra_long_hold_seconds':86400,'positive_and_negative_load':True,'physical_tested':False,'manufacturing_released':False,
 'purpose':['Hold and reposition effort','Printed-body deformation and clamp relaxation','Wear and fastener loosening','Separate fixture deflection from lever slip'],
 'assembly':'Open base on Y=0, place M3 nut and its standard washer into their seats, close with two M3x35 screws. Then add the wide washer, lever, wide washer, opposed disc pair, normal M4 washer and catalogue shoulder bolt. Clamp both base halves to a rigid support through outer mounting holes; axis horizontal.'}
 (out/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 template={'schema':'o11-printed-stack-observation-v1','sample_id':None,'printer_nozzle_layer_orientation':None,'filament_and_drying':None,'actual_part_dimensions_mm':None,'washer_material_and_finish':None,'spring_stack_height_mm':None,'measured_axial_force_N':None,'load_direction':None,'load_torque_Nm':None,'hold_seconds':None,'base_angle_change_deg':None,'lever_angle_change_deg':None,'measurement_uncertainty_deg':None,'breakaway_torque_Nm':None,'running_torque_Nm':None,'screw_witness_mark_change':None,'notes':None}
 (out/'measurement_template.json').write_text(json.dumps(template,indent=2)+'\n');print('bench',len(parts),'parts, no nominal overlap, target',target)
if __name__=='__main__':main()


