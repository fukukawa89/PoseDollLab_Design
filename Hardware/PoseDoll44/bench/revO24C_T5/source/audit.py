from arm_kit import *
import itertools, time

def bounds(s):return np.array(s.bounding_box()).reshape(2,3)
def overlap(A,B):return np.all(np.minimum(A[1],B[1])-np.maximum(A[0],B[0])>.008)
def scene_parts(d,mode='arm',q=0,r=0,w=0,v=0):
 F=transforms(mode,q,r,w,v);out=[]
 for p in d.parts:
  if p['bench_only']:continue
  s=moved(p['s'],F[p['station']][p['frame']]);out.append((p,s,bounds(s)))
 return out

def collisions(parts,only_moving=False):
 rows=[]
 for (p,s,b),(p2,s2,b2) in itertools.combinations(parts,2):
  if only_moving and p['station']==p2['station'] and p['frame']==p2['frame']:continue
  if not overlap(b,b2):continue
  vol=(s^s2).volume()
  if vol>.015:rows.append(dict(a=p['id'],b=p2['id'],volume_mm3=round(vol,6)))
 return rows

def main():
 d=build();cases=[('neutral',0,0,0,0)]
 cases += [('H'+str(q),q,0,0,0) for q in range(0,146,5)]
 cases += [('R'+str(r),90,r,0,0) for r in range(-85,81,5)]
 cases += [('W'+str((w,v)),90,0,w,v) for w in sorted(set(range(-65,71,2))|{70}) for v in range(-20,31,2)]
 cases += [('fold'+str((r,w,v)),145,r,w,v) for r in [-85,0,80] for w,v in [(-65,-20),(-65,30),(70,-20),(70,30),(0,0)]]
 failures=[];pairs={};start=time.time()
 for i,(name,q,r,w,v) in enumerate(cases):
  c=collisions(scene_parts(d,q=q,r=r,w=w,v=v),only_moving=i>0)
  if c:
   failures.append(dict(case=name,pose=[q,r,w,v],collisions=c))
   for item in c:
    key=item['a']+' / '+item['b']
    if key not in pairs or pairs[key]['volume_mm3']<item['volume_mm3']:pairs[key]=dict(**item,case=name)
  if i%80==0:print('CHECK',i,len(cases),'pairs',len(pairs),'seconds',round(time.time()-start,1),flush=True)
 report=dict(passed=not failures,geometry_sha256=sha(OUT/'assembly_meshes.npz'),cases=len(cases),failures=failures,worst_pairs=list(pairs.values()),angular_step_deg={'H_R':5,'W':2},scope='Nominal rigid-solid interference; selected elbow/roll states, full specified wrist angle grid including endpoints, selected deep elbow combinations. Not full 9-DOF global Cartesian ROM or physical holding test.')
 put(OUT/'verification/installed_rom.json',report)
 print(json.dumps(dict(passed=not failures,cases=len(cases),pairs=list(pairs.values())),ensure_ascii=False),flush=True)

if __name__=='__main__':main()
