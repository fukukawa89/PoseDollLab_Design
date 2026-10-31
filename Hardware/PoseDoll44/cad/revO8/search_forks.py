"""Finite-pose screening of localized fork extensions. No full joint qualification."""
import itertools,json,hashlib
from pathlib import Path
import numpy as np
from reference_assembly import OUT,at_pose
from mesh_collision import compare


def run(meshes,angles):
 rows=[]
 for alpha,beta in angles:
  placed=at_pose(meshes,alpha,beta);bad=[]
  for x,y in itertools.combinations(placed,2):
   if {x,y}=={'C14','C15'}:continue
   a,b=placed[x],placed[y]
   if np.any(np.minimum(a.max((0,1)),b.max((0,1)))-np.maximum(a.min((0,1)),b.min((0,1)))<0):continue
   result=compare(a,b)
   if result['status']!='CLEAR_NOMINAL_MESH':bad.append({'a':x,'b':y,**result})
  status='FAIL' if any(x['status']=='PENETRATION' for x in bad) else 'REVIEW' if bad else 'PASS_CORE_MESH_ONLY'
  rows.append({'alpha_deg':alpha,'beta_deg':beta,'status':status,'findings':bad})
  print(alpha,beta,status,flush=True)
 return rows


def main():
 report={'scope':'Two yokes and split ring only; discrete nominal meshes. Excludes screws, housings, PCB, wire and manufacturing tolerance.','candidates':[],'physical_tested':False,'manufacturing_released':False}
 angles=[(0,0)]+[(s*a,0) for a in (95,100,105,110) for s in (-1,1)]+[(0,s*a) for a in (95,100,105,110) for s in (-1,1)]+list(itertools.product((-75,75),repeat=2))
 for length in (0,1,2,3,4):
  folder=OUT.parent/f'fork_extension_{length}mm';meshes=dict(np.load(folder/'core_meshes.npz'));print('EXTENSION',length,flush=True)
  rows=run(meshes,angles);item={'extension_mm':length,'input_sha256':hashlib.sha256((folder/'core_meshes.npz').read_bytes()).hexdigest(),'cases':rows,'pass':sum(x['status']=='PASS_CORE_MESH_ONLY' for x in rows),'fail':sum(x['status']=='FAIL' for x in rows),'review':sum(x['status']=='REVIEW' for x in rows)}
  report['candidates'].append(item);(OUT.parent/'fork_search.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print([(x['extension_mm'],x['pass'],x['fail'],x['review']) for x in report['candidates']])
if __name__=='__main__':main()
