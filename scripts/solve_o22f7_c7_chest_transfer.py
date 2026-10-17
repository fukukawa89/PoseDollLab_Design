"""Find a short, translational chest-core route in its exported sequence context."""
from pathlib import Path
src=Path('scripts/check_o22f7_c7_sequence_paths.py').read_text('utf-8-sig');exec(src.split('chapter=None')[0])
chapter=None
for act in seq['actions']:
 if chapter!=act['chapter']:chapter=act['chapter'];x.begin(next(s for s in x.g['steps'] if s['step']==chapter))
 if act.get('raw_overrides'):x.set_raw(act['raw_overrides'])
 seen.update(act['new'])
 if chapter=='S02' and act['title']=='把核心放进近端半壳':break
 for i in act['moving']:delta[i]=pose(act,act.get('pose_path',act['path'])[-1])
moving=act['moving'];fi=[i for i in seen if i not in moving];fixed=[b.g.move(mesh(i),delta.get(i,np.eye(4))@x.mats[obs[i]]) for i in fi];fb=np.array([s.bounding_box() for s in fixed]);base=[b.g.move(mesh(i),x.mats[obs[i]]) for i in moving];mb=np.array([s.bounding_box() for s in base]);cachep={};last=None;queries=0

def point(q):
 global last,queries
 key=tuple(np.round(q,7))
 if key in cachep:return cachep[key]
 queries+=1
 for j,box in enumerate(mb):
  bb=box+np.r_[q,q];ii=np.where(np.all(np.minimum(bb[3:],fb[:,3:])>np.maximum(bb[:3],fb[:,:3])+1e-6,axis=1))[0]
  if len(ii):
   s=base[j].translate(q)
   for k in ii:
    v=float((s^fixed[k]).volume())
    if v>.02:last={'moving':obs[moving[j]],'fixed':obs[fi[k]],'q':q.tolist(),'mm3':v};cachep[key]=False;return False
 cachep[key]=True;return True

def clear(path,step=1.5):
 for aa,bb in zip(path,path[1:]):
  aa=np.array(aa);bb=np.array(bb)
  for t in np.linspace(0,1,max(2,math.ceil(np.linalg.norm(bb-aa)/step)+1)):
   if not point(aa+(bb-aa)*t):return False
 return True
start=np.array(act['path'][0]);axis=start/np.linalg.norm(start);directions=[x.direction(q) for q in [[1,0,0],[-1,0,0],[0,0,1],[0,0,-1],[1,0,1],[-1,0,1],[1,0,-1],[-1,0,-1]]];print('ENDPOINTS',point(np.zeros(3)),point(start),last,flush=True);found=None
for dist in [4,8,12,18,25,35,50,65]:
 a0=axis*dist
 if not clear([np.zeros(3),a0]):continue
 for d in directions:
  d=d/np.linalg.norm(d)
  for h in [12,24,40,65,100,150]:
   path=[np.zeros(3),a0,a0+d*h,start+d*h,start]
   if clear(path):found=path;break
  if found:break
 if found:break
 print('TRIED',dist,'queries',queries,'last',last,flush=True)
if found:
 assert clear(found,.25),last;put(C/'C7_chest_core_transfer_path.json',{'sequence_source_sha256':sha(a.OUT/'sequence.json'),'escape_path':[q.tolist() for q in found],'entry_path':[q.tolist() for q in reversed(found)],'sampling_mm':.25,'overlap_tolerance_mm3':.02,'passed':True,'queries':queries});print('FOUND',[q.tolist() for q in found],queries,flush=True)
else:put(C/'C7_chest_core_transfer_search.json',{'found':False,'queries':queries,'last':last});print('NOT_FOUND',queries,last,flush=True)
