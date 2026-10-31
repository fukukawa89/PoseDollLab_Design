from pathlib import Path
import sys,json,numpy as np,trimesh,copy
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,vf
from o22_reference_mesh import reference_solid
from o22_mesh_identity import body_sha
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
from refine_revo22_f4_full_bead import refine
from verify_revo22_f4_body_change import check as fit
from verify_revo22_f4_repaired_geometry import check as geom
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def trial(donor,donorlabel,target,previous,label):
 src=O/'candidates'/donor/donorlabel;dst=O/'candidates'/target/label;prior=O/'candidates'/target/previous
 for sub in ['parts','design','verification']:(dst/sub).mkdir(parents=True,exist_ok=True)
 dn=np.load(src/'parts'/f'{donor}.npz');dd=json.loads((src/'design'/f'{donor}.json').read_text());tn=np.load(O.parent/'O22F3_Release/reference/parts'/f'{target}.npz');d=json.loads((prior/'design'/f'{target}.json').read_text());P=np.array(d['transfer_provenance']['print_mirror_matrix']);n={'source_v':tn['source_v'],'source_f':tn['f']}
 for vk,fk in [('v','f'),('fin_v','fin_f'),('teeth_v','teeth_f'),('removed_body_v','removed_body_f')]:n[vk]=dn[vk]@P.T;n[fk]=dn[fk][:,::-1].copy() if np.linalg.det(P)<0 else dn[fk].copy()
 rv,rf=vf(reference_solid(dn,dd).transform(np.c_[P,[0,0,0]]));n['registered_reference_print_v']=rv;n['registered_reference_print_f']=rf;M=np.array(d['orientation']['matrix']);t=np.array(d['orientation']['source_translation_mm']);ov=tn['source_v']@M.T+t;old=trimesh.Trimesh(ov,tn['f'],process=False);ref=trimesh.Trimesh(rv,rf,process=False)
 def maxdist(mesh,pts):return max(float(trimesh.proximity.closest_point(mesh,pts[i:i+2048])[1].max())for i in range(0,len(pts),2048))
 dist=max(maxdist(old,np.r_[rv,ref.triangles_center]),maxdist(ref,np.r_[ov,old.triangles_center]));rs=solid(rv,rf);cert={'qualified':dist<.0001 and abs((rs-rs).volume())<1e-6,'method':'Rigid registration of the original congruent donor reference. Both frozen target vertices and triangle centers are checked against the registered reference and vice versa. No design dimension is intentionally changed. Exact donor print meshes are retained to avoid Boolean triangulation artifacts.','donor':donor,'donor_label':donorlabel,'max_bidirectional_sampled_boundary_distance_mm':dist,'frozen_source_mesh_sha256':body_sha({'v':tn['source_v'],'f':tn['f']}),'printed_reference_mesh_sha256':body_sha({'v':rv,'f':rf}),'orientation_matrix':M.tolist(),'source_translation_mm':t.tolist()};assert cert['qualified'],cert;d['registered_reference']=cert;d.pop('nominal_reference',None);d['transfer_provenance']['exact_donor_print_meshes_retained']=True;d['body_change']['removed_volume_mm3']=float((rs-solid(n['v'],n['f'])).volume());d['body_change']['added_volume_mm3']=float((solid(n['v'],n['f'])-rs).volume());np.savez_compressed(dst/'parts'/f'{target}.npz',**n);(dst/'design'/f'{target}.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');print('EXACT_TRANSFER',target,dist,d['body_change']['added_volume_mm3'],flush=True);run(target,label);check(target,label);q=refine(target,label);fr=fit(target,label);g=geom(target,label);print('EXACT_TRANSFER_RESULT',target,q['external_island_count'],q['critical_external_count'],fr['fit_and_pose_geometry_passed'],g['geometric_constraints_passed'],flush=True)
if __name__=='__main__':trial(*sys.argv[1:])
