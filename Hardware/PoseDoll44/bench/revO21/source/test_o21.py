"""O21 host, unchanged FK, channel binding and cost arithmetic checks."""
from pathlib import Path
import unittest,json,copy,math,struct,zlib
import numpy as np
from mt6701 import crc6,decode_word
from usb_capture import decode,measurement_scans,SIZE,MASK,SCAN
from measurement import correct_sensor,capture_window
from device import forward,digest
B=Path(__file__).resolve().parent.parent
P=json.loads((B/'profiles/device_profile.json').read_text(encoding='utf-8-sig'))
W=json.loads((B/'profiles/wiring.json').read_text(encoding='utf-8-sig'))
class O21(unittest.TestCase):
 def test_binding_46_no_duplicates(self):
  n=[n for g in W['banks'] for n in g['nodes']]
  self.assertEqual(sorted(x['raw_index'] for x in n),list(range(46)))
  for x in n:self.assertEqual(x['raw_id'],P['raw_order'][x['raw_index']])
  self.assertEqual([g['count'] for g in W['banks']],[14,16,16])
 def test_unchanged_geometric_mapping(self):
  old=json.loads((B/'profiles/mechanical_reference_O20.json').read_text(encoding='utf-8-sig'))
  rng=np.random.default_rng(21)
  for _ in range(25):
   q={k:float(rng.uniform(*P['raw_limits_deg'][k])) for k in P['raw_order']}
   a,b=forward(P,q),forward(old,q)
   for name in a:np.testing.assert_array_equal(a[name],b[name])
 def test_c_fixture_and_all_packet_bits(self):
  raw=(B/'source/codec_fixture.bin').read_bytes();f=decode(raw)
  self.assertEqual(f['valid_mask'],MASK)
  for i,w in enumerate(f['words']):self.assertEqual(w>>10,i*307)
  self.assertEqual(len(raw),SIZE)
  for i in range(SIZE*8):
   bad=bytearray(raw);bad[i//8]^=1<<(i%8)
   with self.assertRaises(ValueError):decode(bytes(bad))
  for n in range(SIZE):
   with self.assertRaises(ValueError):decode(raw[:n])
  bad=bytearray(raw);bad[236]^=1;struct.pack_into('<I',bad,244,zlib.crc32(bad[:244]))
  with self.assertRaises(ValueError):decode(bytes(bad))
 def test_valid_zero_not_confused_with_stuck_low(self):
  self.assertTrue(decode_word(0,True)['valid']);self.assertFalse(decode_word(0,False)['valid'])
  self.assertFalse(decode_word(0xffffff,True)['valid'])
  self.assertFalse(decode_word((10<<10)|(1<<6)|crc6((10<<4)|1),True)['valid'])
 def test_replay_boot_and_all46_faults(self):
  f=decode((B/'source/codec_fixture.bin').read_bytes());cap=f['capture']
  rows=measurement_scans(P,[f],cap);self.assertEqual(len(rows[0]['channels']),46)
  for i in range(46):
   bad=copy.deepcopy(f);bad['valid_mask']^=1<<i
   with self.assertRaises(ValueError):measurement_scans(P,[bad],cap)
  with self.assertRaises(ValueError):measurement_scans(P,[f,f],cap)
  bad=copy.deepcopy(f);bad.update(scan=2,token=2);bad['body_boot']+=1
  with self.assertRaises(ValueError):measurement_scans(P,[f,bad],cap)
 def test_lut_circle_and_reject_fold_nan(self):
  lut={'kind':'periodic_delta_deg','source':'SYNTHETIC','knots':[[x,math.sin(math.radians(x))] for x in range(0,360,30)]}
  self.assertAlmostEqual(correct_sensor(90,lut),91)
  self.assertAlmostEqual(correct_sensor(270,lut),269)
  self.assertAlmostEqual(correct_sensor(359.9,lut),359.9-.1/60)
  for bad in [dict(lut,knots=[[0,0],[90,1]]),dict(lut,knots=[[x,float('nan')] for x in range(0,360,30)]),dict(lut,knots=[[x,-2*x] for x in range(0,360,30)])]:
   with self.assertRaises(ValueError):correct_sensor(90,bad)
 def test_capture_does_not_qualify_unmeasured_hardware(self):
  cal={'status':'SYNTHETIC','device_id':'test','profile_sha256':digest(P),'axes':{k:{'sensor_zero_deg':180.,'reference_joint_deg':P['neutral_raw_deg'][k],'sign':1} for k in P['raw_order']}}
  scans=[{'device_id':'test','boot_id':'boot','capture_id':21,'sequence':i+1,'time_ms':1000+i*100.,'integrity':'valid','channels':{k:{'sensor_deg':180.,'time_ms':990+i*100.,'status':'valid'} for k in P['raw_order']}} for i in range(6)]
  raw=copy.deepcopy(scans);out=capture_window(P,cal,scans,expected_capture_id=21,evaluation_time_ms=1510)
  self.assertEqual(out['status'],'VALID_MEASUREMENT');self.assertFalse(out['hardware_capture_eligible'])
  self.assertEqual(out['raw_scans'],raw);self.assertEqual(scans,raw)
  self.assertEqual(out['joint_angles_deg'],P['neutral_raw_deg']);self.assertEqual(out['calibration_sha256'],digest(cal))
  cal['status']='MEASURED';cal['physical_tests']={k:True for k in P['required_physical_measurement_tests']}
  cal['physical_tests']['mt6701_accuracy_full_range']=False
  self.assertFalse(capture_window(P,cal,scans,expected_capture_id=21,evaluation_time_ms=1510)['hardware_capture_eligible'])
 def test_budget_allocation_is_not_a_quote(self):
  b=json.loads((B/'budget.json').read_text(encoding='utf-8-sig'))
  self.assertEqual(b['target_total_cny'],round(sum(r['target_total_cny'] for r in b['rows']),2))
  self.assertEqual(b['target_total_cny'],1482.5);self.assertEqual(b['confirmed_supplier_quote_count'],0)
  self.assertEqual(b['sensor_reference']['quantity'],50);self.assertEqual(b['sensor_reference']['tier_min'],30)
  self.assertAlmostEqual(b['sensor_reference']['usd_each']*50,51.775)
if __name__=='__main__':
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(O21);r=unittest.TextTestRunner(verbosity=2).run(suite)
 (B/'verification').mkdir(exist_ok=True)
 (B/'verification/host_tests.json').write_text(json.dumps({'status':'PASS' if r.wasSuccessful() else 'FAIL','tests':r.testsRun,'hardware_tested':False},indent=2)+'\n')
 raise SystemExit(0 if r.wasSuccessful() else 1)
