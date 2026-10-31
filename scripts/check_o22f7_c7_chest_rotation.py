"""Check the in-hand chest rotation before the waist insertion."""
from pathlib import Path
src=Path('scripts/check_o22f7_c7_sequence_paths.py').read_text('utf-8-sig');exec(src.split('chapter=None')[0])
chapter=None
for act in seq['actions']:
 if chapter!=act['chapter']:chapter=act['chapter'];x.begin(next(s for s in x.g['steps'] if s['step']==chapter))
 if act.get('raw_overrides'):x.set_raw(act['raw_overrides'])
 seen.update(act['new'])
 if act.get('raw_transition'):break
 for i in act['moving']:delta[i]=pose(act,act.get('pose_path',act['path'])[-1])
rawkey,(lo,hi)=next(iter(act['raw_transition'].items()));before={k:v.copy() for k,v in x.mats.items()};x.set_raw({rawkey:hi});moving=[i for i in seen if abs(x.mats[obs[i]]-before[obs[i]]).max()>1e-7];fixedids=list(seen-set(moving));fixed=[b.g.move(mesh(i),delta.get(i,np.eye(4))@x.mats[obs[i]]) for i in fixedids];fb=np.array([s.bounding_box() for s in fixed]);hit=None;peak=0;samples=0
for q in np.linspace(lo,hi,math.ceil(abs(hi-lo)/.5)+1):
 x.set_raw({rawkey:float(q)});samples+=1
 for i in moving:
  shape=b.g.move(mesh(i),delta.get(i,np.eye(4))@x.mats[obs[i]]);bb=np.array(shape.bounding_box());ii=np.where(np.all(np.minimum(bb[3:],fb[:,3:])>np.maximum(bb[:3],fb[:,:3])+1e-6,axis=1))[0]
  for j in ii:
   vol=float((shape^fixed[j]).volume());peak=max(peak,vol)
   if vol>.02:hit={'q':float(q),'moving':obs[i],'fixed':obs[fixedids[j]],'mm3':vol};break
  if hit:break
 if hit:break
rep={'sequence_sha256':sha(a.OUT/'sequence.json'),'passed':hit is None,'angular_sampling_deg':.5,'overlap_tolerance_mm3':.02,'samples':samples,'moving_parts':len(moving),'maximum_overlap_mm3':peak,'hit':hit};put(C/'C7_chest_rotation_review.json',rep);print(rep,flush=True)
