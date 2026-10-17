from pathlib import Path
import sys,json,numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'.local/fins-deps'))
import trimesh
from build_revo22_fins import B,O,D
def coverage(pid):
 n=np.load(O/'parts'/f'{pid}.npz');v,f=n['v'],n['f']
 mesh=trimesh.Trimesh(n['fin_v'],n['fin_f'],process=False)
 cand=json.loads((D/'mesh_candidates.json').read_text())[f'print_batch/{pid}.3mf']
 ex=json.loads((D/'additional_enforcers.json').read_text())['objects'];e=next((a['additional_enforcer_faces'] for a in ex if a['id']==pid),[])
 ids=np.array(sorted(set(cand['external_downward_candidate_faces'])|set(e)),dtype=int)
 if not len(ids) or not len(mesh.faces):return dict(id=pid,coverage=None)
 tris=v[f[ids]];area=np.linalg.norm(np.cross(tris[:,1]-tris[:,0],tris[:,2]-tris[:,0]),axis=1)/2
 cent=tris.mean(axis=1);norm=np.cross(tris[:,1]-tris[:,0],tris[:,2]-tris[:,0])
 keep=(cent[:,2]>.6)&(area>.01)&(abs(norm[:,2])>1e-8)
 protected=O/'parts'/f'{pid}_protected.stl'
 if protected.exists():
  ban=trimesh.load_mesh(protected,process=False);keep &= ~ban.contains(cent-[0,0,.2])
 cent=cent[keep];norm=norm[keep];area=area[keep]
 shifts=np.array([[0,0],[.8,0],[-.8,0],[0,.8],[0,-.8],[1.6,0],[-1.6,0],[0,1.6],[0,-1.6],[1.2,1.2],[1.2,-1.2],[-1.2,1.2],[-1.2,-1.2]])
 origins=cent[:,None,:]+np.c_[shifts,np.zeros(len(shifts))][None,:,:]
 origins[:,:,2]-=(norm[:,None,:2]*shifts[None,:,:]).sum(2)/norm[:,None,2]
 origins[:,:,2]-=.001;origins=origins.reshape(-1,3)
 loc,ray,tri=mesh.ray.intersects_location(origins,np.tile([0,0,-1.],(len(origins),1)),multiple_hits=False)
 good=np.zeros(len(origins),bool);good[ray]=((origins[ray,2]-loc[:,2])<1.0)
 covered=good.reshape(-1,len(shifts)).any(1)
 return dict(id=pid,sample_faces=len(cent),target_area_mm2=float(area.sum()),uncovered_area_mm2=float(area[~covered].sum()),coverage=float(area[covered].sum()/max(area.sum(),1e-10)),uncovered_samples=cent[~covered].round(2).tolist())
if __name__=='__main__':
 ids=sys.argv[1:] or [p.stem for p in (O/'parts').glob('*.npz')]
 for pid in ids:
  r=coverage(pid);(O/'verification'/f'{pid}_coverage.json').write_text(json.dumps(r,indent=2));print({k:v for k,v in r.items() if k!='uncovered_samples'},flush=True)
