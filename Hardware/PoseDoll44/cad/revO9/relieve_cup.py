"""Local cup-bottom relief, without changing the magnet recess or journals.
Study candidates only: not a fabrication or strength release.
"""
import numpy as np,json,itertools
from common import *
from extend_forks import topology,volume,stl
from clearance import certify
from rigid_collision import Body,Pair

def relieved(length=3,relief=.35):
 m=core(length);t=m['C01'].copy();r=np.hypot(t[:,:,0],t[:,:,1]);z=t[:,:,2]
 # Piecewise-linear, monotone radial map. Zero at r<=3.2 or r>=4.8 and
 # z>=-1.5 or z<=-3.5; the 6.4 mm recess and every journal stay fixed.
 radial=np.maximum(0,np.minimum((r-3.2)/.8,(4.8-r)/.8))
 axial=np.interp(z,[-3.5,-2.5,-2.25,-1.5],[0,1,1,0],left=0,right=0)
 delta=relief*radial*axial;delta[(z>=-1.50001)|(r<=3.20001)]=0;scale=1-delta/np.maximum(r,1e-12);t[:,:,:2]*=scale[:,:,None];m['C01']=t
 return m

def main():
 rows=[]
 for length,amount in [(2,.35),(3,.35),(3,.45)]:
  meshes=relieved(length,amount);folder=OUT/f'cup_relief_L{length}_R{str(amount).replace(".","p")}';folder.mkdir(exist_ok=True);np.savez_compressed(folder/'core_meshes.npz',**meshes);records=[]
  original=core(length)
  for name,t in meshes.items():
   check=topology(t);assert not any(check[k] for k in ('boundary_edges','nonmanifold_edges','zero_area_faces'))
   stl(folder/(name+'.stl'),t);records.append({'part':name,'topology':check,'changed_vertices':int(np.any(np.abs(t-original[name])>1e-9,axis=2).sum()),'max_vertex_displacement_mm':float(np.linalg.norm(t-original[name],axis=2).max())})
  # Every source face of the recess and all source journal vertices are retained.
  t=original['C01'];rad=np.hypot(t[:,:,0],t[:,:,1]);journal=np.abs(t[:,:,0])>=5-1e-5;recess=(rad<=3.21)&(t[:,:,2]>=-1.50001)
  assert np.array_equal(meshes['C01'][journal],t[journal]);assert np.array_equal(meshes['C01'][recess],t[recess])
  manifest={'candidate':'local radial relief of cup bottom with smooth transition into attached material','extension_each_yoke_mm':length,'max_requested_radial_relief_mm':amount,'radial_support_mm':[3.2,4,4.8],'axial_support_mm':[-3.5,-2.5,-2.25,-1.5],'jacobian_radial_derivative_lower_bound':1-amount/.8,'unchanged_journal_vertices':int(journal.sum()),'unchanged_recess_vertices':int(recess.sum()),'parts':records,'volume_total_mm3':sum(volume(t) for t in meshes.values()),'physical_tested':False,'manufacturing_released':False,'source_sha256':sha(G8/f'fork_extension_{length}mm/core_meshes.npz')}
  (folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
  pair=Pair(Body(meshes['C01']),Body(meshes['C02']))
  for a,b in itertools.product((-30,0,30),(-100,0,100)):
   B=pose_matrices(a,b)['C02'];c=pair.check(B=B);r=certify(meshes['C01'],meshes['C02']@B.T);row={'length':length,'relief':amount,'alpha':a,'beta':b,'collision':c,**r};rows.append(row);print(length,amount,a,b,c['status'],r['status'],r.get('distance_at_witness_mm'),flush=True)
  save('cup_relief_search.json',{'scope':'Only the listed discrete probes; selecting a candidate requires subsequent full workspace and assembly checks.','cases':rows,'physical_tested':False,'manufacturing_released':False})
if __name__=='__main__':main()

