"""Prepare a measurement-only bench handoff; catalog values never count as data."""
from pathlib import Path
import hashlib,json,math
R=Path(__file__).resolve().parents[1];H=R/'Hardware/PoseDoll44';V=H/'verification/revO7/runs/o7_20260924_r1';OUT=H/'bench/revO7'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 path=V/'loads.json';loads=json.loads(path.read_text());rows=[]
 for fam,ro,ri,force in [('LP6',14,6,354),('M4',7.4,2.6,210)]:
  axes=[r for c in loads['characters'] for r in c['axes'] if r['family']==fam];worst=max(axes,key=lambda r:r['required_hold_Nm']);G=worst['gravity_Nm'];hold=worst['required_hold_Nm'];rp=2*(ro**3-ri**3)/(3*(ro**2-ri**2))/1000;rw=(ro+ri)/2000
  # A 20 N / 60 mm screen is a proposed bench discriminator, not a user-approved
  # final comfort standard; expose it instead of silently turning it into a requirement.
  ceiling=20*.06-G
  rows.append({'family':fam,'ri_mm':ri,'ro_mm':ro,'catalog_nominal_force_N':force,'worst_axis':worst['axis'],'hold_screen_Nm':hold,'gravity_Nm':G,'friction_ceiling_from_provisional_20N_at_60mm_Nm':ceiling,'provisional_user_comfort_screen':True,'required_mu_at_catalog_force_uniform_pressure':hold/(2*force*rp),'required_mu_at_catalog_force_uniform_wear':hold/(2*force*rw),'nominal_contact_pressure_MPa':force/(math.pi*(ro*ro-ri*ri)),'effective_radius_uniform_pressure_m':rp,'effective_radius_uniform_wear_m':rw,'conditional_windows':[{'mu_min':lo,'mu_max':hi,'preload_min_for_hold_N':hold/(2*lo*rw),'preload_max_for_raising_force_N':ceiling/(2*hi*rp),'nonempty':hold/(2*lo*rw)<=ceiling/(2*hi*rp)} for lo,hi in [(.08,.22),(.12,.22),(.16,.22)]]})
 plan={'schema':'o7-material-bench-plan-v1','families':rows,'minimum_repeats_each_direction':3,'directions':['cw','ccw'],'hold_seconds':60,'provisional_drift_screen_deg':.3,'proof_scope':'Material/spring screening only. Not complete-joint force balance, production fit, body motion, UE accuracy or lifetime approval.','loads_sha256':sha(path),'source_sha256':sha(Path(__file__)),'physical_data_available':False,'manufacturing_released':False}
 save(OUT/'plan.json',plan)
 save(OUT/'measurement_template.json',{'schema':'o7-material-bench-data-v1','evidence_kind':'measurement','operator':'','measured_at':'','fixture_calibration_id':'','material_lot':'','mating_alloy_surface':'','plan_sha256':sha(OUT/'plan.json'),'samples':[],'sample_fields':{'sample_id':'unique instrument observation ID','family':'LP6 or M4','preload_setting_id':'shared ID at fixed measured setting','direction':'cw or ccw','repeat':'positive integer','preload_N':'measured total normal force, never catalog value','one_face_breakaway_torque_Nm':'measured nonnegative magnitude on ONE friction face','applied_one_face_hold_torque_Nm':'measured nonnegative magnitude on ONE friction face','hold_seconds':'measured seconds','angle_drift_deg':'measured signed change','temperature_C':'measured','raw_log_relative_path':'path under the data directory','raw_log_sha256':'SHA256 of instrument log'}})
 save(V/'hardware_boundary.json',{'status':'AWAITING_PHYSICAL_MATERIAL_AND_SPRING_DATA','digital_force_windows':rows,'reason':'Current geometry requires a nonempty hold/hand-force preload window. Catalog PEEK friction and nominal disc-spring force cannot establish the window or three-station balance. The narrow guide and rotor clearances also need loaded sliding tests.','do_not_order_whole_doll':True,'physical_tested':False,'manufacturing_released':False,'input_sha256':{path.relative_to(R).as_posix():sha(path),Path(__file__).relative_to(R).as_posix():sha(Path(__file__)),(OUT/'plan.json').relative_to(R).as_posix():sha(OUT/'plan.json')}})
 print([(x['family'],round(x['hold_screen_Nm'],3),round(x['required_mu_at_catalog_force_uniform_wear'],3),x['conditional_windows'][0]['nonempty']) for x in rows])
if __name__=='__main__':main()
