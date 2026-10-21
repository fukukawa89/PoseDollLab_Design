"""Continuous C01/C02 clearance for face-brake forks; all new faces retained."""
from pathlib import Path
import sys,json,time,hashlib,numpy as np
H=Path(__file__).resolve().parents[2];OUT10=H/'generated/revO10/runs/o10_20260926_r1'
from surface_distance import UnsignedCertificate
sys.path.insert(0,str(Path(__file__).parent));from solid_ops import from_tri

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 path=OUT10/'face_brake/parts.npz';sources=[path,Path(__file__),H/'cad/revO9/continuous_clearance.py',H/'cad/revO9/rigid_collision.py',H/'cad/revO9/common.py',H/'cad/revO8/mesh_collision.py',H/'cad/revO10/surface_distance.py',H/'cad/revO10/solid_ops.py'];before={str(p.relative_to(H)):sha(p) for p in sources};m=dict(np.load(path));c=UnsignedCertificate(m['C01'],m['C02']);iv=(from_tri(m['C01'])^from_tri(m['C02'])).volume();assert iv<1e-8, 'Initial overlap or containment';initial={'closed_volume_intersection_mm3':iv,'method':'independent manifold3d CSG'};stack=[((-28.,28.),(-98.,98.),0)];rows=[];bad=[];unknown=[];count=0;t0=time.time()
 while stack:
  aa,bb,depth=stack.pop();r=c.cell(aa,bb,required=.60002);row={'alpha':aa,'beta':bb,**r};count+=1
  if r['status']=='CERTIFIED_CONTINUOUS_NOMINAL_CLEARANCE':rows.append(row)
  elif r['status']=='INSUFFICIENT_AT_CELL_CENTER':bad.append(row)
  elif depth>=24 or max(aa[1]-aa[0],bb[1]-bb[0])<.125:unknown.append(row)
  elif aa[1]-aa[0]>=bb[1]-bb[0]:
   mid=sum(aa)/2;stack.extend([((aa[0],mid),bb,depth+1),((mid,aa[1]),bb,depth+1)])
  else:
   mid=sum(bb)/2;stack.extend([(aa,(bb[0],mid),depth+1),(aa,(mid,bb[1]),depth+1)])
  if count%100==0:print(count,len(rows),len(bad),len(unknown),'pending',len(stack),flush=True)
 after={str(p.relative_to(H)):sha(p) for p in sources};assert before==after,'Input changed during proof'
 area=sum((r['alpha'][1]-r['alpha'][0])*(r['beta'][1]-r['beta'][0]) for r in rows+bad+unknown);assert abs(area-56*196)<1e-7
 out={'status':'CERTIFIED_NOMINAL_YOKE_PAIR_ONLY' if not bad and not unknown else 'FAIL_OR_INCOMPLETE','initial_disjoint':initial,'target_triangle_accounting':c.target.distance.counts,'required_mm':.6,'computed_distance_guard_mm':.60002,'distance_method':'All original triangles retained, exact vertex merge only; unsigned distance plus independent disjoint initial closed volumes and positive clearance over a connected rectangle','alpha_deg':[-28,28],'beta_deg':[-98,98],'certified_cells':rows,'failed_cells':bad,'unknown_cells':unknown,'area_deg2':area,'elapsed_s':time.time()-t0,'input_sha256':before,'scope':'Two enlarged fork bodies including brake bosses, stop ears and magnet support. Ring, axles, springs, thread retention, housings and wires require their own checks. Not whole-joint qualification.','manufacturing_released':False}
 (OUT10/'face_brake/continuous_yokes.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status'],len(rows),len(bad),len(unknown),out['elapsed_s'],flush=True)
if __name__=='__main__':main()



