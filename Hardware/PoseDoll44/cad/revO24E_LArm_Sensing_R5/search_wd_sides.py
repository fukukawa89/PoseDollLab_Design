from check_geometry import saved
from design import *
a,ss=saved();ch=channels()[-1];pf=ch['pcb_frame'];mf=ch['magnet_frame'];world=[]
for flex in [-65,-55,-35,0,35,55,70]:
 for dev in [-20,0,30]:
  ff=frames({'l_wrist_flex':flex,'l_wrist_deviation':dev});obs=[(p['name'],moved(s,ff[p['frame']])) for p,s in zip(a,ss) if not p['name'].startswith('WD_')]
  world.append((flex,dev,ff,obs,np.array([e.bounds(s) for _,s in obs])))
for side in [-1,1]:
 A=F0['l_wrist_flex']@T([side*19.8,0,0],basis([side,0,0]))
 for off in [0,1,2,3,4,5,7,10]:
  for clock in [0,180]:
   p=moved(pcb_solid(True)+pcb_back(True)+pcb_tray(True),np.linalg.inv(F0[pf])@A@T([0,0,off])@rot([0,0,1],clock))
   m=moved((mag_body()+mag_lid())^box([-8,-3.75,-3],[8,3.75,5]),np.linalg.inv(F0[mf])@A@T([0,0,off]));worst=0;hit=None
   for flex,dev,ff,obs,bb in world:
    for solid,fr in [(p,pf),(m,mf)]:
     v=moved(solid,ff[fr]);b=e.bounds(v);ids=np.flatnonzero(np.all(bb[:,1]>b[0],axis=1)&np.all(bb[:,0]<b[1],axis=1))
     for j in ids:
      ov=(v^obs[j][1]).volume()
      if ov>worst:worst=ov;hit=(flex,dev,obs[j][0])
   print(side,off,clock,round(worst,3),hit,flush=True)
