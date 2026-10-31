"""Export existing LP6/M4 full parts to O10 with locked STEP inputs."""
from pathlib import Path
import json,hashlib,sys,time
import numpy as np,cadquery as cq
H=Path(__file__).resolve().parents[2];OUT=H/'generated/revO10/runs/o10_20260926_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 rows=[];dest=OUT/'old_modules';dest.mkdir(exist_ok=True)
 for fam,folder in [('LP6',H/'generated/revO7/runs/o7_20260924_r1/LP6_current'),('M4',H/'generated/revO6/runs/o6_20260924_r1/joint_M4_validated')]:
  manifest=json.loads((folder/'manifest.json').read_text());meshes={};groups={'parent':[],'child':[]};inputs={}
  for row in manifest['parts']:
   p=folder/row['step_file'];digest=sha(p);assert digest==row['step_sha256'];s=cq.importers.importStep(str(p)).val();v,f=s.tessellate(.03,.06);v=np.array([x.toTuple() for x in v]);t=v[np.array(f)];meshes[row['part_id']]=t;groups[row['owner']].append(t);inputs[str(p.relative_to(H))]=digest
  for k,v in groups.items():np.savez_compressed(dest/f'{fam}_{k}.npz',**{name:t for name,t in meshes.items() if next(r for r in manifest['parts'] if r['part_id']==name)['owner']==k})
  assert all(sha(H/p)==v for p,v in inputs.items());rows.append({'family':fam,'manifest_sha256':sha(folder/'manifest.json'),'input_sha256':inputs,'tessellation_linear_mm':.03,'tessellation_angular_rad':.06,'part_count':len(meshes),'triangles':sum(len(t) for t in meshes.values())});print(fam,rows[-1]['triangles'],flush=True)
 (dest/'manifest.json').write_text(json.dumps({'libraries':rows,'scope':'STEP surfaces tessellated for collision screening. Sub-tessellation clearance is unresolved, not certified.'},indent=2)+'\n')
if __name__=='__main__':main()
