import json,numpy as np
from search_revo22_f5_orientation268 import O,OLD
from build_revo22_fins import solid,box,md,vf
from verify_revo22_f5_contacts298 import envelope
from scipy.spatial.transform import Rotation
old=json.loads((OLD/'manifest.json').read_text());counts={}
for p in old['plates']:
 if not p['optional']:
  for i in p['items']:counts[i['id']]=counts.get(i['id'],0)+1
vo=vn=to=tn=0;modified=[]
for f in (O/'selections').glob('*.json'):
 p=f.stem;sel=json.loads(f.read_text());a=O/'candidates'/p/sel['label'];d=json.loads((a/'design'/f'{p}.json').read_text());g=json.loads((a/'verification/f5_geometry.json').read_text());od=json.loads((OLD/'design'/f'{p}.json').read_text());c=counts.get(p,0);vo+=g['old_support_volume_mm3']*c;vn+=g['support_volume_mm3']*c;to+=len(od.get('teeth',[]))*c;tn+=d.get('new_tooth_count',d.get('tooth_count',len(d.get('teeth',[]))))*c
 if g['body_change_fit_and_pose_required']:modified.append(p)
print('INTERIM149_STATS',100*(1-vn/vo),to,tn,len(modified),modified,flush=True)
s=box([0,0,0],[1,1,1]);q=Rotation.from_euler('xyz',[22,-17,39],degrees=True).as_matrix();off=np.array([[x,y,z]for x in[-.05,.05]for y in[-.05,.05]for z in[-.05,.05]])@q.T;true=md.Manifold.hull_points((vf(s)[0][:,None]+off[None]).reshape(-1,3))
for j,r in enumerate([box([.99,.3,.3],[1.04,.6,.6]),box([1.12,.3,.3],[1.2,.6,.6]),box([.999,.49,.49],[1.05,.51,.51]),box([-.1,-.1,-.1],[1.1,1.1,1.1])]):
 want=(r^true).volume();got=envelope(s,r,axes=q).volume();assert abs(got-want)<1e-8,(j,got,want);print('CONTACT_CONTROL436',j,got,want,flush=True)
