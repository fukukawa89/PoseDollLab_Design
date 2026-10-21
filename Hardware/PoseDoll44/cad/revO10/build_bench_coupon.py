"""Isolated face-friction experiment, independent of full shoulder collisions.
Printable lever and flat drilled aluminium base; purchased fasteners are only
nominal envelopes. This tests a material/spring stack, not a full joint.
"""
from solid_ops import *
from build_face_brake import disc_spring
import itertools

def main():
 out=H/'bench/revO10';out.mkdir(parents=True,exist_ok=True);parts={}
 base=box([-15,-15,0],[15,15,8])-cylinder(2.2,-.1,8.1)
 for x in (-10,10):base-=cylinder(2.2,-.1,8.1).translate([x,-10,0])
 lever=cylinder(6,8.5,11.5)+box([4,-5,8.5],[105,5,14.5])
 lever-=cylinder(6,11.5,14.6);lever-=cylinder(2.15,8.4,14.6);lever-=cylinder(1.5,8.4,14.6).translate([100,0,0])
 parts.update(aluminium_base=base,PA12_lever=lever)
 for name,z in [('inner_plate',8),('outer_plate',11.5)]:parts[name]=cylinder(6,z,z+.5)-cylinder(2.12,z-.1,z+.6)
 parts['spring_1']=disc_spring(12);parts['spring_2']=disc_spring(12.45,flip=True)
 parts['front_load_washer']=cylinder(4.5,12.9,13.2)-cylinder(2.15,12.8,13.3)
 parts['rear_load_washer']=cylinder(4.5,-.8,0)-cylinder(2.15,-.9,.1)
 t=np.arange(6)*np.pi/3;parts['M4_nut_envelope']=md.CrossSection([np.c_[np.cos(t),np.sin(t)]*7/np.sqrt(3)]).extrude(3.2).translate([0,0,-4])-cylinder(2.02,-4.1,-.7)
 screw=cylinder(2,-6.8,13.2)+cylinder(3.5,13.2,17.2)
 hexagon=md.CrossSection([np.c_[np.cos(t),np.sin(t)]*3/np.sqrt(3)]).extrude(2.1).translate([0,0,15.2]);parts['M4x20_screw_envelope']=screw-hexagon
 assert all(s.volume()>0 and s.num_tri()>0 for s in parts.values())
 np.savez_compressed(out/'parts.npz',**{k:tri(v) for k,v in parts.items()})
 for k in ('aluminium_base','PA12_lever'):export_stl(out/(k+'.stl'),tri(parts[k]))
 check=[]
 for a,b in itertools.combinations(parts,2):
  v=(parts[a]^parts[b]).volume()
  if v>1e-5:check.append({'pair':[a,b],'volume_mm3':v})
 assert not check,check
 loads=json.loads((OUT/'face_axis_loads.json').read_text());rows=[r for c in loads['characters'] for n,r in c['physical_axes'].items() if n in ('alpha','beta')];maxhold=max(r['required_hold_Nm'] for r in rows);maxgravity=max(r['gravity_Nm'] for r in rows)
 report={'scope':'Isolated stack screening, not joint release. Actual M4 catalogue thread engagement and coupon process drawing must be confirmed before fabrication. No current hardware.','parts':{k:record(v) for k,v in parts.items()},'generator_sha256':sha(__file__),'source_load_sha256':sha(OUT/'face_axis_loads.json'),'nominal_stack_volume_findings':check,'force_not_measured':True,'mounting':'Bolt the two base holes to a fixed backing so the central axis is horizontal. The lever moves in a vertical plane; grip the base, not the moving lever.','lever_finished_bore_mm':4.3,'lever_bore_note':'Finish the printed central hole to 4.3 mm if needed; this is assembly preparation, not the purpose of the experiment. The coupon annulus inner radius 2.15 mm differs from the planned 2.12 mm contact radius; no exact coefficient transfer is claimed.','spring_compressed_total_height_mm_trials':[1.10,1.00,.90],'spring_catalogue_point_N':210,'catalogue_second_grade_conditional_force_range_at_test_height_N':[189,273],'catalogue_point_is_not_measured_preload':True,'required_single_site_min_hold_Nm':maxhold/2,'provisional_single_site_operating_ceiling_Nm':(20*.06-maxgravity)/2,'provisional_drift_screen_deg':.3,'hold_durations_s':[60,600,3600],'example_hanging_mass_at_100mm_excluding_lever_weight_g':maxhold/2/(9.80665*.1)*1000,'limitations':['Two actual sites may not share load equally; coupon does not qualify the full joint','Through-bolt rear nut differs from custom M3 axle; it does not validate axle loosening','Record lever self-weight and its measured gravity lever arm','Use measured perpendicular moment arms, not nominal CAD length','If angular measurement uncertainty exceeds 0.3 degrees, drift classification is inconclusive','Do not infer 210 N from screw tightening torque or assume spring height is measured force'],'material_candidates':{'base':'6061 aluminium, flat load face, actual finish recorded','lever':'same PA12 process and orientation proposed for the forks','plates':'steel annuli OD12 ID4.24 thickness0.5; actual material/finish must match prototype','springs':'Raleigh A8 x 4.2 x 0.4, two opposite-facing discs in series'},'hardware_tested':False,'full_joint_manufacturing_released':False,'primary_spring_source':'https://www.raleigh-spring.cn/discspring/list_84_2/'}
 (out/'plan.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');save('bench_plan.json',report);print('isolated coupon nominal assembled pairs clear; single-site target',maxhold/2)
 template={'schema':'o10-face-stack-observation-v1','sample_id':None,'material_and_finish':None,'compressed_spring_stack_height_mm':None,'measured_axial_force_N':None,'direction':None,'hanging_mass_g':None,'load_perpendicular_arm_mm':None,'lever_mass_g':None,'lever_perpendicular_com_arm_mm':None,'hold_duration_s':None,'angle_drift_deg':None,'angle_uncertainty_deg':None,'running_torque_Nm':None,'breakaway_torque_Nm':None,'notes':None}
 (out/'measurement_template.json').write_text(json.dumps(template,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()

