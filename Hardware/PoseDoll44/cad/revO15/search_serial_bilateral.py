"""Bilateral serial clavicle placement; mirrored printed parts, physical PCB correction."""
from common import *
import search_serial_clavicle as ss
import search_serial_clavicle_outward as outward
from collision_fast import first_cross
BASE=outward.config

def config(char):
 p,mm=BASE(char);by={m['id']:m for m in mm}
 for typ in ('protract','elevate'):
  by['clavicle_r.'+typ]['F']=(np.diag([1,-1,1])@np.array(by['clavicle_l.'+typ]['F'])).tolist()
 return p,mm

CASES=[{}, {'clavicle_l.protract':30,'clavicle_r.protract':30},{'clavicle_l.protract':-20,'clavicle_r.protract':-20},{'clavicle_l.elevate':30,'clavicle_r.elevate':30},{'clavicle_l.elevate':-15,'clavicle_r.elevate':-15},{'clavicle_l.protract':30,'clavicle_r.protract':30,'clavicle_l.elevate':30,'clavicle_r.elevate':30},{'clavicle_l.protract':-20,'clavicle_r.protract':-20,'clavicle_l.elevate':30,'clavicle_r.elevate':30},{'upperarm_l.abduct':150,'upperarm_r.abduct':150},{'upperarm_l.flex':160,'upperarm_r.flex':160}]

def check(include,cases=CASES,chars=('quinn',)):
 for char in chars:
  for i,a in enumerate(cases):
   p,m,st,f,pr=ss.lf.build(char,a,only=include)
   _,mm=config(char);pairs=set()
   for x,y in itertools.combinations(mm,2):
    mirrors=x['id'].replace('_l.','_r.')==y['id'] or y['id'].replace('_l.','_r.')==x['id']
    if x['child']==y['parent'] or y['child']==x['parent'] or x['parent']==y['parent'] and not mirrors:pairs.add(frozenset((x['id'],y['id'])))
   # Zero-pose assembly must be clear even for nonadjacent modules. During
   # motion, user-permitted remote-body contacts remain a separate final audit.
   h=first_cross(p,m,None if not a else pairs)
   if h or f:return {'character':char,'case':i,'hit':h,'mapping':f}
 return None

def main():
 ss.lf.config=config;seed=read(OUT/'serial_clavicle_outward_search.json');ss.CHOICE.update(seed['winners'][0]);fixed=['head','chest','upperarm_l','upperarm_r'];incs=[f'clavicle_{s}.{t}' for s in ('l','r') for t in ('protract','elevate')];first=[];attempt=0;rows=[]
 for dy,dz,phase,sign in itertools.product((18,22,26,30),(0,-10,10),(45,225,270,315,0,90,135,180),(1,-1)):
  ss.CHOICE['protract']={'delta':[-24,dy,dz],'phase':phase,'sign':sign};bad=check(fixed+['clavicle_l.protract','clavicle_r.protract'],[CASES[i] for i in (0,1,2,7,8)]);attempt+=1
  if not bad:
   first.append(dict(ss.CHOICE['protract']));print('BILATERAL FIRST',first[-1],flush=True)
   if len(first)>=12:break
  if attempt%80==0:print('FIRST PAIR',attempt,flush=True)
 save('serial_clavicle_bilateral_search.json',{'first':first,'first_attempts':attempt,'winners':[]})
 if not first:return
 second=[{'delta':[dx,dy,dz],'phase':ph,'sign':sg} for dx,dy,dz,ph,sg in itertools.product((36,42,48,30),(12,16,18,22,26),(12,20,4,28),range(0,360,45),(1,-1))];second.sort(key=lambda c:np.linalg.norm(c['delta']));attempt=0
 for c2 in second:
  ss.CHOICE['elevate']=c2
  if check(fixed+['clavicle_l.elevate','clavicle_r.elevate'],[{}]):continue
  for c1 in first:
   ss.CHOICE['protract']=c1;attempt+=1;bad=check(fixed+incs,chars=('quinn','manny'))
   if not bad:
    winner=dict(ss.CHOICE);save('serial_clavicle_bilateral_search.json',{'first':first,'attempts':attempt,'winners':[winner],'shoulder_F_left':seed['shoulder_F_left'],'shoulder_offset_mm':8,'cases':CASES,'input_sha256':{str(p):sha(p) for p in OUT.glob('*_parts.npz')},'physical_tested':False});print('BILATERAL WINNER',winner,flush=True);return
   if attempt%40==0:print('COMPLETE PAIR',attempt,'last',bad,flush=True)
 save('serial_clavicle_bilateral_search.json',{'first':first,'attempts':attempt,'winners':[],'cases':CASES})
if __name__=='__main__':main()
