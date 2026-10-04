"""Local refinement of the selected serial clavicle, with retained failures."""
from common import *
from layout_fullbody import *
from carriers_swept import motion_bank
from connected import adjacent_pairs
from collision_fast import first_cross

def main():
 selected=['chest','head','clavicle_l.protract','clavicle_r.protract','clavicle_l.elevate','clavicle_r.elevate','upperarm_l','upperarm_r']
 cc=read(H/'mechanical_manifest/revO_pose_cases.json')['cases']
 critical=[cc['arms_crossed'],{'upperarm_l.abduct':-30,'upperarm_r.abduct':-30},*read(OUT/'serial_clavicle_bilateral_search.json')['cases']]
 variants=[(np.array([36,12,4])+v,phase) for v in sorted(itertools.product(range(-3,4),repeat=3),key=lambda v:(np.linalg.norm(v),v)) for phase in (175,185,170,190,180)]
 rows=[]
 for delta,phase in variants:
  ov={f'clavicle_{s}.elevate':{'offset_parent_mm':(delta*[1,1 if s=='l' else -1,1]).tolist()} for s in ('l','r')}
  ov['head']={'offset_parent_mm':[0,0,12]}
  for side in ('l','r'):
   F=frame([1,0,0],[0,0,-1])@rot(2,phase)
   if side=='r':F=np.diag([1,-1,1])@F
   ov[f'clavicle_{side}.elevate']['F']=F.tolist()
  fail=None
  for char in ('quinn','manny'):
   adj=adjacent_pairs(char)
   for i,a in enumerate(critical):
    pp,mm,st,f,pr=build(char,a,ov,only=selected);hit=first_cross(pp,mm,None if not a else adj,skip_same_body=bool(a))
    if hit or f:fail={'character':char,'critical':i,'hit':hit,'mapping':f};break
   if fail:break
  if not fail:
   for char in ('quinn','manny'):
    adj=adjacent_pairs(char);raw={k:s for k,s in build(char,{},ov,only=selected)[0].items()}
    raw={k:libraries()[next(m['kind'] for m in config(char)[1] if m['id']==k.split('/')[0])][0][k.split('/',1)[1]] for k in raw}
    for label,meta,T in motion_bank(char,ov):
     pp={k:pose(s,meta[k]['transform'][:3,:3],meta[k]['transform'][:3,3]) for k,s in raw.items()};hit=first_cross(pp,meta,adj,skip_same_body=True)
     if hit:fail={'character':char,'case':label,'hit':hit};break
    if fail:break
  rows.append({'delta':delta.tolist(),'phase':phase,'failure':fail})
  if not fail or len(rows)%25==0:print('REFINE',len(rows),delta.tolist(),phase,fail,flush=True)
  if not fail:
   save('serial_clavicle_refinement.json',{'winner_delta':delta.tolist(),'winner_phase':phase,'head_delta':[0,0,12],'candidates':rows,'scope':'Relevant bare modules; critical nominal assembly and moving adjacent pairs in 109 poses per character. Connected carrier check still required.','input_sha256':{str(p):sha(p) for p in [Path(__file__),Path(__file__).with_name('layout_fullbody.py'),*OUT.glob('*_parts.npz')]}});return
 save('serial_clavicle_refinement.json',{'winner_delta':None,'candidates':rows})
if __name__=='__main__':main()
