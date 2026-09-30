from common import *
from layout_fullbody import *
from search_adjacent import first_cross
poses=[{}]+[{f'{j}.{a}':v} for j in ('waist','chest','head') for a,vs in [('yaw',(-35,35)),('pitch',(-20,40 if j=='waist' else 30)),('roll',(-25,25))] for v in vs]
for side in ('l','r'):poses += [{f'clavicle_{side}.{a}':v} for a,vs in [('protract',(-20,30)),('elevate',(-15,30))] for v in vs]
names=('waist','chest','head','clavicle_l','clavicle_r');pairs={frozenset(('chest',x)) for x in names if x!='chest'};rr=[];F0=frame([0,1,0],[1,0,0])
for dx,dz,ph in itertools.product((0,-16,16,-32),(8,16,24,32,40),range(0,360,45)):
 F=F0@rot(2,ph);op={'chest':{'F':F.tolist(),'V':(F@rot(1,-42)).tolist(),'offset_parent_mm':[dx,0,dz]}};ss=[]
 for a in poses:
  p,m,st,f,_=build('quinn',a,op,only=names);h=first_cross(p,m,pairs=pairs);ss.append({'angles':a,'mapping':f,'hit':h})
  if f or h:break
 ok=len(ss)==len(poses) and not(ss[-1]['mapping'] or ss[-1]['hit']);rr.append({'dx':dx,'dz':dz,'phase':ph,'overrides':op,'pass_all_samples':ok,'samples':ss})
 if ok:print('CHEST CLEAR',dx,dz,ph,flush=True)
 if len(rr)%8==0:print('chest tried',len(rr),flush=True);save('chest_orientation_search.json',{'trials':rr})
save('chest_orientation_search.json',{'trials':rr});print('done',len(rr),sum(r['pass_all_samples'] for r in rr),flush=True)
