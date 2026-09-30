from associated_fit import *
from carriers_swept import motion_bank

CASES=read(H/'mechanical_manifest/revO_pose_cases.json')['cases']
CLAV_CASES=[CASES['arms_side'],{'upperarm_l.twist':-90,'upperarm_r.twist':-90},{'clavicle_l.protract':30,'clavicle_r.protract':30},CASES['arms_crossed'],ASSEMBLY_POSE,{},*read(OUT/'serial_clavicle_bilateral_search.json')['cases']]

def clavicle():
 include=['chest','head','clavicle_l.protract','clavicle_r.protract','clavicle_l.elevate','clavicle_r.elevate','upperarm_l','upperarm_r'];rr=[]
 vv=list(itertools.product((-24,-28,-32,-36,-40),(18,22,26),(0,4,-4,8,-8,12)))
 vv.sort(key=lambda v:np.linalg.norm(np.array(v)-[-24,18,0]))
 for delta in vv:
  ov={f'clavicle_{side}.protract':{'offset_parent_mm':(np.array(delta)*[1,1 if side=='l' else -1,1]).tolist()} for side in ('l','r')};bad=None
  for char in ('quinn','manny'):
   for i,a in enumerate(CLAV_CASES):
    bad=associated_hit(char,a,ov,include)
    if bad:bad={'character':char,'case':i,'hit':bad};break
   if bad:break
  rr.append({'delta':list(delta),'failure':bad})
  print('ASSOCIATED CLAV',delta,bad,flush=True)
  if not bad:
   save('associated_clavicle_refinement.json',{'winner':list(delta),'trials':rr,'input_sha256':{str(p):sha(p) for p in [Path(__file__),Path(__file__).with_name('layout_fullbody.py'),*OUT.glob('*_parts.npz')]}});return
 save('associated_clavicle_refinement.json',{'winner':None,'trials':rr})

def forearm():
 include=['upperarm_l','upperarm_r','elbow_l.flex','elbow_r.flex','forearm_l.twist','forearm_r.twist','hand_l.flex','hand_r.flex','hand_l.deviate','hand_r.deviate'];rows=[]
 cases=[{'elbow_l.flex':145,'elbow_r.flex':145},CASES['one_hand_up_back'],CASES['palms_turn'],ASSEMBLY_POSE,{}]
 for phase in (45,-45,90,-90,135,-135,180,0):
  ov={}
  for m in config('quinn')[1]:
   if m['id'].startswith('forearm_'):ov[m['id']]={'F':(np.array(m['F'])@rot(2,phase)).tolist()}
  bad=None
  for char in ('quinn','manny'):
   for i,a in enumerate(cases):
    bad=associated_hit(char,a,ov,include)
    if bad:bad={'character':char,'case':i,'hit':bad};break
   if bad:break
  rows.append({'phase':phase,'failure':bad});print('ASSOCIATED FOREARM',phase,bad,flush=True)
  if not bad:
   save('associated_forearm_refinement.json',{'winner_phase':phase,'trials':rows});return
 save('associated_forearm_refinement.json',{'winner_phase':None,'trials':rows})
if __name__=='__main__':
 if len(sys.argv)>1 and sys.argv[1]=='forearm':forearm()
 else:clavicle()
