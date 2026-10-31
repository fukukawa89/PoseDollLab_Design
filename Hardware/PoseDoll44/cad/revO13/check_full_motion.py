"""Original angle-linear paths with actual four-angle allocations at <=2 deg input steps.
This includes ALL unlike rigid-body module pairs, exposing any retained old
forearm/wrist issues rather than reusing the narrower shoulder-only predicate.
"""
from clavicle_trial import *
from parts_library import Parts
PAIR_CACHE={}
def check(state,lib,bb,all_pairs=False):
 world={};boxes={};hits=[]
 for o in state['objects']:
  F=np.array(o['frame']);p=bb[o['library']]@F[:3,:3].T+F[:3,3];boxes[o['id']]=(p.min(0),p.max(0));world[o['id']]=pose(lib[o['library']],F[:3,:3],F[:3,3])
 for a,b in itertools.combinations(state['objects'],2):
  if a['body']==b['body']:continue
  if not all_pairs and not relevant(a,b):continue
  al,ah=boxes[a['id']];bl,bh=boxes[b['id']]
  if np.any(np.minimum(ah,bh)<=np.maximum(al,bl)+1e-8):continue
  Fa=np.array(a['frame']);Fb=np.array(b['frame']);relative=np.linalg.inv(Fa)@Fb
  key=(a['library'],b['library'],tuple(np.round(relative.flatten(),8)))
  if key not in PAIR_CACHE:PAIR_CACHE[key]=(world[a['id']]^world[b['id']]).volume()
  v=PAIR_CACHE[key]
  if v>1e-4:hits.append({'pair':[a['id'],b['id']],'sum_piece_overlap_mm3':v})
 return hits
def main():
 lib=library();bb={k:bounds(s) for k,s in lib.items()}
 report=json.loads((OUT/'clavicle_trial/motion.json').read_text());c=report['candidate'];x,y,z=c['x_mm'],c['lateral_mm'],c['z_shift_mm']
 inputs={p.relative_to(H).as_posix():sha(p) for p in [Path(__file__),Path(__file__).with_name('clavicle_trial.py'),Path(__file__).with_name('parts_library.py'),Path(__file__).with_name('assemble_shoulders.py'),G9/'bounded_mapping.json']}
 rows=[];start=time.time()
 for char in ('manny','quinn'):
  full,_=frames(char,x,y,z)
  for i,end in enumerate(full):
   # Endpoint whole-arm audit includes legacy module pairs intentionally not
   # included by the inherited narrow clavicle/shoulder checker.
   findings=check(end,lib,bb,True)
   rows.append({'character':char,'pose':end['pose'],'scope':'ALL_UNLIKE_MODULE_BODY_PAIRS_ENDPOINT','findings':findings})
 save('whole_arm_endpoints.json',{'input_sha256':inputs,'complete':True,'cases':rows,'scope':'Physical module groups only. Same-body connection fabrication and torso/harness remain outside this audit.','elapsed_s':time.time()-start})
 # Sample the original allocation at its actual grid. No free interpolation
 # across branch choices; checking samples is still not continuous certification.
 rows=[];count=0
 for char in ('manny','quinn'):
  for i,end in enumerate(OLD[char,'l']['poses']):
   count_l=len(MAPP[char,'l']['paths'][i]['angles_deg']);count_r=len(MAPP[char,'r']['paths'][i]['angles_deg'])
   grid=sorted(set(np.linspace(0,1,count_l).tolist()+np.linspace(0,1,count_r).tolist()))
   fail=[];inspected=0
   for u in grid[1:-1]:
    fractions={'l':round(u*(count_l-1))/(count_l-1),'r':round(u*(count_r-1))/(count_r-1),'common':u}
    states,_=frames(char,x,y,z,progress=fractions,pose_index=i);st=states[0]
    findings=check(st,lib,bb)
    inspected+=1;count+=1
    if findings:fail.append({'fraction':u,'arm_fractions':fractions,'findings':findings})
   rows.append({'character':char,'pose':end['pose'],'interior_samples':inspected,'original_left_samples':count_l,'original_right_samples':count_r,'findings':fail})
   save('sampled_paths.json',{'complete':False,'input_sha256':inputs,'cases':rows,'interior_samples':count,'elapsed_s':time.time()-start})
 assert inputs=={n:sha(H/n) for n in inputs}
 save('sampled_paths.json',{'complete':True,'input_sha256':inputs,'cases':rows,'interior_samples':count,'elapsed_s':time.time()-start,'scope':'Union of both original time grids; each arm uses its own stored <=2 deg sample and four-angle allocation, shared trunk angles use common fraction. Only inherited clavicle/shoulder relevant pairs. No continuous, arbitrary hand path, wires or torso claim.'})
 print('path samples',count,'failed paths',sum(bool(r['findings']) for r in rows),flush=True)
if __name__=='__main__':main()
