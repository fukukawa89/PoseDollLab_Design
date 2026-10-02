"""Exact BRep witnesses for selected poses after O6 conservative layout search."""
from pathlib import Path
import argparse,hashlib,json,sys,itertools
import numpy as np
import cadquery as cq
R=Path(__file__).resolve().parents[4];H=R/'Hardware/PoseDoll44'
sys.path.insert(0,str(R/'scripts'));sys.path.insert(0,str(H/'cad'))
from model import fk,rotation
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def located(s,M):return s.moved(cq.Location(cq.Plane(origin=tuple(M[:3,3]),xDir=tuple(M[:3,0]),normal=tuple(M[:3,2]))))
def bb(s):
 b=s.BoundingBox();return [b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--joint',type=Path,required=True);ap.add_argument('--layout',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 a.joint=a.joint.resolve();a.layout=a.layout.resolve();a.out=a.out.resolve()
 m=json.loads((a.joint/'manifest.json').read_text());layout=json.loads((a.layout/'layout_search.json').read_text());sources=[a.joint/'manifest.json',a.layout/'layout_search.json',Path(__file__),H/'cad/model.py']
 parts=[]
 for row in m['parts']:
  p=a.joint/row['step_file'];assert sha(p)==row['step_sha256'];sources.append(p)
  b=row['bounds_mm'];corners=np.array(list(itertools.product(*zip(b[:3],b[3:]))))
  parts.append((row['part_id'],row['owner'],cq.importers.importStep(str(p)).val(),corners))
 receipts={p.relative_to(R).as_posix():sha(p) for p in sources};results=[];a.out.mkdir(parents=True,exist_ok=True)
 for character in layout['characters']:
  ch,side=character['character'],character['side'];pfile=a.layout/(ch+'_'+side+'_profile.json');receipts[pfile.relative_to(R).as_posix()]=sha(pfile);profile=json.loads(pfile.read_text())
  names=['neutral','arms_side']
  if ch=='manny' and side=='l':names+=['arms_overhead','arms_crossed','back_reach_45']
  for k,pose in enumerate(character['poses']):
   if pose['pose'] not in names:continue
   T,axes=fk(profile,pose['angles_deg']);objects={}
   for i,axis in enumerate(character['axes']):
    M=np.array(character['module_frames'][i][k]);C=M.copy();C[:3,:3]=rotation(axes[axis]['direction'],pose['angles_deg'].get(axis,0))@M[:3,:3]
    rows=[]
    for n,owner,shape,corners in parts:
     frame=C if owner=='child' else M;points=corners@frame[:3,:3].T+frame[:3,3]
     rows.append((n,shape,frame,points.min(0),points.max(0)))
    objects[axis]=rows
   actual=[];clear=[];counts=0;allbb=[]
   for x,y in itertools.combinations(character['axes'],2):
    A,B=objects[x],objects[y];la=np.array([r[3] for r in A]);ha=np.array([r[4] for r in A]);lb=np.array([r[3] for r in B]);hb=np.array([r[4] for r in B])
    overlap=np.minimum(ha[:,None,:],hb[None,:,:])-np.maximum(la[:,None,:],lb[None,:,:])
    candidates=np.argwhere((overlap>1e-5).all(2));hit=None
    for ai,bi in candidates:
     an,sa,ma,_,_=A[ai];bn,sb,mb,_,_=B[bi];counts+=1
     va=located(sa,ma).intersect(located(sb,mb)).Volume()
     if va>1e-4:
      hit={'axis_a':x,'axis_b':y,'part_a':an,'part_b':bn,'intersection_mm3':va};actual.append(hit);break
    if hit is None:clear.append([x,y])
   if pose['pose']=='neutral':
    shapes=[located(s,M) for group in objects.values() for _,s,M,_,_ in group]
    neutral=cq.Compound.makeCompound(shapes)
    if ch=='manny' and side=='l':cq.exporters.export(neutral,str(a.out/'manny_left_nine_axis_positioned.step'))
    allbb=bb(neutral)
   result={'character':ch,'side':side,'pose':pose['pose'],'angles_deg':pose['angles_deg'],'nominal_bounds_mm':allbb,'first_intersection_per_joint_pair':actual,'fully_checked_clear_joint_pairs':clear,'exact_part_pair_evaluations':counts,'scope':'All 36 distinct module pairs: full candidate-part search for clear pairs; stop at first positive witness for failed pairs. No yokes/boards/shell here.','status':'FAIL' if actual else 'PASS_NOMINAL_MODULES_ONLY'}
   results.append(result);save(a.out/'exact_module_audit.json',{'cases':results,'input_sha256':receipts,'physical_tested':False,'manufacturing_released':False})
   print(ch,side,pose['pose'],'actual',len(actual),'exact',counts,flush=True)
 assert all(sha(R/k)==h for k,h in receipts.items())
if __name__=='__main__':main()

