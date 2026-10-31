from pathlib import Path
import sys,json,numpy as np,copy
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,vf,md
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
from verify_revo22_f4_body_change import check as fit
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4';F=O.parent/'O22F3_Release/reference'
def transfer(donor,label,target,newlabel):
 groups=json.loads((O/'source_canonical_groups.json').read_text()) if (O/'source_canonical_groups.json').exists() else []
 groups=json.loads((O/'source_congruence_groups.json').read_text())+groups;group=next(q for q in groups if {donor,target}.issubset({v['id'] for v in q['members']}));members={q['id']:q for q in group['members']};d=members[donor];t=members[target];Q=np.array(d['Q']).T@np.array(t['Q']);shift=np.array(d['Q']).T@(np.array(t['shift'])-np.array(d['shift']));P=np.diag([-1.,1.,1.]) if np.linalg.det(Q)<0 else np.eye(3);src=O/'candidates'/donor/label;dst=O/'candidates'/target/newlabel
 for sub in ['parts','design','verification']:(dst/sub).mkdir(parents=True,exist_ok=True)
 nn=dict(np.load(src/'parts'/f'{donor}.npz'));tn=np.load(F/'parts'/f'{target}.npz');r=json.loads((src/'design'/f'{donor}.json').read_text());tr=json.loads((F/'design'/f'{target}.json').read_text());Md=np.array(r['orientation']['matrix']);td=np.array(r['orientation']['source_translation_mm']);M=P@Md@Q;t0=P@(td+Md@shift);v=tn['source_v']@M.T+t0;f=tn['f'];s=solid(v,f);donorsource=solid(nn['source_v']@Md.T+td,nn.get('source_f',nn['f']));source_difference=float(((s.transform(np.c_[P,[0,0,0]])-donorsource)+(donorsource-s.transform(np.c_[P,[0,0,0]]))).volume());assert source_difference<.03,(target,source_difference)
 def transform(vk,fk):
  vv=nn[vk]@P.T;ff=nn[fk][:,::-1].copy() if np.linalg.det(P)<0 else nn[fk];return vv,ff
 out={'source_v':tn['source_v'].copy(),'v':v,'f':f.copy()}
 for vk,fk in [('fin_v','fin_f'),('teeth_v','teeth_f')]:out[vk],out[fk]=transform(vk,fk)
 if 'body_change' in r:
  assert r['body_change'].get('added_volume_mm3',0)<1e-6,'Only validated subtractive changes may be transferred by this function'
  rem=solid(*transform('removed_body_v','removed_body_f'));new=s-rem;out['source_f']=f.copy();out['v'],out['f']=vf(new);out['removed_body_v'],out['removed_body_f']=vf(s-new);r['body_change']['removed_volume_mm3']=float((s-new).volume());r['body_change']['source_body_volume_mm3']=float(s.volume());r['body_change']['removed_fraction']=float((s-new).volume()/s.volume());r['body_change']['assembly_contact_validation_pending']=True
 def bounds(bb):
  vv=np.array([[x,y,z] for x in [bb[0],bb[3]] for y in [bb[1],bb[4]] for z in [bb[2],bb[5]]])@P.T;return np.r_[vv.min(0),vv.max(0)].tolist()
 for row in r.get('segments',[]):row['bounds_mm']=bounds(row['bounds_mm'])
 for row in r.get('teeth',[]):
  row['bounds_mm']=bounds(row['bounds_mm'])
  if 'contact_point_mm' in row:row['contact_point_mm']=(P@row['contact_point_mm']).tolist()
 for row in r.get('body_change',{}).get('chamfers',[]):row['local_bounds_mm']=bounds(row['local_bounds_mm'])
 r.update(id=target,part=tr['part'],orientation={'matrix':M.tolist(),'source_translation_mm':t0.tolist(),'gravity_in_source':M[2].tolist(),'size_mm':np.ptp(v,axis=0).tolist()},source_mesh_preserved='body_change' not in r,transfer_provenance={'donor':donor,'label':label,'source_symmetric_difference_mm3':source_difference,'print_mirror_matrix':P.tolist(),'source_mapping_matrix':Q.tolist(),'source_mapping_translation_mm':shift.tolist(),'independent_target_fit_and_slice_required':True});np.savez_compressed(dst/'parts'/f'{target}.npz',**out);(dst/'design'/f'{target}.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8');print('TRANSFER',donor,target,source_difference,flush=True);run(target,newlabel);d=check(target,newlabel)
 if 'body_change' in r:fit(target,newlabel)
 return d
if __name__=='__main__':transfer(*sys.argv[1:])
