from check_geometry import saved
from design import *

a,ss=saved();ch=channels()[-1];A=ch['A'];pcbfr=ch['pcb_frame'];magfr=ch['magnet_frame'];world=[]
for flex in [-65,-50,-30,0,30,55,70]:
 for dev in [-20,0,30]:
  ff=frames({'l_wrist_flex':flex,'l_wrist_deviation':dev});obs=[]
  for p,s in zip(a,ss):
   if p['name'].startswith('WD_') or ('--without-forearm' in sys.argv and p['name']=='FOREARM'):continue
   obs.append((p['name'],moved(s,ff[p['frame']])))
  world.append((flex,dev,ff,obs,np.array([e.bounds(s) for _,s in obs])))
cap=(mag_body()+mag_lid())^box([-8,-3.75,-3],[8,3.75,5])
for off in ([0,1,2,3] if '--without-forearm' in sys.argv else [0,3,5,8,10,12,15,20,25,30,40]):
 for clock in [0,90,180,270]:
  pcb=pcb_solid()+pcb_back()+pcb_tray();pcb=moved(pcb,A@T([0,0,off])@rot([0,0,1],clock));pcb=moved(pcb,np.linalg.inv(F0[pcbfr]))
  mag=moved(cap,A@T([0,0,off]));mag=moved(mag,np.linalg.inv(F0[magfr]));worst=0;hit=None
  for flex,dev,ff,obs,bb in world:
   for sol,fr in [(pcb,pcbfr),(mag,magfr)]:
    s=moved(sol,ff[fr]);b=e.bounds(s);ids=np.flatnonzero(np.all(bb[:,1]>b[0],axis=1)&np.all(bb[:,0]<b[1],axis=1))
    for j in ids:
     v=(s^obs[j][1]).volume()
     if v>worst:worst=v;hit=(flex,dev,obs[j][0])
  print(off,clock,round(worst,3),hit,flush=True)
