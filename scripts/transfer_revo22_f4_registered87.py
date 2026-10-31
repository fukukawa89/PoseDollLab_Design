from pathlib import Path
import sys,json,numpy as np,trimesh,copy,concurrent.futures,traceback
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,vf
from o22_reference_mesh import reference_solid
from o22_mesh_identity import body_sha
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
from refine_revo22_f4_full_bead import refine
from verify_revo22_f4_body_change import check as fit
from verify_revo22_f4_repaired_geometry import check as geom
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4';F=O.parent/'O22F3_Release/reference'
def trial(donor,donorlabel,target,label):
 src=O/'candidates'/donor/donorlabel;dst=O/'candidates'/target/label
 for sub in ['parts','design','verification']:(dst/sub).mkdir(parents=True,exist_ok=True)
 groups=json.loads((O/'source_congruence_groups.json').read_text())+json.loads((O/'source_canonical_groups.json').read_text());g=next(g for g in groups if {donor,target}.issubset({q['id']for q in g['members']}));mem={q['id']:q for q in g['members']};a=mem[donor];b=mem[target];Q=np.array(a['Q']).T@np.array(b['Q']);shift=np.array(a['Q']).T@(np.array(b['shift'])-np.array(a['shift']));P=np.diag([-1.,1.,1.])if np.linalg.det(Q)<0 else np.eye(3);dn=np.load(src/'parts'/f'{donor}.npz');d=json.loads((src/'design'/f'{donor}.json').read_text());tn=np.load(F/'parts'/f'{target}.npz');td=json.loads((F/'design'/f'{target}.json').read_text());Md=np.array(d['orientation']['matrix']);ot=np.array(d['orientation']['source_translation_mm']);M=P@Md@Q;t=P@(ot+Md@shift);n={'source_v':tn['source_v'],'source_f':tn['f']}
 for vk,fk in [('v','f'),('fin_v','fin_f'),('teeth_v','teeth_f'),('removed_body_v','removed_body_f')]:
  if vk in dn:n[vk]=dn[vk]@P.T;n[fk]=dn[fk][:,::-1].copy()if np.linalg.det(P)<0 else dn[fk].copy()
 rv,rf=vf(reference_solid(dn,d).transform(np.c_[P,[0,0,0]]));n['registered_reference_print_v']=rv;n['registered_reference_print_f']=rf;ov=tn['source_v']@M.T+t;old=trimesh.Trimesh(ov,tn['f'],process=False);ref=trimesh.Trimesh(rv,rf,process=False)
 def maxdist(mesh,pts):return max(float(trimesh.proximity.closest_point(mesh,pts[i:i+2048])[1].max())for i in range(0,len(pts),2048))
 dist=max(maxdist(old,np.r_[rv,ref.triangles_center]),maxdist(ref,np.r_[ov,old.triangles_center]));rs=solid(rv,rf);cert={'qualified':dist<.0001 and abs((rs-rs).volume())<1e-6,'method':'Rigidly register the original congruent donor reference; independently compare all frozen target vertices and face centres against the registered reference and vice versa. Copy exact donor print meshes without subtracting the repair a second time.','donor':donor,'donor_label':donorlabel,'max_bidirectional_sampled_boundary_distance_mm':dist,'frozen_source_mesh_sha256':body_sha({'v':tn['source_v'],'f':tn['f']}),'printed_reference_mesh_sha256':body_sha({'v':rv,'f':rf}),'orientation_matrix':M.tolist(),'source_translation_mm':t.tolist()};assert cert['qualified'],cert
 def bounds(bb):
  pts=np.array([[x,y,z]for x in[bb[0],bb[3]]for y in[bb[1],bb[4]]for z in[bb[2],bb[5]]])@P.T;return np.r_[pts.min(0),pts.max(0)].tolist()
 for r in d.get('segments',[]):r['bounds_mm']=bounds(r['bounds_mm'])
 for r in d.get('teeth',[]):
  r['bounds_mm']=bounds(r['bounds_mm'])
  if 'contact_point_mm'in r:r['contact_point_mm']=(P@r['contact_point_mm']).tolist()
 for r in d.get('body_change',{}).get('chamfers',[]):r['local_bounds_mm']=bounds(r['local_bounds_mm'])
 d.update(id=target,part=td['part'],registered_reference=cert,orientation={'matrix':M.tolist(),'source_translation_mm':t.tolist(),'gravity_in_source':M[2].tolist(),'size_mm':np.ptp(n['v'],axis=0).tolist()},source_mesh_preserved=False,transfer_provenance={'donor':donor,'label':donorlabel,'print_mirror_matrix':P.tolist(),'source_mapping_matrix':Q.tolist(),'source_mapping_translation_mm':shift.tolist(),'exact_donor_print_meshes_retained':True,'independent_target_fit_and_slice_required':True});d.pop('nominal_reference',None);d.setdefault('body_change',{'kind':'registered_congruent_reference','chamfers':[]});d['body_change'].update(removed_volume_mm3=float((rs-solid(n['v'],n['f'])).volume()),added_volume_mm3=float((solid(n['v'],n['f'])-rs).volume()),source_body_volume_mm3=float(rs.volume()));np.savez_compressed(dst/'parts'/f'{target}.npz',**n);(dst/'design'/f'{target}.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');print('REGISTERED87',target,dist,flush=True);run(target,label);check(target,label);q=refine(target,label);f=fit(target,label);g=geom(target,label);return {'id':target,'label':label,'native':q['native_review_resolved'],'fit':f['fit_and_pose_geometry_passed'],'geometry':g['geometric_constraints_passed']}
def one(spec):
 try:return trial(*spec.split(':'))
 except Exception:return {'spec':spec,'error':traceback.format_exc()}
if __name__=='__main__':
 out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as pool:
  for f in concurrent.futures.as_completed([pool.submit(one,s)for s in sys.argv[1:]]):
   out.append(f.result());print('REGISTERED87_RESULT',out[-1],flush=True);(O/'registered87_progress.json').write_text(json.dumps(out,indent=2))
