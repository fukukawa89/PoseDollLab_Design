"""Fit a bounded installed-axis calibration from an independent angle fixture.
Input is JSON, no sensor ports opened. No physical qualification flags are granted.
"""
from pathlib import Path
import argparse,json,math,hashlib
from device import number
from measurement import correct_sensor
def angular_delta(a,b):return (a-b+180)%360-180
def fit_axis(data):
 sign=data.get('sign');unc=data.get('reference_uncertainty_deg')
 if sign not in (-1,1) or isinstance(sign,bool):raise ValueError('measured sign must be +/-1')
 if not number(unc) or not 0<unc<=.1:raise ValueError('independent fixture uncertainty must be <=0.1deg')
 if data.get('source_kind') not in ('MEASURED_FIXTURE','SYNTHETIC'):raise ValueError('source provenance required')
 if not data.get('fixture_id') or not data.get('axis_id'):raise ValueError('fixture and axis identity required')
 rows=data.get('samples',[])
 for row in rows:
  if row.get('phase') not in ('fit','validate') or row.get('direction') not in ('cw','ccw'):raise ValueError('sample phase/direction')
  if not all(number(row.get(k)) for k in ('sensor_deg','fixture_joint_deg','peak_to_peak_deg')):raise ValueError('finite samples required')
  if not 0<=row['sensor_deg']<360 or not 0<=row['peak_to_peak_deg']<=.3:raise ValueError('unstable or invalid sample')
  if not isinstance(row.get('sample_count'),int) or row['sample_count']<20:raise ValueError('at least 20 samples per hold')
 fits=[r for r in rows if r['phase']=='fit']
 if len(fits)<5:raise ValueError('at least five fit holds')
 # Sort in the direction of increasing encoder angle, independent of 0/360 wrap.
 fits=sorted(fits,key=lambda r:sign*r['fixture_joint_deg'])
 anchor=fits[0]['sensor_deg'];reference=fits[0]['fixture_joint_deg'];knots=[]
 for row in fits:
  u=(row['sensor_deg']-anchor)%360
  expected=sign*(row['fixture_joint_deg']-reference)
  knots.append([u,expected-u])
 lut={'kind':'bounded_delta_deg','source':data['source_kind'],'anchor_sensor_deg':anchor,'knots':knots}
 for row in fits:correct_sensor(row['sensor_deg'],lut)
 validators=[r for r in rows if r['phase']=='validate']
 refs=sorted(set(r['fixture_joint_deg'] for r in validators))
 if len(refs)<4:raise ValueError('at least four independent validation angles')
 if any(abs(v-f['fixture_joint_deg'])<.001 for v in refs for f in fits):raise ValueError('validation angles must differ from fit knots')
 fmin,fmax=sorted([fits[0]['fixture_joint_deg'],fits[-1]['fixture_joint_deg']])
 if refs[0]>fmin+.15*(fmax-fmin) or refs[-1]<fmax-.15*(fmax-fmin):raise ValueError('validation must cover both ends')
 errors=[];repeat=[]
 for ref in refs:
  pair=[r for r in validators if r['fixture_joint_deg']==ref]
  if sorted(r['direction'] for r in pair)!=['ccw','cw']:raise ValueError('each validation angle needs CW and CCW')
  measured=[]
  for row in pair:
   corrected=correct_sensor(row['sensor_deg'],lut)
   # The range is <355deg, unwrap against the known fixture for qualification.
   candidates=[reference+sign*((corrected-anchor)%360+360*n) for n in (-1,0,1)]
   q=min(candidates,key=lambda v:abs(v-ref));measured.append(q);errors.append(q-ref)
  repeat.append(abs(measured[0]-measured[1]))
 maxerror=max(map(abs,errors));repeatmax=max(repeat)
 if maxerror>1 or repeatmax>.3:raise ValueError('accuracy or bidirectional repeatability failed')
 bound=maxerror+unc
 if bound>1.25:raise ValueError('diagnostic uncertainty budget exceeded')
 source_hash=hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
 lut['fixture_id']=data['fixture_id'];lut['evidence_sha256']=source_hash
 axis={'sensor_zero_deg':anchor,'reference_joint_deg':reference,'sign':sign,
       'diagnostic_error_bound_deg':bound,'linearization':lut}
 report={'status':'PASS_NUMERICAL_EVALUATION','source_kind':data['source_kind'],
  'axis_id':data['axis_id'],'fixture_id':data['fixture_id'],'evidence_sha256':source_hash,
  'max_independent_error_deg':maxerror,'max_cw_ccw_difference_deg':repeatmax,
  'fixture_uncertainty_deg':unc,'diagnostic_error_bound_deg':bound,
  'validated_joint_interval_deg':[fmin,fmax],'fit_points':len(fits),'validation_points':len(validators),
  'whole_device_physical_qualification_granted':False}
 return axis,report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('samples');p.add_argument('--output',required=True);a=p.parse_args()
 data=json.loads(Path(a.samples).read_text(encoding='utf-8-sig'));axis,report=fit_axis(data)
 Path(a.output).write_text(json.dumps({'axis':axis,'report':report,'original_samples':data},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
