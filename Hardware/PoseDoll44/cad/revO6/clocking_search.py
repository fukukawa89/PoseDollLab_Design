"""Bounded clocking search at the observed clavicle/twist side-raise contact."""
from pathlib import Path
import argparse,hashlib,itertools,json,sys
import numpy as np
import cadquery as cq
R=Path(__file__).resolve().parents[4];H=R/'Hardware/PoseDoll44'
sys.path.insert(0,str(H/'cad'));from model import rotation
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def loc(s,M):return s.moved(cq.Location(cq.Plane(origin=tuple(M[:3,3]),xDir=tuple(M[:3,0]),normal=tuple(M[:3,2]))))
def main():
 p=argparse.ArgumentParser();p.add_argument('--joint',type=Path,required=True);p.add_argument('--layout',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.joint=a.joint.resolve();a.layout=a.layout.resolve()
 m=json.loads((a.joint/'manifest.json').read_text());L=json.loads(a.layout.read_text());parts=[];inputs={a.layout.relative_to(R).as_posix():sha(a.layout),(a.joint/'manifest.json').relative_to(R).as_posix():sha(a.joint/'manifest.json'),Path(__file__).relative_to(R).as_posix():sha(Path(__file__))}
 for row in m['parts']:
  path=a.joint/row['step_file'];assert sha(path)==row['step_sha256'];inputs[path.relative_to(R).as_posix()]=sha(path)
  b=row['bounds_mm'];parts.append((row['part_id'],cq.importers.importStep(str(path)).val(),np.array(list(itertools.product(*zip(b[:3],b[3:]))))))
 trials=[]
 # Only parent/child coaxial spin of the two placement frames is changed here;
 # their relative revolute poses are zero in neutral and pure shoulder abduction.
 for cp,ct in itertools.product((0,90,180,270),(0,45,90,135,180,225,270,315)):
  hits=[];evaluations=0
  for character in L['characters']:
   if character['side']!='l':continue
   k=next(i for i,p in enumerate(character['poses']) if p['pose']=='arms_side')
   mats=[np.array(character['module_frames'][i][k]) for i in (0,4)]
   for M,clock in zip(mats,(cp,ct)):M[:3,:3]=M[:3,:3]@rotation([0,0,1],clock)
   rows=[]
   for M in mats:
    ps=[corners@M[:3,:3].T+M[:3,3] for _,_,corners in parts];rows.append((np.array([q.min(0) for q in ps]),np.array([q.max(0) for q in ps])))
   ov=np.minimum(rows[0][1][:,None,:],rows[1][1][None,:,:])-np.maximum(rows[0][0][:,None,:],rows[1][0][None,:,:])
   indices=np.argwhere((ov>1e-5).all(2));indices=sorted(indices,key=lambda ab:-float(np.prod(ov[ab[0],ab[1]])))
   for i,j in indices:
    v=loc(parts[i][1],mats[0]).intersect(loc(parts[j][1],mats[1])).Volume();evaluations+=1
    if v>1e-4:hits.append({'character':character['character'],'a':parts[i][0],'b':parts[j][0],'volume_mm3':v});break
  trials.append({'clavicle_clock_deg':cp,'twist_clock_deg':ct,'hits':hits,'exact_evaluations':evaluations})
  print(cp,ct,'hits',len(hits),flush=True)
  if not hits:break
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps({'schema':'o6-local-clocking-study-v1','trials':trials,'selected':next((t for t in trials if not t['hits']),None),'scope':'Only witnessed clavicle-protract / upperarm-twist contact at 90 degree abduction, two references. Full arm recheck required.','input_sha256':inputs,'physical_tested':False},indent=2)+'\n',encoding='utf-8')
 assert all(sha(R/k)==h for k,h in inputs.items())
if __name__=='__main__':main()

