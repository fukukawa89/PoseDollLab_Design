"""Read actual measured evidence to assemble a calibration; never grants missing tests."""
import argparse,json,hashlib
from pathlib import Path
from device import digest
from calibrate_axis import fit_axis

def assemble(profile,device_id,axis_files,test_manifest,root):
 if not device_id or not device_id.isdecimal() or int(device_id)<=0:raise ValueError('real USB device_id required')
 axes={};reports={}
 for filename in axis_files:
  data=json.loads(Path(filename).read_text(encoding='utf-8-sig'));source=data.get('original_samples',data)
  if source.get('source_kind')!='MEASURED_FIXTURE':raise ValueError('synthetic calibration cannot qualify hardware')
  if source.get('device_id')!=device_id:raise ValueError('fixture belongs to another device')
  axis,report=fit_axis(source);key=report['axis_id']
  if key not in profile['raw_order'] or key in axes:raise ValueError('duplicate or unknown axis')
  axes[key]=axis;reports[key]=report
 if set(axes)!=set(profile['raw_order']):raise ValueError('all 46 measured axis calibrations required')
 if test_manifest.get('device_id')!=device_id:raise ValueError('test device mismatch')
 checks={};evidence={};root=Path(root).resolve()
 for key in profile['required_physical_measurement_tests']:
  row=test_manifest.get('tests',{}).get(key,{})
  checks[key]=False
  if row.get('status')!='PASS' or row.get('source_kind')!='MEASURED_HARDWARE':continue
  files=row.get('evidence',[])
  if not files:raise ValueError('PASS without evidence: '+key)
  hashes={}
  for item in files:
   path=(root/item['file']).resolve()
   if not path.is_relative_to(root):raise ValueError('evidence outside selected directory')
   h=hashlib.sha256(path.read_bytes()).hexdigest()
   if h!=item.get('sha256'):raise ValueError('evidence digest mismatch: '+key)
   hashes[item['file']]=h
  checks[key]=True;evidence[key]=hashes
 return {'schema':'POSEDOLL-O22-CALIBRATION/1','status':'MEASURED','device_id':device_id,'profile_sha256':digest(profile),'axes':axes,'axis_reports':reports,'physical_tests':checks,'physical_evidence':evidence,'hardware_tests_complete':all(checks.values()),'notice':'Evidence integrity check; operator remains responsible for authentic measurement and stated uncertainty. No factory calibration assumed.'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--profile',required=True);p.add_argument('--device-id',required=True);p.add_argument('--axis-dir',required=True);p.add_argument('--tests',required=True);p.add_argument('--output',required=True);a=p.parse_args();read=lambda f:json.loads(Path(f).read_text(encoding='utf-8-sig'))
 result=assemble(read(a.profile),a.device_id,sorted(Path(a.axis_dir).glob('*.json')),read(a.tests),Path(a.tests).parent)
 Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('PHYSICAL_TESTS_COMPLETE',result['hardware_tests_complete'])
