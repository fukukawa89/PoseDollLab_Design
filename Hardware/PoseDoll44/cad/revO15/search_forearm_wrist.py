from common import *
from layout_fullbody import *
from search_adjacent import first_cross
rr=[]
for side in ('l','r'):
 names=(f'elbow_{side}.flex',f'forearm_{side}.twist',f'hand_{side}.flex',f'hand_{side}.deviate');pairs={frozenset(x) for x in zip(names,names[1:])};rows=[]
 for dz in (4,6,8):
  op={f'hand_{side}.{a}':{'offset_parent_mm':[0,0,-dz]} for a in ('flex','deviate')};ss=[]
  for e,t,w in itertools.product((0,145),(-90,0,90),(-65,0,65)):
   ang={names[0]:e,names[1]:t,names[2]:w};p,m,st,f,_=build('quinn',ang,op,only=names)
   # Existing left wrist stock/lever overlap is a planned mounting pocket, audited separately.
   p={k:v for k,v in p.items() if m[k]['module']!=names[3]};ss.append({'angles':ang,'mapping':f,'hit':first_cross(p,m,pairs=pairs)})
  rows.append({'shift_distal_mm':dz,'overrides':op,'samples':ss,'failures':sum(bool(s['mapping'] or s['hit']) for s in ss)});print('forearm/wrist',side,dz,rows[-1]['failures'],flush=True)
 rr.append({'side':side,'trials':rows});save('forearm_wrist_search.json',{'results':rr,'scope':'Adjacent elbow/forearm and forearm/wrist only; existing wrist-pair pocket not waived'})
