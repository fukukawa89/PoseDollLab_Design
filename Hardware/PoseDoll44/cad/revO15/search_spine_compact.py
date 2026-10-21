from common import *
from layout_fullbody import build
from search_adjacent import first_cross
poses=[{}]+[{f'waist.{a}':v} for a,vs in [('yaw',(-35,35)),('pitch',(-20,40)),('roll',(-25,25))] for v in vs]
for side in ('l','r'):poses += [{f'thigh_{side}.{a}':v} for a,vs in [('flex',(-30,125)),('abduct',(-25,65)),('twist',(-50,50))] for v in vs]
rr=[]
for up,dx in itertools.product((12,20,28,36), (0,-12,-24,-36)):
 op={'waist':{'offset_parent_mm':[dx,0,up-8]},'chest':{'offset_parent_mm':[dx,0,up+8]}};ss=[]
 for a in poses:
  p,m,st,f,_=build('quinn',a,op,only=('waist','thigh_l','thigh_r'));ss.append({'angles':a,'mapping':f,'hit':first_cross(p,m,pairs={frozenset(('waist','thigh_l')),frozenset(('waist','thigh_r'))})})
 rr.append({'up':up,'dx':dx,'overrides':op,'failures':sum(bool(s['mapping'] or s['hit']) for s in ss),'samples':ss});print('compact spine',up,dx,rr[-1]['failures'],flush=True);save('compact_spine_search.json',{'ranked':sorted(rr,key=lambda r:(r['failures'],np.hypot(r['dx'],r['up']-8)))})
