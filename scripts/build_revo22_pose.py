"""Generate an interior A-pose preset without redefining encoder zero."""
from pathlib import Path
import json, sys
import numpy as np
R=Path(__file__).resolve().parents[1];B=R/'Hardware/PoseDoll44/bench/revO22'
sys.path.insert(0,str(B/'source'))
from device import forward,compound,rotation
def main():
 p=json.loads((B/'profiles/device_profile.json').read_text(encoding='utf-8-sig'))
 q=dict(p['neutral_raw_deg']);original=forward(p,q);residuals={}
 for child in ('thigh_l','thigh_r','upperarm_l','upperarm_r'):
  j=next(j for j in p['joints'] if j['child']==child);current=forward(p,q)
  target=original[child][:3,:3]
  if child.startswith('upperarm'):target=rotation([1,0,0],35 if child.endswith('_l') else -35)@target
  target=np.linalg.inv(current[j['parent']][:3,:3]@np.asarray(j['parent_to_mount_mm'])[:3,:3])@target@np.linalg.inv(np.asarray(j['rotor_to_child_mm'])[:3,:3])
  indices=[0,2,3];x=np.array([q[j['raw_ids'][i]] for i in indices])
  bounds=np.array([p['raw_limits_deg'][j['raw_ids'][i]] for i in indices],float)
  def residual(v):return (compound(j['kind'],[v[0],15.,v[1],v[2]])[:3,:3]-target).ravel()
  for _ in range(150):
   error=residual(x)
   if np.linalg.norm(error)<1e-11:break
   jac=np.column_stack([(residual(x+np.eye(3)[i]*1e-4)-error)/1e-4 for i in range(3)])
   step=np.linalg.lstsq(jac,-error,rcond=None)[0]
   for scale in (1.,.5,.25,.125,.0625,.03125):
    candidate=np.clip(x+scale*step,bounds[:,0]+3,bounds[:,1]-3)
    if np.linalg.norm(residual(candidate))<np.linalg.norm(error):x=candidate;break
   else:raise RuntimeError('Pose solve failed: '+child)
  residuals[child]=float(np.linalg.norm(residual(x)))
  assert residuals[child]<1e-8,residuals
  for key,value in zip(j['raw_ids'],[x[0],15.,x[1],x[2]]):q[key]=float(value)
 q['head/r2']=-3.
 margins={k:min(v-p['raw_limits_deg'][k][0],p['raw_limits_deg'][k][1]-v) for k,v in q.items()}
 assert min(margins.values())>=3-1e-9
 result={'schema':'POSEDOLL-O22-PRESET/1','name':'A_STAND_35','default':True,
  'raw_deg':q,'margin_to_mechanical_limits_deg':margins,'minimum_margin_deg':min(margins.values()),
  'shoulder_abduction_deg':35,'head_small_nod_deg':3,'solver_matrix_residuals':residuals,
  'frames_mm':{k:v.tolist() for k,v in forward(p,q).items()},
  'notes':'Preset only. neutral_raw_deg remains the kinematic reference. Encoder zero/sign must be measured; no all-zero reset.',
  'collision_clearance':'Separate CAD and real harness checks required.'}
 (B/'profiles/default_pose.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'minimum_margin_deg':result['minimum_margin_deg'],'residuals':residuals}))
if __name__=='__main__':main()
