from layout_fullbody import *
from search_adjacent import first_cross
prof,_=config('quinn');limits={a['id']:np.rad2deg(a['limits_rad']) for a in prof['axes']};cands=read(OUT/'trunk_orientation_candidates.json')['groups'];valid={};trials={};inputs={str(p):sha(p) for p in [Path(__file__).with_name('layout_fullbody.py'),*OUT.glob('*_parts.npz')]}
cache=read(OUT/'trunk_compact_search_waist_candidates.json');valid['waist']=cache['individual_valid']['waist'];trials['waist']=cache['trials']['waist']
for name in ('chest',):
 unique={}
 for c in cands[name]:
  key=tuple(np.round(np.asarray(c['F']),7).ravel())
  if key not in unique or c['minimum_margin_deg']>unique[key]['minimum_margin_deg']:unique[key]=c
 orientation=sorted(unique.values(),key=lambda c:-c['minimum_margin_deg'])
 positions=([[0,0,z] for z in (0,12,20,28)]+[[x,y,z] for x,y,z in ((-12,0,16),(12,0,16),(0,16,16),(0,-16,16),(-24,0,12),(24,0,12),(0,24,12),(0,-24,12))]) if name=='waist' else [[0,0,0],[-12,0,0],[12,0,0],[0,-12,0],[0,12,0],[-24,0,0],[24,0,0],[0,-24,0],[0,24,0],[0,0,12],[0,0,-12]]
 positions.sort(key=np.linalg.norm);valid[name]=[];trials[name]=[];neighbors=('thigh_l','thigh_r') if name=='waist' else ('head','clavicle_l','clavicle_r');names=(name,*neighbors);pairs={frozenset((name,n)) for n in neighbors};poses=[{}]
 for aid,vs in limits.items():
  if aid.split('.')[0] in names:poses += [{aid:float(v)} for v in vs]
 for pos in positions:
  for c in orientation:
   op={name:{'offset_parent_mm':pos,'F':c['F'],'V':c['V']}};ss=[]
   for a in poses:
    p,m,st,f,_=build('quinn',a,op,only=names);hit=first_cross(p,m,pairs=pairs);ss.append({'angles':a,'mapping':f,'hit':hit})
    if f or hit:break
   ok=len(ss)==len(poses) and not(ss[-1]['mapping'] or ss[-1]['hit']);row={'position':pos,'orientation':c,'overrides':op,'passed':ok,'samples_checked':len(ss),'last':ss[-1]};trials[name].append(row)
   if ok:valid[name].append(row);print('INDIVIDUAL_CLEAR',name,pos,c['az'],c['el'],c['phase'],c['bias'],flush=True)
   if len(trials[name])%20==0:print('SEARCH',name,len(trials[name]),'valid',len(valid[name]),flush=True);save('trunk_compact_search_v2.json',{'status':'SEARCH_RUNNING','trials':trials,'individual_valid':valid})
  if len(valid[name])>=12:break
 print('INDIVIDUAL_DONE',name,len(trials[name]),len(valid[name]),flush=True)
 save('trunk_compact_search_v2.json',{'status':'SEARCH_RUNNING','trials':trials,'individual_valid':valid})
rr=[];poses=[{}, {'waist.pitch':35,'chest.pitch':25,'waist.yaw':30,'chest.yaw':20}]
for aid,vs in limits.items():
 if aid.split('.')[0] in ('waist','chest'):poses += [{aid:float(v)} for v in vs]
options=list(itertools.product(valid['waist'],valid['chest']));options.sort(key=lambda cc:sum(np.linalg.norm(c['position']) for c in cc))
for w,c in options:
 op={**w['overrides'],**c['overrides']};ss=[]
 for a in poses:
  p,m,st,f,_=build('quinn',a,op,only=('waist','chest'));hit=first_cross(p,m);ss.append({'angles':a,'mapping':f,'hit':hit})
  if f or hit:break
 ok=len(ss)==len(poses) and not(ss[-1]['mapping'] or ss[-1]['hit']);rr.append({'overrides':op,'pass_all_samples':ok,'samples':ss});print('PAIR',len(rr),'checked',len(ss),'pass',ok,flush=True)
 save('trunk_compact_search_v2.json',{'status':'PAIR_SEARCH_RUNNING','trials':trials,'individual_valid':valid,'pairs':rr})
 if ok:break
if any(sha(Path(k))!=v for k,v in inputs.items()):raise RuntimeError('inputs changed')
save('trunk_compact_search_v2.json',{'status':'SEARCH_COMPLETE','trials':trials,'individual_valid':valid,'pairs':rr,'input_sha256':inputs})
