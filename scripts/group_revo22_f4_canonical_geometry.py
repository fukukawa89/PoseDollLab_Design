from pathlib import Path
import numpy as np,json,itertools,time
import sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid
B=R/'Hardware/PoseDoll44/bench/revO22';O=B/'a1mini_fins_v4';F=B/'O22F3_Release/reference/parts';beds={x['id']:x['bed'] for x in json.loads((B/'print_batch/manifest.json').read_text())['rows']};items=[]
for p in sorted(F.glob('*.npz')):
 n=np.load(p);bed=beds[p.stem];Br=np.array(bed['rotation']);Bt=np.array(bed['translation_mm']);v=(n['source_v']-Bt)@Br;s=solid(v,n['f']);bb=np.r_[v.min(0),v.max(0)];items.append({'id':p.stem,'v':v,'f':n['f'],'solid':s,'bounds':bb,'size':bb[3:]-bb[:3],'volume':float(s.volume()),'Br':Br,'Bt':Bt})
groups=[];left=items
while left:
 ref=left[0];remaining=[];members=[{'id':ref['id'],'Q':np.eye(3).tolist(),'shift':[0,0,0],'symmetric_difference_mm3':0}]
 for cand in left[1:]:
  if not np.allclose(np.sort(ref['size']),np.sort(cand['size']),atol=.002,rtol=0) or abs(cand['volume']-ref['volume'])>max(.03,ref['volume']*.00001):remaining.append(cand);continue
  match=None
  for perm in itertools.permutations(range(3)):
   if not np.allclose(ref['size'],cand['size'][list(perm)],atol=.002,rtol=0):continue
   for signs in itertools.product([-1,1],repeat=3):
    Q=np.eye(3)[list(perm)]*np.array(signs)[:,None];center=(ref['bounds'][:3]+ref['bounds'][3:])/2;cc=(cand['bounds'][:3]+cand['bounds'][3:])/2;shift=center-Q@cc;mv=cand['v']@Q.T+shift;ff=cand['f'] if np.linalg.det(Q)>0 else cand['f'][:,::-1].copy();other=solid(mv,ff);diff=float(((other-ref['solid'])+(ref['solid']-other)).volume())
    if abs(diff)<max(.01,ref['volume']*1e-6):
     Qs=ref['Br']@Q@cand['Br'].T;ts=ref['Bt']+ref['Br']@shift-Qs@cand['Bt'];match={'id':cand['id'],'Q':Qs.tolist(),'shift':ts.tolist(),'symmetric_difference_mm3':diff,'determinant':float(np.linalg.det(Qs))};break
   if match:break
  if match:members.append(match)
  else:remaining.append(cand)
 left=remaining;groups.append({'reference':ref['id'],'members':members})
 if len(members)>1:print('CANONICAL_GROUP',ref['id'],[q['id'] for q in members],flush=True)
 (O/'source_canonical_groups.json').write_text(json.dumps(groups,indent=2))
print('CANONICAL_GROUPS_DONE',len(groups),'types',sum(len(q['members']) for q in groups),flush=True)
