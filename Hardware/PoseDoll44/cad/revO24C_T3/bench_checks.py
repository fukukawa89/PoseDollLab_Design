from audit import *

def main():
 d=build();P={p['id']:p for p in d.parts};fail=[];cases=0
 for st in ['H','R','W']:
  parts=[p for p in d.parts if p['station']==st and p['id'] not in ['W3-09','WPALM_B','WPALM_N','WPALM_W']]
  states=[(q,0,0) for q in range(0,146,5)] if st=='H' else ([(q,0,0) for q in range(-85,81,5)] if st=='R' else [(0,w,v) for w in range(-65,71,5) for v in range(-20,31,5)])
  for q,w,v in states:
   items=[]
   for p in parts:
    M=np.eye(4)
    if p['frame'] in ['rotor','ball']:M=rot(Y,-q) if st=='H' else rot(Z,90-q) if st=='R' else rot(X,v)@rot(Y,w)
    s=moved(p['s'],M);items.append((p,s,bounds(s)))
   hits=collisions(items,only_moving=True);cases+=1
   if hits:fail.append(dict(station=st,angles=[q,w,v],collisions=hits))
 # Static fixture hardware / sockets also matter.
 for st in ['H','R','W']:
  pts=[p for p in d.parts if p['station']==st and p['id'] not in ['W3-09','WPALM_B','WPALM_N','WPALM_W']]
  hits=collisions([(p,p['s'],bounds(p['s'])) for p in pts])
  if hits:fail.append(dict(station=st,angles=[0,0,0],collisions=hits))
 put(OUT/'verification/bench_rom.json',dict(passed=not fail,geometry_sha256=sha(OUT/'assembly_meshes.npz'),cases=cases,failures=fail,scope='Independent actual joint modules with detachable 100mm load tools and W clamp handle; not substitute enlarged joints.'))
 # Assemble the same complete R and W modules onto the real H, then W onto R.
 S={p['id']:(p,s) for p,s,b in scene_parts(d)};installed=[i for i in S if S[i][0]['station']=='H' and not i.startswith('H_R_')];errors=[];samples=0
 for st,offset,excludes in [('R',[0,0,-35],[]),('W',[0,0,-35],['W_R_B','W_R_W','W_R_N'])]:
  moving=[i for i in S if S[i][0]['station']==st and i not in excludes]
  for f in np.linspace(1,0,71):
   for id in moving:
    ss=S[id][1].translate(np.array(offset)*f);bb=bounds(ss)
    for oid in installed:
     other=S[oid][1]
     if overlap(bb,bounds(other)) and (ss^other).volume()>.02:errors.append(dict(station=st,a=id,b=oid,offset_fraction=float(f)))
   samples+=1
  installed.extend(moving)
 put(OUT/'verification/module_insertion.json',dict(passed=not errors,geometry_sha256=sha(OUT/'assembly_meshes.npz'),samples=samples,errors=errors,scope='Same-mesh R into H and W into R, along the bone line, 0.5mm steps; crossbolts removed during insertion.'))
 print(json.dumps(dict(bench_passed=not fail,bench_failures=fail[:5],insertion_passed=not errors,insertion_errors=errors[:8]),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
