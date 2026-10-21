"""Add positively fixed backpack parts to the preserved fine-path carrier design."""
from common import *
from connected import carrier_inputs,build_connected
from layout_fullbody import build,fk
from carriers_swept import ASSEMBLY_POSE

VARIANT='carriers_equipped'

def generate(char):
 rr,frames,_=carrier_inputs(char,'carriers_refined');search=read(OUT/f'equipment/{char}_search.json');assert search['status']=='ENVELOPES_ROUTED'
 _,_,_,f,pr=build(char,ASSEMBLY_POSE,geometry=False);assert not f;T,_=fk(pr,ASSEMBLY_POSE);extra={};meta={};notes=[];inputs={}
 for entry in search['entries']:
  body=entry['body'];kind=entry['kind'];report=read(OUT/f'equipment/{kind}_local.json')
  if report['findings']:raise ValueError(('Equipment collision',kind))
  raw=np.load(OUT/f'equipment/{kind}_local.npz');I=np.linalg.inv(T[body]);c=np.array(entry['front_center_world_mm']);F=np.c_[[0,1,0],[0,0,-1],[-1,0,0]];o=c-F@np.array([35,30,0]) if kind=='controller' else c
  links=md.Manifold()
  for path in entry['mount_paths_world_mm']:
   for a,b in zip(path,path[1:]):links+=beam(a,b,4)+md.Manifold.sphere(4,24).translate(a)+md.Manifold.sphere(4,24).translate(b)
  # Mounts stop at the inner face of the enclosure backplate, never in the battery cavity.
  links=links^box([-c[0]*0+c[0]-2,-10000,-10000],[10000,10000,10000])
  rec=next(r for r in rr['frames'] if r['body']==body);fused=pose(frames[body],T[body][:3,:3],T[body][:3,3])+links;mods=sorted(set(v.split('/')[0] for v in rec['replaces']))
  for k,tt in raw.items():
   s=pose(from_tri_exact(tt),F,o)
   if k=='base':fused+=s;continue
   pid=f'accessory/{body}/{kind}_{k}';extra[pid]=pose(s,I[:3,:3],I[:3,3]);meta[pid]={'body':body,'module':'frame/'+body,'modules':mods,'owner':'rigid_frame','sku':report['stock_skus'][k]}
  if solid_count(fused)!=1:raise ValueError(('Disconnected backpack',body))
  frames[body]=pose(fused,I[:3,:3],I[:3,3]);rec['mesh']=mesh_record(fused);rec['equipment']={'kind':kind,'front_center_world_mm':c.tolist(),'mount_paths_world_mm':entry['mount_paths_world_mm'],'local_notes':report['notes']};notes.append(rec['equipment'])
  for p in [OUT/f'equipment/{kind}_local.npz',OUT/f'equipment/{kind}_local.json']:inputs[str(p)]=sha(p)
 folder=OUT/VARIANT;folder.mkdir(exist_ok=True);dest=folder/(char+'_parts.npz');np.savez_compressed(dest,**{k:tri(s) for k,s in frames.items()});np.savez_compressed(folder/(char+'_accessories.npz'),**{k:tri(s) for k,s in extra.items()})
 for p in [Path(__file__),Path(__file__).with_name('equipment_parts.py'),OUT/f'equipment/{char}_search.json',OUT/f'carriers_refined/{char}_parts.npz',OUT/f'carriers_refined/{char}_routing.json']:inputs[str(p)]=sha(p)
 rr['input_sha256'].update(inputs);rr.update(status='ROUTING_GENERATED',mesh_sha256=sha(dest));save(f'{VARIANT}/{char}_routing.json',rr);save(f'{VARIANT}/{char}_accessories.json',{'parts':meta,'sha256':sha(folder/(char+'_accessories.npz')),'input_sha256':inputs,'notes':notes});print('EQUIPPED',char,len(extra),flush=True)

def build_full(char,angles=ASSEMBLY_POSE):
 p,m,st,f,pr,prov=build_connected(char,angles,VARIANT);_,meta,_,_,_=build(char,angles,geometry=False);T,_=fk(pr,angles)
 for k in p:m[k]['transform']=T[k.split('/',1)[1]] if k.startswith('frame/') else meta[k]['transform']
 report=read(OUT/f'{VARIANT}/{char}_accessories.json');path=OUT/f'{VARIANT}/{char}_accessories.npz';assert sha(path)==report['sha256']
 for dep,h in report['input_sha256'].items():
  if sha(dep)!=h:raise RuntimeError('Equipment evidence stale '+dep)
 with np.load(path) as z:
  for k,tt in z.items():
   m[k]={**report['parts'][k],'transform':T[report['parts'][k]['body']]};M=m[k]['transform'];p[k]=pose(from_tri_exact(tt),M[:3,:3],M[:3,3])
 return p,m,st,f,pr,prov

if __name__=='__main__':
 for char in sys.argv[1:] or ['quinn','manny']:generate(char)
