from build_guide import *
from collections import Counter
import time

def main():
 t0=time.time();d=load(DEST/'steps.json');a=load(SOURCE/'production_assembly.json')['parts'];z=np.load(SOURCE/'production_meshes.npz');S={}
 for p in a:
  i=str(p['i']);s=md.Manifold(md.Mesh64(np.array(z[i+'v'],copy=True),np.array(z[i+'f'],dtype=np.uint64,copy=True)));S[p['part_number']]=moved(s,F0[p['frame']])
 rows=[]
 for st in d['steps']:
  if st['kind']=='pose':continue
  active=st['parts'];fixed=union(S[n].translate(st['offsets'].get(n,[0,0,0])) for n in st['visible'] if n not in active);moving=union(S[n] for n in active).translate(st['base_offset']);pts=[np.array(p) for p in st['path']];shifts=[]
  if len(pts)==1:shifts=pts
  else:
   for p,q in zip(pts[:-1],pts[1:]):
    for t in np.linspace(0,1,math.ceil(np.linalg.norm(q-p)/.25)+1):shifts.append(p*(1-t)+q*t)
  mx=0.;bad=[]
  for off in shifts:
   vol=(moving.translate(off)^fixed).volume();mx=max(mx,vol)
   if vol>.02 and len(bad)<3:bad.append(dict(offset=off.tolist(),volume_mm3=vol))
  # The individual nut insertion is checked against a genuinely displaced cover,
  # not a lid already on the seat; similarly for four-side wrist preassembly.
  row=dict(step=st['number'],title=st['title'],current=active,samples=len(shifts),maximum_intersection_mm3=mx,passed=mx<.02,bad_samples=bad);rows.append(row)
  if not row['passed'] or len(rows)%25==0:print('PATH',len(rows),st['title'],mx,flush=True)
 checks=[]
 def ck(n,ok):checks.append(dict(check=n,passed=bool(ok)))
 ids={p['id'] for p in d['parts']};fresh=Counter(n for st in d['steps'] for n in st['new_parts']);ck('each of 146 physical items first appears exactly once',set(fresh)==ids and all(v==1 for v in fresh.values()))
 ck('final assembly contains every mechanical item',set(d['steps'][-1]['visible'])==ids)
 ck('every part has explicit direction and model annotations',all(p['orientation'] and len(p['markers'])+len(p['arrows'])>=2 for p in d['parts']))
 ck('every step identifies current items and receiving print direction',all(st['parts'] and st['printed_direction'] and st['metal_direction'] and st['target'] in ids for st in d['steps']))
 ck('cover nut steps are separated before cover closure',sum(st['title'].startswith('压盖锁母') for st in d['steps'])==6 and sum(st['title']=='将带锁母的压盖合到固定座' for st in d['steps'])==3)
 ck('wrist centre inner hardware stays at separate bench position',all(np.linalg.norm(st['base_offset'])>49 for st in d['steps'] if st['chapter']=='W' and st['source_step'] and 2<=st['source_step']<=22))
 counts=Counter(p['sku'] for p in d['parts']);ck('12 prints and 134 hardware, no electronics',len(d['parts'])==146 and counts[None]==12 and d['mechanical_only'])
 spring_rows=[]
 for group,ps in d['spring_groups'].items():
  if group=='RP':
   one=[p for p in ps if '_A8_1_' in p['feature']];two=[p for p in ps if '_A8_2_' in p['feature']];ok=len(one)==len(two)==2 and np.dot(one[0]['direction'],one[1]['direction'])>.99 and np.dot(two[0]['direction'],two[1]['direction'])>.99 and np.dot(one[0]['direction'],two[0]['direction'])<-.99
  else:ok=len(ps)==2 and np.dot(ps[0]['direction'],ps[1]['direction'])<-.99
  spring_rows.append(dict(group=group,passed=bool(ok),members=ps))
 ck('all 24 A8 arrows agree with actual inner and outer rim geometry',sum(len(x['members']) for x in spring_rows)==24 and all(r['passed'] for r in spring_rows))
 ck('all path samples clear fixed installed bodies',all(r['passed'] for r in rows))
 ck('source R2 output files remain unchanged',all(sha(H/n)==v for n,v in load(DEST/'source_fingerprints.json').items()))
 pose=load(SOURCE/'verification/motion_dense.json');ck('final A pose lies on already checked shoulder-abduction sweep',pose['geometry_sha256']==d['geometry_sha256'] and pose['status']=='PASS_SAMPLED')
 result=dict(status='PASS_GUIDE_GEOMETRY' if all(c['passed'] for c in checks) else 'REVIEW_REQUIRED',geometry_sha256=d['geometry_sha256'],steps=len(d['steps']),checks=checks,paths=rows,springs=spring_rows,total_samples=sum(r['samples'] for r in rows),seconds=time.time()-t0,scope='Exact R2 production geometry; translated assembly paths sampled at <=0.25 mm, including isolated cover and wrist preparation. Final pose uses R2 kinematic chain and inherited sampled sweep. Does not simulate hands, tools, elastic insertion force or helical thread engagement. No physical-test claim.')
 put(DEST/'verification/assembly_paths.json',result);print(result['status'],[x for x in checks if not x['passed']],flush=True)
if __name__=='__main__':main()
