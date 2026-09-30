from common import *
from layout_fullbody import *
from search_adjacent import first_cross
poses=[{}]+[{f'waist.{a}':v} for a,vs in [('yaw',(-35,35)),('pitch',(-20,40)),('roll',(-25,25))] for v in vs]
for side in ('l','r'):poses += [{f'thigh_{side}.{a}':v} for a,vs in [('flex',(-30,125)),('abduct',(-25,65)),('twist',(-50,50))] for v in vs]
rr=[];F0=frame([0,1,0],[1,0,0])
for dx,dz,ph in itertools.product((0,-12,-24),(0,8,16),range(0,360,45)):
 F=F0@rot(2,ph);op={'waist':{'F':F.tolist(),'V':(F@rot(1,-42)).tolist(),'offset_parent_mm':[dx,0,dz]}};ss=[]
 for a in poses:
  p,m,st,f,_=build('quinn',a,op,only=('waist','thigh_l','thigh_r'));h=first_cross(p,m,pairs={frozenset(('waist','thigh_l')),frozenset(('waist','thigh_r'))});ss.append({'angles':a,'mapping':f,'hit':h})
  if f or h:break
 ok=len(ss)==len(poses) and not(ss[-1]['mapping'] or ss[-1]['hit']);rr.append({'dx':dx,'dz':dz,'phase':ph,'overrides':op,'pass_all_samples':ok,'samples':ss})
 if ok:print('compact orientation CLEAR',dx,dz,ph,flush=True)
 save('waist_orientation_search.json',{'trials':rr})
print('done',len(rr),sum(r['pass_all_samples'] for r in rr),flush=True)
