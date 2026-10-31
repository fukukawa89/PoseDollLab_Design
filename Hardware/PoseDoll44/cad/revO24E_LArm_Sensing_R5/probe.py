from common import *
a,S=world_solids();ints=load(BASE/'interfaces.json')
for r in ints['rolls']:
 W=np.array(r['W']); iw=np.linalg.inv(W); solids={p['name']:moved(S[p['name']],iw) for p in a}
 print('\n',r['id'])
 for z in [14,16,18,20,22,24,26,28,30,32,34]:
  test=box([-6.3,-5.3,z],[6.3,5.3,z+3.2])
  hits={n:round((s^test).volume(),1) for n,s in solids.items() if (s^test).volume()>.02}
  print('PCB',z,hits)
 # Half-spoke at each height, swept over the real single-axis range, against fixed structures.
 axis={'RP':'l_shoulder_flex','RU':'l_upperarm_roll','RF':'l_forearm_roll'}[r['id']]
 limit=next(x['limits_deg'] for x in PROFILE['axes'] if x['id']==axis)
 radius=28 if r['id']=='RF' else 24
 for z in [18,20,22,24,26,28,30,32]:
  candidate=beam([0,0,z],[radius,0,z],1.8)
  fixed=union(moved(s,np.linalg.inv(W)) for p,s in zip(a,S.values()) if p['frame']==r['fixed_frame'])
  best=(1e6,None)
  for clock in range(0,360,10):
   hits=[(moved(candidate,rot([0,0,1],clock+sg*q))^fixed).volume() for q in np.linspace(*limit,18) for sg in [1]]
   score=max(hits)
   if score<best[0]:best=(score,clock)
  print('SPOKE',z,best)
