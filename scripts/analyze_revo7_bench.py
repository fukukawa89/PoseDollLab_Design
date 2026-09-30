"""Fail-closed import of single-face material coupon observations; never releases a joint."""
from pathlib import Path
import argparse,hashlib,json,math

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def analyze(plan,data,root,plan_digest):
 result={'status':'AWAITING_HARDWARE','issues':[],'settings':[],'measured_claim_independently_verified':False,'full_joint_qualified':False,'manufacturing_released':False}
 if not data.get('samples'):return result
 try:
  assert data.get('schema')=='o7-material-bench-data-v1','wrong schema'
  assert data.get('evidence_kind')=='measurement','synthetic/catalog data is not a measurement'
  assert data.get('plan_sha256')==plan_digest,'plan hash mismatch'
  for key in ['operator','measured_at','fixture_calibration_id','material_lot','mating_alloy_surface']:assert isinstance(data.get(key),str) and data[key].strip(), 'missing '+key
  families={x['family']:x for x in plan['families']};groups={};seen=set()
  for sample in data['samples']:
   assert isinstance(sample.get('sample_id'),str) and sample['sample_id'] not in seen,'missing or duplicate sample ID';seen.add(sample['sample_id'])
   fam=sample['family'];assert fam in families,'unknown coupon family'
   assert sample['direction'] in ('cw','ccw'),'bad direction'
   assert isinstance(sample['preload_setting_id'],str) and sample['preload_setting_id'],'missing preload setting ID'
   for key in ['preload_N','one_face_breakaway_torque_Nm','applied_one_face_hold_torque_Nm','hold_seconds','angle_drift_deg','temperature_C']:
    v=sample[key];assert isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v),'invalid numeric '+key
   assert sample['preload_N']>0 and sample['one_face_breakaway_torque_Nm']>=0 and sample['applied_one_face_hold_torque_Nm']>=0 and sample['hold_seconds']>=0,'invalid physical magnitude'
   rel=Path(sample['raw_log_relative_path']);assert not rel.is_absolute(),'raw log must be relative'
   p=(root/rel).resolve();assert p.is_relative_to(root.resolve()) and p.is_file(),'raw log missing or outside evidence directory'
   assert sha(p)==sample['raw_log_sha256'],'raw log hash mismatch'
   groups.setdefault((fam,sample['preload_setting_id']),[]).append(sample)
  for (fam,setting),rows in groups.items():
   ref=families[fam];count={d:sum(r['direction']==d for r in rows) for d in ('cw','ccw')};complete=min(count.values())>=plan['minimum_repeats_each_direction'];forces=[r['preload_N'] for r in rows]
   force_band=(max(forces)-min(forces))/(sum(forces)/len(forces));complete &= force_band<=.05
   hold_ok=all(r['applied_one_face_hold_torque_Nm']*2>=ref['hold_screen_Nm'] and r['hold_seconds']>=plan['hold_seconds'] and abs(r['angle_drift_deg'])<=plan['provisional_drift_screen_deg'] for r in rows)
   lower=2*min(r['one_face_breakaway_torque_Nm'] for r in rows);upper=2*max(r['one_face_breakaway_torque_Nm'] for r in rows)
   ok=complete and hold_ok and lower>=ref['hold_screen_Nm'] and upper<=ref['friction_ceiling_from_provisional_20N_at_60mm_Nm']
   result['settings'].append({'family':fam,'setting':setting,'count_each_direction':count,'preload_relative_spread':force_band,'complete':complete,'inferred_two_equal_faces_breakaway_range_Nm':[lower,upper],'inferred_raising_force_range_at_60mm_N':[(t+ref['gravity_Nm'])/.06 for t in (lower,upper)],'candidate_for_later_joint_test':ok,'status':'COUPON_SCREEN_ONLY' if ok else ('INCOMPLETE' if not complete else 'DOES_NOT_MEET_PROVISIONAL_SCREEN')})
  result['status']='COUPON_CANDIDATES_RECORDED' if all(any(x['family']==f and x['candidate_for_later_joint_test'] for x in result['settings']) for f in families) else 'MORE_MEASUREMENTS_OR_DIFFERENT_SETTING_REQUIRED'
  result['scope']='Two-face inference assumes equivalent interfaces. No claim about joint force distribution, guide stiction, drift, backlash, precision or lifetime.'
 except (AssertionError,KeyError,TypeError,ValueError,OSError) as e:result['status']='INVALID_EVIDENCE';result['issues'].append(str(e))
 return result

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--plan',type=Path,required=True);ap.add_argument('--data',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 plan=json.loads(a.plan.read_text(encoding='utf-8-sig'));data=json.loads(a.data.read_text(encoding='utf-8-sig'));result=analyze(plan,data,a.data.parent,sha(a.plan));result['input_sha256']={str(a.plan.resolve()):sha(a.plan),str(a.data.resolve()):sha(a.data),str(Path(__file__).resolve()):sha(Path(__file__))};a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result['status'])
if __name__=='__main__':main()
