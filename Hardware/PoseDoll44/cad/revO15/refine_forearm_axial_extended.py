from associated_fit import *
CASES=read(H/'mechanical_manifest/revO_pose_cases.json')['cases']
rows=[];winners={}
for side in ('l','r'):
 include=[f'upperarm_{side}',f'elbow_{side}.flex',f'forearm_{side}.twist',f'hand_{side}.flex',f'hand_{side}.deviate'];mid=f'forearm_{side}.twist'
 cases=[{f'elbow_{side}.flex':145},{f'elbow_{side}.flex':145,f'forearm_{side}.twist':85},{f'elbow_{side}.flex':145,f'forearm_{side}.twist':-85},CASES['one_hand_up_back'],CASES['palms_turn'],ASSEMBLY_POSE,{}]
 for dz in (-12,-16,-20,-24,-28,-32,-36,-40):
  for ph in (-90,90,-75,75,-105,105,-60,60,-120,120,-45,45,0,180,135,-135):
   ov={};bad=None
   for char in ('quinn','manny'):
    m=next(m for m in config(char)[1] if m['id']==mid);ov[mid]={'F':(np.array(m['F'])@rot(2,ph)).tolist(),'offset_parent_mm':[0,0,dz]}
    for i,a in enumerate(cases):
     bad=associated_hit(char,a,ov,include)
     if bad:bad={'character':char,'case':i,'hit':bad};break
    if bad:break
   rows.append({'side':side,'dz':dz,'phase':ph,'failure':bad})
   if not bad:
    winners[side]={'delta_z':dz,'phase':ph};print('FOREARM AXIAL WINNER',side,winners[side],flush=True);break
  if side in winners:break
  print('FOREARM AXIAL',side,dz,'none',flush=True)
 save('forearm_axial_refinement_extended.json',{'winners':winners,'trials':rows,'scope':'Early associated endpoint fits. Full 109-pose connected audit still required.'})
