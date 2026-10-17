"""Check whether the neck core can be installed after bare-chest clavicle preassembly."""
from o22f7_animation import *
from build_revo22_assembly import b
x=Build();st=x.g['steps'][2];x.begin(st);seq=read(OUT/'sequence.json');a=next(a for a in seq['actions'] if a['chapter']=='S03' and a['kind']=='transfer' and '近端半壳' in a['title']);movingkeys=[list(x.obs)[i] for i in a['moving']];cache={}
def rawsolid(k):
 o=x.obs[k];m=x.scene['meshes'][o['mesh']]
 if o['mesh'] not in cache:cache[o['mesh']]=b.b.from_tri_exact(x.verts[m['first']:m['first']+m['count'],:3].reshape(-1,3,3))
 return cache[o['mesh']]
moving=[b.g.move(rawsolid(k),x.mats[k]) for k in movingkeys];fixedkeys=['frame/chest','frame/clavicle_l.protract_frame','frame/clavicle_r.protract_frame']+[mod+'/'+s for mod in ['clavicle_l.protract','clavicle_r.protract'] for s in ['M3_nut','M3_reaction_washer','inner_M4_wide','outer_M4_wide','spring_1','spring_2','front_M4_washer','shoulder_D4_L8_M3_thread6']];rows=[]
for angle in [0,-20]:
 raw=dict(x.raw);raw['clavicle_l.protract/r0']=angle;ff,oo=kin.owners(raw);fixed=[]
 for k in fixedkeys:
  mm=x.meta['meta'][k];owner=ff[mm['body']] if mm['owner']=='rigid_frame' else oo[mm['module'],mm['owner']];fixed.append(b.g.move(rawsolid(k),owner@np.array(x.bind[x.idx[k]]['local']).reshape(4,4)))
 boxes=[np.array(s.bounding_box()) for s in fixed]
 for name,local in [('original',None),('above_y12',[[0,90,80],[0,12,80],[0,12,0],[0,0,0]]),('above_y25',[[0,90,80],[0,25,80],[0,25,0],[0,0,0]])]:
  path=np.array(a['path']) if local is None else np.array([x.direction(v) for v in local]);hit=None;count=0;peak=0
  for p,q in zip(path,path[1:]):
   for t in np.linspace(0,1,max(2,int(np.ceil(np.linalg.norm(q-p)))+1)):
    shift=p+(q-p)*t;count+=1
    for key,base in zip(movingkeys,moving):
     s=base.translate(shift);box=np.array(s.bounding_box())
     for k,f,bo in zip(fixedkeys,fixed,boxes):
      if np.any(np.minimum(box[3:],bo[3:])<=np.maximum(box[:3],bo[:3])+1e-6):continue
      vol=float((s^f).volume());peak=max(peak,vol)
      if vol>.02:hit={'part':key,'other':k,'shift':arr(shift),'overlap_mm3':vol};break
     if hit:break
    if hit:break
   if hit:break
  row={'parked_left_angle':angle,'path':name,'passed_sampled_check':hit is None,'samples':count,'maximum_overlap_mm3':peak,'hit':hit,'moving_part_count':len(movingkeys),'fixed_part_count':len(fixedkeys)};rows.append(row);put(WORK/'head_after_clavicles_review.json',{'checks':rows,'scope':'sampled core transfer only'});print(row,flush=True)
