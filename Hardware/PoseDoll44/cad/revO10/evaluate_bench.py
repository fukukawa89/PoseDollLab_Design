"""Classify recorded single-site observations without inventing preload."""
import math,json,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def evaluate(o,plan):
 required=['sample_id','material_and_finish','compressed_spring_stack_height_mm','direction','hanging_mass_g','load_perpendicular_arm_mm','lever_mass_g','lever_perpendicular_com_arm_mm','hold_duration_s','angle_drift_deg','angle_uncertainty_deg','running_torque_Nm','breakaway_torque_Nm']
 missing=[k for k in required if o.get(k) is None or o.get(k)=='']
 if missing:return {'status':'INCOMPLETE','missing':missing,'hardware_result':False}
 for k in required[2:]:
  if k=='direction':continue
  if isinstance(o[k],bool) or not isinstance(o[k],(int,float)) or not math.isfinite(o[k]):return {'status':'INVALID','reason':k}
 if o['direction'] not in ('positive','negative'):return {'status':'INVALID','reason':'direction'}
 nonnegative=['hanging_mass_g','load_perpendicular_arm_mm','lever_mass_g','lever_perpendicular_com_arm_mm','hold_duration_s','angle_uncertainty_deg','running_torque_Nm','breakaway_torque_Nm']
 if any(o[k]<0 for k in nonnegative):return {'status':'INVALID','reason':'negative measurement'}
 if not .9<=o['compressed_spring_stack_height_mm']<=1.2:return {'status':'OUTSIDE_PLANNED_COMPRESSION','hardware_result':False}
 torque=9.80665e-6*(o['hanging_mass_g']*o['load_perpendicular_arm_mm']+o['lever_mass_g']*o['lever_perpendicular_com_arm_mm'])
 drift=abs(o['angle_drift_deg']);u=o['angle_uncertainty_deg'];limit=plan['provisional_drift_screen_deg']
 drift_state='PASS_SCREEN' if drift+u<=limit else 'FAIL_SCREEN' if drift-u>limit else 'INCONCLUSIVE_RESOLUTION'
 minload=plan['required_single_site_min_hold_Nm'];ceiling=plan['provisional_single_site_operating_ceiling_Nm']
 status='MATERIAL_STACK_SCREEN_CANDIDATE' if torque>=minload and drift_state=='PASS_SCREEN' and o['hold_duration_s']>=60 and max(o['running_torque_Nm'],o['breakaway_torque_Nm'])<=ceiling else 'REVIEW_OBSERVATION'
 return {'status':status,'applied_gravity_torque_Nm':torque,'drift_screen':drift_state,'measured_axial_force_N':o.get('measured_axial_force_N'),'preload_inferred_from_height_or_screw_torque':False,'full_joint_pass':False,'manufacturing_released':False,'scope':'One recorded direction/sample only. Require repeats, both directions, longer holds and the actual assembled two-site joint.'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('observation');a=p.parse_args();plan=json.loads((ROOT/'bench/revO10/plan.json').read_text());print(json.dumps(evaluate(json.loads(Path(a.observation).read_text()),plan),ensure_ascii=False,indent=2))
