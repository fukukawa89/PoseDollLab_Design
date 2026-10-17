import json,numpy as np
from explore_revo22_f3 import *
from pack_revo22_a1mini import read_mesh
pid='X046';it=next(i for p in json.loads((B/'a1mini/manifest.json').read_text())['plates'] for i in p['items'] if i['id']==pid)
vols=next(x['volumes'] for x in json.loads((B/'a1mini_supports/design/all_protected_volumes.json').read_text())['objects'] if x['part']==it['part'])
old=json.loads((OLD/'design/X046.json').read_text());base=dict(np.load(OLD/'parts/X046.npz'));v,f=read_mesh(B/it['source_3mf'])
tri=v[f];normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-20)
# Explicit underside of the controller box, excluding all joint and fitting geometry.
faces=np.where((abs(tri[:,:,0]-31).max(axis=1)<.001)&(normal[:,0]<-.99))[0]
dest=O/'candidates/X046/distributed_box'
for folder in ['parts','design','verification']:(dest/folder).mkdir(parents=True,exist_ok=True)
builder.O=dest;builder.choose=lambda _:old['orientation'];builder.AXIS=90;builder.FACE_FILTER=faces;builder.PITCH_OVERRIDE=8.;builder.THICKNESS_OVERRIDE=1.6
new=builder.make(pid,it,vols);n=dict(np.load(dest/'parts/X046.npz'))
assert np.max(abs(n['v']-base['v']))<1e-9
b=union([solid(base['fin_v'],base['fin_f']),solid(n['fin_v'],n['fin_f'])]);t=union([solid(base['teeth_v'],base['teeth_f']),solid(n['teeth_v'],n['teeth_f'])]);s=solid(n['v'],n['f'])
n.update(fin_v=vf(b)[0],fin_f=vf(b)[1],teeth_v=vf(t)[0],teeth_f=vf(t)[1]);np.savez_compressed(dest/'parts/X046.npz',**n)
extra=len(new['segments']);num=len(old['segments'])
for q in new['segments']:q['number']+=num;q['purpose']='distributed_controller_box_support'
for q in new['teeth']:q['fin_number']+=num
old['segments']+=new['segments'];old['teeth']+=new['teeth'];old.update(support_count=len(old['segments']),support_volume_mm3=float((b+t).volume()),distributed_box_panels=extra,body_part_overlap_mm3=float((b^s).volume()),teeth_part_overlap_mm3=float((t^s).volume()))
assert (b^s).volume()<1e-6
(dest/'design/X046.json').write_text(json.dumps(old,ensure_ascii=False,indent=2),encoding='utf8')
print('ADDED_BOX_PANELS',extra,'added_teeth',len(new['teeth']),'support_cm3',(b+t).volume()/1000,flush=True)
audit(pid,dest)
