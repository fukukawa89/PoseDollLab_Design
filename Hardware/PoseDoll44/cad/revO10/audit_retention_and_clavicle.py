"""Independent nominal assembled-part and old-clavicle volume audit."""
from solid_ops import *
import itertools,time

def main():
 source=OUT/'face_brake/parts.npz';raw={k:from_tri(t) for k,t in dict(np.load(source)).items()}
 for k,t in np.load(G8/'fastened_core/fasteners.npz').items():raw['ring_'+k]=from_tri(t)
 rows=[]
 for a,b in itertools.combinations(raw,2):
  if a in ('C01','C02') or b in ('C01','C02'):continue
  v=(raw[a]^raw[b]).volume()
  if v>1e-6:rows.append({'pair':[a,b],'volume_mm3':v})
 save('face_brake/fixed_part_audit.json',{'input_sha256':sha(source),'findings':rows,'checked_pairs':sum(a not in ('C01','C02') and b not in ('C01','C02') for a,b in itertools.combinations(raw,2)),'scope':'Unmerged stationary members; positive volume is reported even if a pair has an intended contact. Numerical reference threads only.','manufacturing_released':False})
 print('fixed',rows,flush=True)
 data=json.loads((OUT/'shoulder_assembly/states.json').read_text());state=data['states'][0];objects={x['id']:x for x in state['objects']};old={};result=[]
 for side in ('l','r'):
  key='manny_'+side;p=np.load(OUT/'braked_module'/f'{key}.npz');new=md.Manifold()
  for name,t in p.items():
   if name.startswith('P_'):new+=from_tri(t)
  F=np.array(objects[f'TUT_{side}/P']['frame']);nw=pose(new,F[:3,:3],F[:3,3])
  for axis,owner in [('protract','parent'),('protract','child'),('elevate','child')]:
   ob=objects[f'clavicle_{side}.{axis}/{owner}'];lib=ob['library']
   if lib not in old:
    s=md.Manifold()
    for name,t in np.load(OUT/'old_modules'/f'{lib}.npz').items():s+=from_tri(t)
    old[lib]=s
   M=np.array(ob['frame']);ov=nw^pose(old[lib],M[:3,:3],M[:3,3]);result.append({'pair':[f'TUT_{side}/P',ob['id']],'volume_mm3':ov.volume(),'bounds_mm':list(ov.bounding_box())});print(result[-1],flush=True)
 save('shoulder_assembly/neutral_csg_audit.json',{'scope':'Independent CSG of six earlier reported overlaps using the complete new braked proximal housing and actual retained old module parts at neutral. Not a full body check.','cases':result,'manufacturing_released':False})
if __name__=='__main__':main()
