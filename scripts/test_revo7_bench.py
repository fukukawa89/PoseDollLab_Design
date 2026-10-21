from pathlib import Path
import copy,hashlib,json,sys,tempfile
from analyze_revo7_bench import analyze
R=Path(__file__).resolve().parents[1];H=R/'Hardware/PoseDoll44';planpath=H/'bench/revO7/plan.json';plan=json.loads(planpath.read_text());digest=hashlib.sha256(planpath.read_bytes()).hexdigest();checks=[]
with tempfile.TemporaryDirectory(prefix='o7-bench-',dir=R/'.local') as td:
 root=Path(td);p=root/'synthetic-instrument.txt';p.write_text('SYNTHETIC TEST VECTOR NOT HARDWARE',encoding='utf-8');rawhash=hashlib.sha256(p.read_bytes()).hexdigest()
 data={'schema':'o7-material-bench-data-v1','evidence_kind':'measurement','operator':'TEST ONLY','measured_at':'TEST ONLY','fixture_calibration_id':'TEST ONLY','material_lot':'TEST ONLY','mating_alloy_surface':'TEST ONLY','plan_sha256':digest,'samples':[]}
 assert analyze(plan,data,root,digest)['status']=='AWAITING_HARDWARE';checks.append('empty remains awaiting hardware')
 for fam,torque in [('LP6',.27),('M4',.18)]:
  for d in ['cw','ccw']:
   for i in range(3):data['samples'].append({'sample_id':f'{fam}-{d}-{i}','family':fam,'preload_setting_id':'test-only','direction':d,'preload_N':200,'one_face_breakaway_torque_Nm':torque,'applied_one_face_hold_torque_Nm':torque,'hold_seconds':60,'angle_drift_deg':.1,'temperature_C':25,'raw_log_relative_path':p.name,'raw_log_sha256':rawhash})
 q=analyze(plan,data,root,digest);assert q['status']=='COUPON_CANDIDATES_RECORDED' and not q['full_joint_qualified'] and not q['manufacturing_released'];checks.append('synthetic positive control never releases joint')
 mutations=[('evidence_kind','synthetic'),('plan_sha256','wrong'),('operator','')]
 for key,value in mutations:
  x=copy.deepcopy(data);x[key]=value;assert analyze(plan,x,root,digest)['status']=='INVALID_EVIDENCE';checks.append(key)
 for key,value in [('preload_N',0),('preload_N',float('nan')),('one_face_breakaway_torque_Nm',float('inf')),('hold_seconds',True),('family','unknown'),('direction','invalid'),('sample_id',data['samples'][1]['sample_id']),('raw_log_relative_path','../outside.txt'),('raw_log_relative_path',str(p.resolve())),('raw_log_sha256','wrong')]:
  x=copy.deepcopy(data);x['samples'][0][key]=value;assert analyze(plan,x,root,digest)['status']=='INVALID_EVIDENCE',(key,value);checks.append(key+':'+str(value))
 for key,value in [('hold_seconds',59),('angle_drift_deg',.31),('applied_one_face_hold_torque_Nm',0),('one_face_breakaway_torque_Nm',.01),('one_face_breakaway_torque_Nm',2),('preload_N',300)]:
  x=copy.deepcopy(data);x['samples'][0][key]=value;q=analyze(plan,x,root,digest);assert q['status']=='MORE_MEASUREMENTS_OR_DIFFERENT_SETTING_REQUIRED';checks.append('screen '+key+':'+str(value))
 x=copy.deepcopy(data);x['samples']=x['samples'][1:];assert analyze(plan,x,root,digest)['status']=='MORE_MEASUREMENTS_OR_DIFFERENT_SETTING_REQUIRED';checks.append('missing repeat')
 p.write_text('changed',encoding='utf-8');assert analyze(plan,data,root,digest)['status']=='INVALID_EVIDENCE';checks.append('raw file tamper')
out=H/'verification/revO7/runs/o7_20260924_r1/bench_import_tests.json';out.write_text(json.dumps({'status':'PASS_SOFTWARE_ONLY','count':len(checks),'cases':checks,'test_values_are_synthetic':True,'physical_tested':False,'input_sha256':{p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),R/'scripts/analyze_revo7_bench.py',planpath]}},indent=2)+'\n',encoding='utf-8');print(len(checks),'software assertions passed')
