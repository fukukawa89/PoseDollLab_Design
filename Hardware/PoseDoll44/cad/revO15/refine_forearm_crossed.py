from associated_fit import *
from carriers_swept import motion_bank
CASES=read(H/'mechanical_manifest/revO_pose_cases.json')['cases']
rows=[];winners={}
for side in ('l',):
 include=[f'upperarm_{side}',f'elbow_{side}.flex',f'forearm_{side}.twist',f'hand_{side}.flex',f'hand_{side}.deviate','chest',f'clavicle_{side}.protract',f'clavicle_{side}.elevate'];mid=f'forearm_{side}.twist'
 cases=[CASES['arms_crossed'],{f'elbow_{side}.flex':145},{f'elbow_{side}.flex':145,f'forearm_{side}.twist':85},{f'elbow_{side}.flex':145,f'forearm_{side}.twist':-85},CASES['one_hand_up_back'],CASES['palms_turn'],ASSEMBLY_POSE,{}]
 vv=list(itertools.product((-12,-8,-6,-4,-2,0,2,4,8),(-8,-6,-4,-2,0,2,4),(0,-2,-4,2,4)))
 vv=[v for v in vv if v[0] or v[1]];vv.sort(key=lambda v:np.linalg.norm(np.array(v)-[-4,-4,0]))
 for j,d in enumerate(vv):
  for ph in (0,-15,15,-30,30,-45,45,-60,60,-90,90,180):
   bad=None;ov={}
   for char in ('quinn','manny'):
    m=next(m for m in config(char)[1] if m['id']==mid);ov[mid]={'F':(np.array(m['F'])@rot(2,ph)).tolist(),'offset_parent_mm':list(d)}
    for i,a in enumerate(cases):
     bad=associated_hit(char,a,ov,include)
     if bad:bad={'character':char,'case':i,'hit':bad};break
    if bad:break
   rows.append({'side':side,'delta':list(d),'phase':ph,'failure':bad})
   if not bad:
    winners[side]={'delta':list(d),'phase':ph};print('FOREARM RADIAL WINNER',side,winners[side],flush=True);break
  if side in winners:break
  if j%15==0:print('FOREARM RADIAL',side,j,d,flush=True)
  if j%15==0:save('forearm_radial_crossed_refinement.json',{'winners':winners,'trials':rows})
 save('forearm_radial_crossed_refinement.json',{'winners':winners,'trials':rows,'scope':'Early associated fits. Full connected audit required.'})
