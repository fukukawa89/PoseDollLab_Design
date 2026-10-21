"""Verify the proposed preassembly order at its remaining shared interfaces."""
from o22f7_animation import *
from build_revo22_assembly import b
x=Build();seq=read(OUT/'sequence.json');cache={};rows=[]
stock=['M3_nut','M3_reaction_washer','inner_M4_wide','outer_M4_wide','spring_1','spring_2','front_M4_washer','shoulder_D4_L8_M3_thread6'];pre=['frame/clavicle_l.protract_frame','frame/clavicle_r.protract_frame']+[mod+'/'+s for mod in ['clavicle_l.protract','clavicle_r.protract'] for s in stock]
def mesh(k):
 o=x.obs[k];m=x.scene['meshes'][o['mesh']]
 if o['mesh'] not in cache:cache[o['mesh']]=b.b.from_tri_exact(x.verts[m['first']:m['first']+m['count'],:3].reshape(-1,3,3))
 return cache[o['mesh']]
def shape(k):return b.g.move(mesh(k),x.mats[k])
def test(name,keys,fixed,path):
 moving={k:shape(k) for k in keys};bb={k:np.array(s.bounding_box()) for k,s in fixed.items()};samples=0;peak=0;hit=None
 for p,q in zip(path,path[1:]):
  p,q=np.array(p),np.array(q)
  for t in np.linspace(0,1,max(2,int(np.ceil(np.linalg.norm(q-p)/.5))+1)):
   off=p+(q-p)*t;samples+=1
   for k,s in moving.items():
    a=s.translate(off);bo=np.array(a.bounding_box())
    for other,f in fixed.items():
     if np.any(np.minimum(bo[3:],bb[other][3:])<=np.maximum(bo[:3],bb[other][:3])+1e-6):continue
     v=float((a^f).volume());peak=max(peak,v)
     if v>.02:hit={'moving':k,'obstacle':other,'volume_mm3':v,'offset':arr(off)};break
    if hit:break
   if hit:break
  if hit:break
 row={'check':name,'passed':hit is None,'samples':samples,'moving_parts':len(keys),'fixed_parts':len(fixed),'peak_mm3':peak,'hit':hit};rows.append(row);put(WORK/'clavicle_preassembly_interfaces_review.json',{'checks':rows});print(row,flush=True)
x.begin(x.g['steps'][1]);chapter=[a for a in seq['actions'] if a['chapter']=='S02'];introduce=next(i for i,a in enumerate(chapter) if x.idx['frame/chest'] in a['new']);seen=set();offset={}
for a in seq['actions']:
 if a['id']==chapter[introduce]['id']:break
 seen.update(a['new'])
 for i in a['moving']:offset[i]=np.array(a['path'][-1])
fixed={list(x.obs)[i]:shape(list(x.obs)[i]).translate(offset.get(i,np.zeros(3))) for i in seen};test('preassembled_chest_into_core',['frame/chest',*pre],fixed,chapter[introduce]['path'])
a=next(a for a in chapter if a['kind']=='transfer' and '近端半壳' in a['title']);movingkeys=[list(x.obs)[i] for i in a['moving']]+pre;seen=set();offset={}
for prev in seq['actions']:
 if prev['id']==a['id']:break
 seen.update(prev['new'])
 for i in prev['moving']:offset[i]=np.array(prev['path'][-1])
fixed={list(x.obs)[i]:shape(list(x.obs)[i]).translate(offset.get(i,np.zeros(3))) for i in seen if list(x.obs)[i] not in movingkeys};test('chest_and_clavicles_into_waist',movingkeys,fixed,a['path'])
x.begin(x.g['steps'][3]);rightkeys=['frame/chest','frame/clavicle_r.protract_frame']+['clavicle_r.protract/'+s for s in stock];fixed={k:shape(k) for k in rightkeys};bb={k:np.array(s.bounding_box()) for k,s in fixed.items()};hit=None;peak=0;count=0;k='frame/clavicle_l.protract_frame'
for angle in np.linspace(-20,0,81):
 raw=dict(x.raw);raw['clavicle_l.protract/r0']=angle;ff,oo=kin.owners(raw);l=b.g.move(mesh(k),ff['clavicle_l.protract_frame']@np.array(x.bind[x.idx[k]]['local']).reshape(4,4));bo=np.array(l.bounding_box());count+=1
 for other,f in fixed.items():
  if np.any(np.minimum(bo[3:],bb[other][3:])<=np.maximum(bo[:3],bb[other][:3])+1e-6):continue
  v=float((l^f).volume());peak=max(peak,v)
  if v>.02:hit={'angle':float(angle),'obstacle':other,'volume_mm3':v};break
 if hit:break
row={'check':'park_and_return_left_with_right_installed','passed':hit is None,'samples':count,'peak_mm3':peak,'hit':hit};rows.append(row);put(WORK/'clavicle_preassembly_interfaces_review.json',{'checks':rows});print(row,flush=True)
