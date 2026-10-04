import copy,json,unittest,math
from pathlib import Path
from calibrate_axis import fit_axis
from measurement import correct_sensor
from ue_export import export
from test_device import P
B=Path(__file__).resolve().parent.parent

def calibration_data(sign=1):
 rows=[]
 def sample(q,phase,direction):
  # Exact invertible error curve crossing encoder zero; fixed independent fixture.
  sensor=(350+sign*q/1.01)%360
  return {'fixture_joint_deg':q,'sensor_deg':sensor,'phase':phase,'direction':direction,'peak_to_peak_deg':.02,'sample_count':25}
 fits=list(range(0,61,10)) if sign==1 else list(range(-60,1,10))
 for q in fits:rows.append(sample(q,'fit','cw'))
 for q in ([5,15,45,55] if sign==1 else [-55,-45,-15,-5]):
  for direction in ['cw','ccw']:rows.append(sample(q,'validate',direction))
 return {'axis_id':'elbow_l.flex/r0','fixture_id':'SYNTHETIC_REFERENCE','source_kind':'SYNTHETIC','sign':sign,'reference_uncertainty_deg':.05,'samples':rows}

class CalibrationExport(unittest.TestCase):
 def test_bounded_fit_and_independent_validation_both_directions(self):
  for sign in [-1,1]:
   axis,report=fit_axis(calibration_data(sign));self.assertLess(report['max_independent_error_deg'],1e-10);self.assertFalse(report['whole_device_physical_qualification_granted'])
   self.assertAlmostEqual(axis['diagnostic_error_bound_deg'],.05)
 def test_fit_rejects_false_precision_incomplete_and_unstable_fixture(self):
  for mutate in [lambda d:d.update(reference_uncertainty_deg=.2),lambda d:d['samples'].pop(),lambda d:d['samples'][0].update(peak_to_peak_deg=.31),lambda d:d['samples'][0].update(sample_count=2)]:
   d=calibration_data();mutate(d)
   with self.assertRaises(ValueError):fit_axis(d)
 def test_validation_is_not_fit_resubstitution(self):
  d=calibration_data();d['samples'][-1]['fixture_joint_deg']=60
  with self.assertRaises(ValueError):fit_axis(d)
 def test_export_default_refuses_synthetic_and_preserves_rotations(self):
  r=json.loads((B/'ue/a_stand.record.json').read_text())
  with self.assertRaises(ValueError):export(P,r)
  self.assertEqual(export(P,r,True)['raw_count'],46)
 def test_packet_tamper_scan_tamper_angle_tamper_rejected(self):
  original=json.loads((B/'ue/a_stand.record.json').read_text())
  for mode in ['packet','scan','angle','calibration']:
   r=copy.deepcopy(original)
   if mode=='packet':r['packets_hex'][0]=r['packets_hex'][0][:200]+'ff'+r['packets_hex'][0][202:]
   elif mode=='scan':r['measurement']['raw_scans'][0]['channels']['waist/r0']['sensor_deg']+=.1
   elif mode=='angle':r['measurement']['joint_angles_deg']['waist/r0']+=1
   else:r['measurement']['calibration']['axes']['waist/r0']['sensor_zero_deg']+=1
   with self.subTest(mode=mode):
    with self.assertRaises(ValueError):export(P,r,True)
if __name__=='__main__':unittest.main()
