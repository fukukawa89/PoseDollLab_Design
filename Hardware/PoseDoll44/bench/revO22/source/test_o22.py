"""Regression reproductions from the independent O21 review."""
import copy,json,unittest,math
from pathlib import Path
import numpy as np
from test_device import fixture,P
from device import capture_window,forward,digest
from measurement import correct_sensor,capture_window as calibrated_capture
B=Path(__file__).resolve().parent.parent
class O22(unittest.TestCase):
 def capture(self,c,s,t=1510):
  return capture_window(P,c,s,expected_capture_id=17,evaluation_time_ms=t)
 def test_one_and_multiple_counts_at_each_limit_preserved(self):
  for k in P['raw_order']:
   for limit in P['raw_limits_deg'][k]:
    for counts in (-8,-1,0,1,8):
     with self.subTest(axis=k,limit=limit,counts=counts):
      c,s=fixture();c['axes'][k]['reference_joint_deg']=limit
      for row in s:row['channels'][k]['sensor_deg']=180+counts*360/16384
      out=self.capture(c,s)
      self.assertEqual(out['status'],'VALID_MEASUREMENT',out)
      self.assertAlmostEqual(out['joint_angles_deg'][k],limit+counts*360/16384)
      self.assertIn(k,out['boundary_uncertainty'])
      self.assertEqual(out['raw_scans'],s)
 def test_real_overrun_and_uncertainty_cap_rejected(self):
  for k in P['raw_order']:
   for limit,direction in zip(P['raw_limits_deg'][k],(-1,1)):
    c,s=fixture();c['axes'][k]['reference_joint_deg']=limit
    for row in s:row['channels'][k]['sensor_deg']=180+direction*1.1
    self.assertEqual(self.capture(c,s)['status'],'REJECTED')
  for bound in (-1,1.251,float('nan'),True):
   c,s=fixture();c['axes'][P['raw_order'][0]]['diagnostic_error_bound_deg']=bound
   self.assertEqual(self.capture(c,s)['status'],'REJECTED')
 def test_ambiguous_turn_not_accepted_by_tolerance(self):
  p=copy.deepcopy(P);k=p['raw_order'][0];p['raw_limits_deg'][k]=[-180,180]
  c,s=fixture();c['profile_sha256']=digest(p);c['axes'][k]['reference_joint_deg']=180
  self.assertEqual(capture_window(p,c,s,expected_capture_id=17,evaluation_time_ms=1510)['status'],'REJECTED')
 def test_final_age_is_total_not_two_independent_intervals(self):
  c,s=fixture()
  for row in s:
   for sample in row['channels'].values():sample['time_ms']=row['time_ms']-50
  # 50 ms scan + 110 ms evaluation delay used to pass separately.
  self.assertEqual(self.capture(c,s,1610)['reason'],'stale final oldest sample')
  self.assertEqual(self.capture(c,s,1570)['final_oldest_sample_age_ms'],120)
  self.assertEqual(self.capture(c,s,1570.001)['status'],'REJECTED')
  # The 500ms historical window remains legal; only the final round is age-gated.
  self.assertEqual(self.capture(c,s,1550)['status'],'VALID_MEASUREMENT')
 def test_most_recent_scan_uses_earliest_channel(self):
  c,s=fixture();s[-1]['channels'][P['raw_order'][0]]['time_ms']=1450.
  self.assertEqual(self.capture(c,s,1571)['status'],'REJECTED')
 def test_measured_calibration_cannot_borrow_synthetic_bound(self):
  c,s=fixture();c['status']='MEASURED'
  self.assertEqual(self.capture(c,s)['status'],'REJECTED')
  for a in c['axes'].values():a['diagnostic_error_bound_deg']=.4
  out=self.capture(c,s);self.assertEqual(out['status'],'VALID_MEASUREMENT')
  self.assertFalse(out['hardware_capture_eligible'])
 def test_a_pose_margin_and_unchanged_reference(self):
  a=json.loads((B/'profiles/default_pose.json').read_text())
  self.assertGreaterEqual(min(a['margin_to_mechanical_limits_deg'].values()),3-1e-9)
  old=json.loads((B/'profiles/mechanical_reference_O20.json').read_text())
  self.assertEqual(P['neutral_raw_deg'],old['neutral_raw_deg'])
  f=forward(P,a['raw_deg'])
  for side,sign in [('l',1),('r',-1)]:
   v=f['elbow_'+side][:3,3]-f['upperarm_'+side][:3,3]
   self.assertAlmostEqual(math.degrees(math.atan2(sign*v[1],-v[2])),35,places=7)
   self.assertLess(abs(v[0]),1e-7)
 def test_bounded_lut_wrap_no_extrapolation_and_zero_corrected(self):
  lut={'kind':'bounded_delta_deg','source':'SYNTHETIC','anchor_sensor_deg':350,
       'knots':[[i,float(i)/100] for i in range(0,61,10)]}
  self.assertAlmostEqual(correct_sensor(10,lut),10.2)
  self.assertAlmostEqual(correct_sensor(50,lut),50.6)
  for outside in [349.999,50.001,180]:
   with self.assertRaises(ValueError):correct_sensor(outside,lut)
  for bad in [dict(lut,knots=lut['knots'][:3]),dict(lut,knots=[[i,-2*i] for i in range(0,61,10)])]:
   with self.assertRaises(ValueError):correct_sensor(10,bad)
  c,s=fixture();k=P['raw_order'][0]
  c['axes'][k].update(sensor_zero_deg=10,linearization=lut)
  for row in s:row['channels'][k]['sensor_deg']=10
  out=calibrated_capture(P,c,s,expected_capture_id=17,evaluation_time_ms=1510)
  self.assertEqual(out['status'],'VALID_MEASUREMENT')
  self.assertAlmostEqual(out['joint_angles_deg'][k],P['neutral_raw_deg'][k])
  self.assertEqual(out['raw_scans'],s)
if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(O22))
 (B/'verification/review_regressions.json').write_text(json.dumps({'status':'PASS' if r.wasSuccessful() else 'FAIL','tests':r.testsRun,'boundary_count_cases':46*2*5,'physical_tests':False},indent=2)+'\n')
 raise SystemExit(0 if r.wasSuccessful() else 1)
