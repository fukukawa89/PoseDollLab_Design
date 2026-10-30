from check_geometry import saved
from design import *
a,ss=saved();cs=channels();wd=cs[-1];rf=cs[2];AA=rf['A'];wc=wd['A'];best=[]
for clock in range(0,360,15):
  edits=[]
  for p,s in zip(a,ss):
    if p['name']=='FOREARM' or p['name'].startswith('WD_'):continue
    if not p.get('baseline_name') and p['name'].startswith('RF_'):
      tr=np.linalg.inv(F0[p['frame']])@AA@rot([0,0,1],clock)@np.linalg.inv(AA)@F0[p['frame']];s=moved(s,tr)
    edits.append((p,s))
  worst=0;hit=None
  for flex in [-65,-55,-40,0,40,55,70]:
    for dev in [-20,0,30]:
      ff=frames({'l_wrist_flex':flex,'l_wrist_deviation':dev});obs=[moved(s,ff[p['frame']]) for p,s in edits];bb=np.array([e.bounds(s) for s in obs]);s=moved(moved(pcb_solid()+pcb_tray()+pcb_back(),np.linalg.inv(F0[wd['pcb_frame']])@wc),ff[wd['pcb_frame']]);b=e.bounds(s)
      ids=np.flatnonzero(np.all(bb[:,1]>b[0],axis=1)&np.all(bb[:,0]<b[1],axis=1))
      for j in ids:
        ov=(s^obs[j]).volume()
        if ov>worst:worst=ov;hit=(flex,dev,edits[j][0]['name'])
  print(clock,round(worst,4),hit,flush=True)
