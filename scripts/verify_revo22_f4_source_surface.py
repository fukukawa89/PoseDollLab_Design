from pathlib import Path
import sys,json,numpy as np,trimesh,time
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from repair_revo22_f4_guarded_chamfer import context,O
from build_revo22_fins import solid,vf
for pid in sys.argv[1:]:
 folder=O/'candidates'/pid/'contact_full_02';n=np.load(folder/'parts'/f'{pid}.npz');r=json.loads((folder/'design'/f'{pid}.json').read_text());parts,key,T=context(r,pid);av,af=vf(parts[key].transform(T[:3,:]));bv,bf=n['v'],n['f'];values=[]
 for v,f,tv,tf in [(av,af,bv,bf),(bv,bf,av,af)]:
  tm=trimesh.Trimesh(tv,tf,process=False);pts=np.r_[v,v[f].mean(1)];dist=[]
  for k in range(0,len(pts),256):dist.extend(trimesh.proximity.closest_point(tm,pts[k:k+256])[1])
  values.append(float(max(dist)))
 d={'id':pid,'surface_sample':'All vertices and triangle centroids in both directions','directed_max_mm':values,'maximum_mm':max(values),'tolerance_mm':.005,'matched':max(values)<.005};(O/'candidates'/pid/'source_assembly_surface_match.json').write_text(json.dumps(d,indent=2));print('SOURCE_MATCH',d,flush=True)
