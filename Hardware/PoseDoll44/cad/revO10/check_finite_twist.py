"""Check all body pairs of the assembled finite twist candidate without mesh decimation."""
from module_frames import *
from rigid_collision import Body,Pair
import itertools,hashlib,argparse,time

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--quick',action='store_true');args=ap.parse_args()
 data=json.loads((G9/'bounded_mapping.json').read_text());rows=[];start=time.time()
 for c in data['characters'][:1] if args.quick else data['characters']:
  key=c['character']+'_'+c['side'];m=meshes(key);bodies={k:Body(t) for k,t in m.items()};pairs={(x,y):Pair(bodies[x],bodies[y]) for x,y in itertools.combinations(m,2)}
  targets=[(p['pose'],p['angles_deg'][-1],p['zero_offsets_deg']) for p in c['paths']]
  if args.quick:targets=targets[:1]+[(f'probe_{a}_{b}',[0,a,b,0],c['paths'][0]['zero_offsets_deg']) for a,b in [(0,0),(25,96.2),(-25,-96.2),(0,98)]]
  for name,q,zero in targets:
   M=matrices(q,zero);hits=[]
   for (x,y),pair in pairs.items():
    r=pair.check(M[x],M[y],tol=.005)
    if not r['status'].startswith('CLEAR'):hits.append({'pair':[x,y],**r})
   rows.append({'group':key,'pose':name,'angles_deg':q,'findings':hits});print(key,name,hits if args.quick else [(h['pair'],h['status']) for h in hits],flush=True)
  name='quick_grid' if args.quick else 'target_grid'
  (OUT/'finite_twist'/f'{name}.json').write_text(json.dumps({'cases':rows,'elapsed_s':time.time()-start,'scope':'All five rigid-body groups; stationary seated contacts inside each group do not count as motion pairs. Nominal discrete endpoint checks only.','physical_tested':False,'manufacturing_released':False},indent=2)+'\n')
if __name__=='__main__':main()
