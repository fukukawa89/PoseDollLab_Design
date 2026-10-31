"""Inspect candidate motions against the already installed model, without editing it."""
from o22f7_animation import *
from build_revo22_assembly import b
x=Build();st=x.g['steps'][3];x.begin(st);seq=read(OUT/'sequence.json');key='frame/'+st['child'];index=next(n for n,a in enumerate(seq['actions']) if x.idx[key] in a['new']);seen=set(i for a in seq['actions'][:index] for i in a['new']);cache={}
def shape(k):
 o=x.obs[k];m=x.scene['meshes'][o['mesh']]
 if o['mesh'] not in cache:cache[o['mesh']]=b.b.from_tri_exact(x.verts[m['first']:m['first']+m['count'],:3].reshape(-1,3,3))
 return b.g.move(cache[o['mesh']],x.mats[k])
fixed={list(x.obs)[i]:shape(list(x.obs)[i]) for i in seen};bounds={k:np.array(v.bounding_box()) for k,v in fixed.items()};moving=shape(key);inverse=np.linalg.inv(x.mount)
for name in ['S04_rigid_refined_progress.json','clavicle_goal_1_-1.json','clavicle_goal_2_1.json']:
 d=read(WORK/name);path=d['best_path'];rows=[]
 for pi in sorted(set([0,len(path)-1,*range(0,len(path),max(1,len(path)//14))])):
  q=path[pi];M=np.eye(4);M[:3,:3]=b.b.rot(0,q[3])@b.b.rot(1,q[4])@b.b.rot(2,q[5]);M[:3,3]=q[:3];s=b.g.move(moving,x.mount@M@inverse);bb=np.array(s.bounding_box());hits=[]
  for k,f in fixed.items():
   if np.any(np.minimum(bb[3:],bounds[k][3:])<=np.maximum(bb[:3],bounds[k][:3])+1e-6):continue
   v=float((s^f).volume())
   if v>.02:hits.append({'part':k,'overlap_mm3':v})
  if hits:rows.append({'path_index':pi,'hits':hits})
 print(json.dumps({'path':name,'sampled':16,'obstacles':len(fixed),'conflicts':rows},ensure_ascii=False),flush=True)
 put(WORK/(name.replace('.json','_installed_context.json')),{'partial_path_inspection':True,'conflicts':rows,'obstacles':len(fixed)})
