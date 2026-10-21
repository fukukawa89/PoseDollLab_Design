"""Independent reference-FK checks for raw 46 -> semantic 41 (+3 fixed)."""
from common import *
from layout_fullbody import *
sys.path.insert(0,str(R/'Tools/PoseDollHardwareBridge'))
from o15_kinematics import *

def groups_for(prof,states):
 axes={n['axis_id']:n['axis_local'] for n in prof['nodes'] if n.get('axis_id')};lim={a['id']:np.rad2deg(a['limits_rad']).tolist() for a in prof['axes']};groups=[]
 for m in states:
  n=len(m['angles_deg']);limits=[[-170,170],[-25,25],[-120 if m['kind']=='wide_tut' else -95,0],[-170,170]] if m['kind'] in ('tut','wide_tut') else [[-170,170],[-45,45],[-90,0]] if m['kind']=='three_axis' else [[-30,30],[-50,0]] if m['kind']=='clavicle_core' else [[-25,25],[-45,45]] if m['kind']=='ankle_core' else [[-90,145]]
  groups.append({**m,'raw_ids':[m['id']+'/r'+str(i) for i in range(n)],'raw_limits_deg':limits,'semantic_axes':[axes[a] for a in m['axis_ids']],'semantic_limits_deg':[lim[a] for a in m['axis_ids']]})
 return groups

def main():
 cases=read(H/'mechanical_manifest/revO_pose_cases.json')['cases'];rows=[];snap=None
 for char in ('quinn','manny'):
  for label,angles in cases.items():
   _,_,st,f,prof=build(char,angles,geometry=False);gg=groups_for(prof,st);raw={rid:RawAngle(float(a),'valid',17,'synthetic-boot',4.) for g in gg for rid,a in zip(g['raw_ids'],g['angles_deg'])};results=[]
   for g in gg:
    result=compose_group(g,raw,capture_id=17,boot_id='synthetic-boot',max_age_ms=1000,previous=[angles.get(a,0) for a in g['axis_ids']]);expect=semantic_matrix(g['semantic_axes'],[angles.get(a,0) for a in g['axis_ids']]);err=float(np.max(np.abs(semantic_matrix(g['semantic_axes'],result['angles_deg'])-expect))) if result['status']=='valid' else None;results.append({'module':g['id'],'result':result,'rotation_matrix_error':err})
   rows.append({'character':char,'pose':label,'mapping_failures':f,'results':results});print('kinematics',char,label,'fail',len(f)+sum(r['result']['status']!='valid' or r['rotation_matrix_error']>1e-7 for r in results),flush=True)
   if char=='quinn' and label=='neutral':snap=(gg,raw)
 gg,raw=snap;faults=[]
 for g in gg:
  for rid in g['raw_ids']:
   for kind in ('missing','fault','stale','mixed_request','mixed_boot','nan'):
    rr=dict(raw);old=rr[rid]
    if kind=='missing':del rr[rid]
    else:rr[rid]=RawAngle(float('nan') if kind=='nan' else old.angle_deg,'fault' if kind=='fault' else 'valid',18 if kind=='mixed_request' else 17,'other' if kind=='mixed_boot' else 'synthetic-boot',1001. if kind=='stale' else 4.)
    out=compose_group(g,rr,capture_id=17,boot_id='synthetic-boot',max_age_ms=1000);ok=out['status']==('missing' if kind=='missing' else 'fault') and all(v is None for v in out['angles_deg']);faults.append({'raw':rid,'injected':kind,'pass':ok})
 mapping={'groups':gg,'fixed_axes':['pelvis.yaw','pelvis.pitch','pelvis.roll']};order=read(R/'Tools/PoseDollHardwareBridge/layout.json')['axis_order'];frame_tests=[]
 good=compose_frame(mapping,raw,order,capture_id=17,boot_id='synthetic-boot');frame_tests.append({'case':'all_valid','pass':good['status']=='valid' and len(good['channels'])==44 and sum(x['status']=='fixed' for x in good['channels'])==3 and not good['capture_eligible']})
 for rid in raw:
  rr=dict(raw);del rr[rid];out=compose_frame(mapping,rr,order,capture_id=17,boot_id='synthetic-boot');frame_tests.append({'case':'missing_'+rid,'pass':out['status']=='missing' and any(v['angle_deg'] is None for v in out['channels']) and not out['capture_eligible']})
 import copy
 for name in ('duplicate_raw','duplicate_semantic','missing_group','extra_raw','duplicate_fixed','bad_order'):
  mm=copy.deepcopy(mapping);rr=dict(raw);oo=list(order)
  if name=='duplicate_raw':mm['groups'][1]['raw_ids'][0]=mm['groups'][0]['raw_ids'][0]
  if name=='duplicate_semantic':mm['groups'][1]['axis_ids'][0]=mm['groups'][0]['axis_ids'][0]
  if name=='missing_group':mm['groups'].pop()
  if name=='extra_raw':rr['unknown/r0']=next(iter(raw.values()))
  if name=='duplicate_fixed':mm['fixed_axes'].append('pelvis.yaw')
  if name=='bad_order':oo[0]=oo[1]
  rejected=False
  try:compose_frame(mm,rr,oo,capture_id=17,boot_id='synthetic-boot')
  except ValueError:rejected=True
  frame_tests.append({'case':name,'pass':rejected})
 assert all(x['pass'] for x in frame_tests)
 save('whole_frame_validation.json',{'tests':frame_tests,'passed':sum(x['pass'] for x in frame_tests),'total':len(frame_tests),'source_sha256':sha(R/'Tools/PoseDollHardwareBridge/o15_kinematics.py'),'physical_calibration':False})
 counts={'raw':sum(len(g['raw_ids']) for g in gg),'measured_semantic':sum(len(g['axis_ids']) for g in gg),'fixed_semantic':3};assert counts=={'raw':46,'measured_semantic':41,'fixed_semantic':3}
 save('kinematics_validation.json',{'counts':counts,'pose_results':rows,'fault_injection':faults,'physical_calibration':False,'production_transport_connected':False,'source_sha256':sha(R/'Tools/PoseDollHardwareBridge/o15_kinematics.py')});save('raw46_mapping_candidate.json',{'schema':'O15-KINEMATIC-CANDIDATE/1','hardware_calibrated':False,'capture_eligible':False,'fixed_axes':['pelvis.yaw','pelvis.pitch','pelvis.roll'],'groups':gg});print('FAULTS',len(faults),sum(f['pass'] for f in faults),flush=True)
if __name__=='__main__':main()
