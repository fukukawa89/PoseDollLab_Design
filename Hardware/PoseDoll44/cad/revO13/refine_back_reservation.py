"""Select a lower empty rear-PCB reservation, preserving dimensions and poses."""
from back_reservation import *
def main():
 lib=library();bb={k:bounds(s) for k,s in lib.items()};world=[]
 for char in ('manny','quinn'):
  p=merged_profile(char)
  for st in json.loads((OUT/f'clavicle_trial/{char}_states.json').read_text())['states']:
   T,_=fk(p,st['requested_angles_deg']);obs=[]
   for o in st['objects']:
    F=np.array(o['frame']);v=bb[o['library']]@F[:3,:3].T+F[:3,3]
    obs.append((o,pose(lib[o['library']],F[:3,:3],F[:3,3]),v.min(0),v.max(0)))
   world.append((char,st['pose'],T['chest'],obs))
 results=[]
 for dz in (-8,-12,-16):
  # An axis-aligned 0.5 mm expansion contains the Euclidean 0.5 mm offset.
  low=np.array([-40,-24,dz],float);high=np.array([-28,24,48+dz],float)
  s=md.Manifold.cube(high-low+1).translate(low-.5);corners=bounds(s);rows=[]
  for char,name,F,obs in world:
   target=pose(Parts([s]),F[:3,:3],F[:3,3]);p=corners@F[:3,:3].T+F[:3,3];lo,hi=p.min(0),p.max(0);hits=[]
   for o,t,al,ah in obs:
    if np.any(np.minimum(hi,ah)<=np.maximum(lo,al)):continue
    if (v:=(target^t).volume())>1e-4:hits.append({'part':o['id'],'volume_mm3':v})
   rows.append({'character':char,'pose':name,'findings':hits})
  results.append({'shift_down_mm':-dz,'local_low_mm':low.tolist(),'local_high_mm':high.tolist(),'expanded_by_mm':.5,'failed_endpoints':sum(bool(r['findings']) for r in rows),'cases':rows})
 clear=[r for r in results if not r['failed_endpoints']]
 save('back_reservation_candidates.json',{'complete':True,'candidates':results,'selected':clear[0] if clear else None,
 'scope':'48x48x12 mm EMPTY target plus 0.5 mm box expansion, 102 endpoints against existing arm modules. No actual PCB, body/neck mechanism, carrier, wires, magnetic/RF or continuous-path qualification.'})
 print('backbox candidates',[(r['shift_down_mm'],r['failed_endpoints']) for r in results],flush=True)
if __name__=='__main__':main()
