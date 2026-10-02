"""Test new shoulder modules against retained real LP6/M4 and the opposite arm.
Old module-to-module failures remain inherited; this never declares body PASS.
"""
from module_frames import *
from rigid_collision import Body,Pair
import itertools,argparse,time

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--quick',action='store_true');args=ap.parse_args();data=json.loads((OUT/'shoulder_assembly/states.json').read_text());lib={}
 for fam in ('LP6','M4'):
  for owner in ('parent','child'):
   raw=np.load(OUT/'old_modules'/f'{fam}_{owner}.npz');lib[fam+'_'+owner]=Body(np.concatenate(list(raw.values())))
 for char,side in itertools.product(('manny','quinn'),('l','r')):
  for k,t in meshes(char+'_'+side).items():lib[char+'_'+side+'/'+k]=Body(t)
 pairs={};rows=[];start=time.time();states=data['states'][:1] if args.quick else data['states']
 for state in states:
  findings=[];checks=0
  for a,b in itertools.combinations(state['objects'],2):
   if a['module']==b['module']:continue
   if not (a['module'].startswith('TUT') or b['module'].startswith('TUT')):continue
   ka,kb=a['library'],b['library'];Fa,Fb=np.array(a['frame']),np.array(b['frame']);alo,ahi=lib[ka].bound(Fa[:3,:3],Fa[:3,3]);blo,bhi=lib[kb].bound(Fb[:3,:3],Fb[:3,3])
   if np.any(np.minimum(ahi,bhi)<np.maximum(alo,blo)):continue
   key=ka,kb
   if key not in pairs:pairs[key]=Pair(lib[ka],lib[kb])
   r=pairs[key].check(Fa[:3,:3],Fb[:3,:3],tol=.06,ta=Fa[:3,3],tb=Fb[:3,3]);checks+=1
   if not r['status'].startswith('CLEAR'):findings.append({'a':a['id'],'b':b['id'],**r})
  rows.append({'character':state['character'],'pose':state['pose'],'findings':findings,'narrowphase_checks':checks});print(state['character'],state['pose'],len(findings),[(r['a'],r['b']) for r in findings],flush=True)
  fn='quick_collisions.json' if args.quick else 'collisions.json'
  (OUT/'shoulder_assembly'/fn).write_text(json.dumps({'cases':rows,'elapsed_s':time.time()-start,'penetration_witness_threshold_mm':.06,'scope':'New shoulder to all retained modules, plus left/right new shoulder. Inherited old module collisions, carriers, trunk/neck, shell, wiring not cleared.','manufacturing_released':False},indent=2)+'\n')
if __name__=='__main__':main()
