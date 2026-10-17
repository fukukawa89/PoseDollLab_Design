import sys,json,numpy as np
from build_revo22_fins_v2 import *
for pid in sys.argv[1:]:
 n=dict(np.load(O/'parts'/f'{pid}.npz'));r=json.loads((O/'design'/f'{pid}.json').read_text());manifest=json.loads((O/'manifest.json').read_text());qitems=[]
 for plate in manifest['plates']:
  names={it['object_name'] for it in plate['items'] if it['id']==pid};qp=O/'verification'/f"{plate['id']}_extrusion_contacts.json"
  if names and qp.exists():qitems += [x for x in json.loads(qp.read_text())['teeth'] if x['object_name'] in names]
 q={'teeth':qitems} if qitems else json.loads((O/'verification'/f'QC_{pid}_extrusion_contacts.json').read_text())
 s=solid(n['v'],n['f']);b=solid(n['fin_v'],n['fin_f']);t=solid(n['teeth_v'],n['teeth_f']);vols=next((x['volumes'] for x in json.loads((D/'all_protected_volumes.json').read_text())['objects'] if x['part']==r['part']),[]);M=np.array(r['orientation']['matrix']);off=np.array(r['orientation']['source_translation_mm']);ban=protected(vols).transform(np.c_[M,off]);changed=[]
 for item in q['teeth']:
  if item['continuous_printed_stack']:continue
  ix=item['tooth']-1;tooth=r['teeth'][ix];bb=np.array(tooth['bounds_mm']);lo=bb[:3].copy();hi=bb[3:].copy();center=(lo+hi)/2
  for wx,wy in [(1.2,1.2),(1.2,.9),(.9,1.2),(1.0,1.0)]:
   a=lo.copy();c=hi.copy();a[:2]=center[:2]-np.array([wx,wy])/2;c[:2]=center[:2]+np.array([wx,wy])/2;probe=box(a,c);bite=(probe^s).volume();root=(probe^b).volume()
   if bite<.02 or bite>.8 or root<.06 or (probe^ban).volume()>1e-7:continue
   tt=t+probe
   if str(tt.status())!='Error.NoError':continue
   t=tt;tooth.update(bounds_mm=np.r_[a,c].tolist(),part_bite_mm3=float(bite),fin_root_mm3=float(root),neck_xy_mm=[wx,wy],widened_after_extrusion_audit=True);changed.append(ix+1);break
 n.update(teeth_v=vf(t)[0],teeth_f=vf(t)[1]);np.savez_compressed(O/'parts'/f'{pid}.npz',**n);r.update(teeth_part_overlap_mm3=float((t^s).volume()),support_volume_mm3=float((b+t).volume()));(O/'design'/f'{pid}.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print('WIDEN',pid,changed,flush=True)