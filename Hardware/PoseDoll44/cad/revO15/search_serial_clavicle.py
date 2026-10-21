"""Alternative clavicle: two existing single-axis hinges, no new stock family."""
from common import *
import layout_fullbody as lf
from collision_fast import first_cross
BASE=lf.config
CHOICE={}

def config(char):
 p,mods=BASE(char);orig=read(lf.G3/f'layouts/{char}/anatomy_profile.json');on={n['id']:n for n in orig['nodes']}
 for n in p['nodes']:
  if n.get('axis_id','').startswith('clavicle_') or n['id'].startswith('upperarm_') and n.get('axis_id','').endswith('.flex'):
   n['parent_to_axis']=on[n['id']]['parent_to_axis']
 mods=[m for m in mods if not m['id'].startswith('clavicle_')]
 for n in p['nodes']:
  aid=n.get('axis_id','')
  if not aid.startswith('clavicle_'):continue
  side=1 if '_l.' in aid else -1;typ=aid.split('.')[-1];c=CHOICE.get(typ,{'delta':[0,20,0],'phase':0,'sign':1});F=lf.frame(n['axis_local'],[1,0,0] if typ=='protract' else [0,0,-1])@rot(2,c['phase'])
  if c['sign']==-1:F=F@rot(0,180)
  d=np.array(c['delta'])*[1,side,1]
  mods.append({'id':aid,'kind':'hinge','axis_ids':[aid],'parent':n['parent'],'child':n['id'],'F':F.tolist(),'hinge_sign':c['sign'],'offset_parent_mm':d.tolist()})
 return p,mods

def check(cases,include):
 for i,ang in enumerate(cases):
  p,m,st,f,pr=lf.build('quinn',ang,only=include)
  pairs={frozenset((x,y)) for x in include if x.startswith('clavicle_') for y in include if x!=y};h=first_cross(p,m,pairs)
  if f or h:return {'case':i,'hit':h,'mapping':f}
 return None

def main():
 lf.config=config;positions=list(itertools.product((-24,-12,0,12,24),(14,22,30),(-20,-10,0,10,20)));positions.sort(key=lambda x:np.linalg.norm(x));first=[];count=0
 cases=[{}, {'clavicle_l.protract':30},{'clavicle_l.protract':-20},{'upperarm_l.abduct':150},{'upperarm_l.flex':160}]
 for d,phase,sign in itertools.product(positions,range(0,360,45),(-1,1)):
  c={'delta':d,'phase':phase,'sign':sign};CHOICE['protract']=c;bad=check(cases,['clavicle_l.protract','head','chest','upperarm_l']);count+=1
  if not bad:
   first.append(c);print('FIRST',c,flush=True)
   if len(first)>=12:break
  if count%160==0:print('FIRST SEARCH',count,flush=True)
 save('serial_clavicle_search.json',{'first_axis_candidates':first,'first_tested':count,'winners':[]})
 if not first:return
 cases += [{'clavicle_l.elevate':30},{'clavicle_l.elevate':-15},{'clavicle_l.protract':30,'clavicle_l.elevate':30},{'clavicle_l.protract':-20,'clavicle_l.elevate':30}]
 seconds=list(itertools.product((-36,-24,-12,0,12,24,36),(6,18,30,42),(-24,-12,0,12,24)));seconds.sort(key=lambda x:np.linalg.norm(x));wins=[];count=0
 for d,phase,sign in itertools.product(seconds,range(0,360,45),(-1,1)):
  c2={'delta':d,'phase':phase,'sign':sign};CHOICE['elevate']=c2
  # First test the second hinge against surrounding modules without first hinge.
  bad=check([{}],['clavicle_l.elevate','head','chest','upperarm_l']);count+=1
  if bad:continue
  for c1 in first:
   CHOICE['protract']=c1
   if np.linalg.norm(np.array(c1['delta'])-d)<18:continue
   bad=check(cases,['clavicle_l.protract','clavicle_l.elevate','head','chest','upperarm_l'])
   if not bad:
    winner={'protract':c1,'elevate':c2};wins.append(winner);print('SERIAL WINNER',winner,flush=True)
    save('serial_clavicle_search.json',{'first_axis_candidates':first,'second_tested':count,'winners':wins,'cases':cases,'scope':'Left-side module checks only. Bilateral and connected validation still required.'});return
  if count%160==0:print('SECOND SEARCH',count,flush=True)
 save('serial_clavicle_search.json',{'first_axis_candidates':first,'second_tested':count,'winners':wins,'cases':cases})
if __name__=='__main__':main()
