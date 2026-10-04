import unittest,json,copy,tempfile,hashlib
from pathlib import Path
from assemble_calibration import assemble
from check_quotes import check
from test_calibration_export import calibration_data
from test_device import P
B=Path(__file__).resolve().parent.parent
class EvidenceWorkflow(unittest.TestCase):
 def test_missing_axis_or_synthetic_calibration_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);src=calibration_data();src['device_id']='42';f=root/'axis.json';f.write_text(json.dumps(src))
   with self.assertRaises(ValueError):assemble(P,'42',[f],{'device_id':'42'},root)
   src['source_kind']='MEASURED_FIXTURE';f.write_text(json.dumps(src))
   with self.assertRaises(ValueError):assemble(P,'42',[f],{'device_id':'42'},root)
 def test_incomplete_physical_tests_cannot_become_qualified(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);files=[]
   for i,key in enumerate(P['raw_order']):
    src=calibration_data();src.update(axis_id=key,device_id='42',source_kind='MEASURED_FIXTURE');f=root/f'{i}.json';f.write_text(json.dumps(src));files.append(f)
   out=assemble(P,'42',files,{'device_id':'42'},root);self.assertFalse(out['hardware_tests_complete']);self.assertFalse(any(out['physical_tests'].values()))
   manifest={'device_id':'42','tests':{P['required_physical_measurement_tests'][0]:{'status':'PASS','source_kind':'MEASURED_HARDWARE','evidence':[{'file':'proof.txt','sha256':'0'*64}]}}}
   (root/'proof.txt').write_text('test evidence only')
   with self.assertRaises(ValueError):assemble(P,'42',files,manifest,root)
 def test_empty_prices_are_not_zero_and_overrun_is_reported(self):
  d=json.loads((B/'manufacturing/quote_response_EMPTY.json').read_text())
  with self.assertRaises(ValueError):check(d)
  for row in d['items']+d['additional_mandatory_costs']:row.update(landed_total_cny=200,confirmed=True,quote_reference='UNIT_TEST_ONLY',includes_tax_moq_processing_freight=True)
  result=check(d);self.assertFalse(result['within_target']);self.assertFalse(result['hardware_qualified'])
if __name__=='__main__':unittest.main()
