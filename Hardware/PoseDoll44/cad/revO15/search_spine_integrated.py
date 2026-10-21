from layout_fullbody import *
from connected import adjacent_pairs
from search_adjacent import first_cross
names=('waist','chest','head','clavicle_l','clavicle_r','thigh_l','thigh_r');pairs={p for p in adjacent_pairs('quinn') if p<=set(names)};prof,mods=config('quinn');poses=[{}, {'waist.roll':-25}, {'waist.pitch':35,'chest.pitch':25,'waist.yaw':30,'chest.yaw':20}]
for a in prof['axes']:
 if a['id'].split('.')[0] in names:
  poses += [{a['id']:float(np.rad2deg(v))} for v in a['limits_rad']]
F0=frame([0,1,0],[1,0,0]);rr=[];choices=list(itertools.product((0,-16,-32,-48,-60,-65),(0,8,16,24,32),((0,180),(225,45),(225,180),(0,45),(90,270),(270,90))))
choices.sort(key=lambda c:np.hypot(c[0],c[1]-8)+np.hypot(c[0],c[1]+8))
for dx,up,phases in choices:
 op={}
 for j,z,ph in zip(('waist','chest'),(up-8,up+8),phases):
  F=F0@rot(2,ph);op[j]={'offset_parent_mm':[dx,0,z],'F':F.tolist(),'V':(F@rot(1,-42)).tolist()}
 ss=[]
 for a in poses:
  p,m,st,f,_=build('quinn',a,op,only=names);hit=first_cross(p,m,pairs=pairs);ss.append({'angles':a,'mapping':f,'hit':hit})
  if f or hit:break
 ok=len(ss)==len(poses) and not(ss[-1]['mapping'] or ss[-1]['hit']);rr.append({'dx':dx,'up':up,'phases':list(phases),'overrides':op,'pass_all_samples':ok,'samples':ss})
 print('SPINE',dx,up,phases,'checked',len(ss),'/',len(poses),'pass',ok,flush=True);save('spine_integrated_search.json',{'status':'SEARCH_RUNNING','trials':rr})
 if ok:break
save('spine_integrated_search.json',{'status':'SEARCH_COMPLETE','trials':rr,'source_sha256':sha(Path(__file__).with_name('layout_fullbody.py'))})
