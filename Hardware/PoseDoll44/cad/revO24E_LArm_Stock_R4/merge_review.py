from check_stock import saved
from build_stock import *
from collections import defaultdict

def main():
 a,ss=saved();P={p['name']:p for p in a};S={p['name']:moved(s,F0[p['frame']]) for p,s in zip(a,ss)};rows=[]
 for r,fn,pair in zip(load(OUT/'interfaces.json')['rolls'],['ROOT','SHOULDER_ABDUCT','ELBOW_OUTPUT'],[('S2-P001','S2-P004'),('S2-P002','S2-P006'),('S2-P003','S2-P008')]):
  W=np.array(r['W']);iw=np.linalg.inv(W);body=moved(S[fn],iw);cover=moved(S[r['keeper']],iw);washer=moved(S[r['anchor']],iw)
  travel=np.linspace(-24,0,97);closed=[(washer.translate([0,0,float(z)])^(body+cover)).volume() for z in travel];open_=[(washer.translate([0,0,float(z)])^body).volume() for z in travel]
  assert max(closed)>1 and max(open_)<.02
  rows.append(dict(old_parts=list(pair),frame=r['fixed_frame'],decision='KEEP_SEPARATE_FOR_METAL_INSERTION_AND_RETENTION',nominal_cover_aperture_mm=16.4,captive_washer_OD_mm=18.,fused_cover_washer_entry_max_overlap_mm3=max(closed),cover_removed_washer_entry_max_overlap_mm3=max(open_),relative_motion_after_locking=False,reason='The lid is an assembly closure and positive axial stop. Fixed after assembly does not mean removable closure is redundant. Side-loading or embedded-metal printing would require a different retention and manufacturing process.'))
 olda=load(R2/'production_assembly.json')['parts'];oldz=np.load(R2/'production_meshes.npz');by={p['name']:p for p in olda}
 def old(name):
  p=by[name];i=str(p['i']);return md.Manifold(md.Mesh64(np.array(oldz[i+'v'],copy=True),np.array(oldz[i+'f'],dtype=np.uint64,copy=True)))
 fused=ss[next(i for i,p in enumerate(a) if p['name']=='KEEP_E-P018')]
 visible=box([-50,-50,-60],[50,50,-32]);functional=box([-50,-50,-20],[50,50,30]);original_palm=old('KEEP_E-P017');original_fork=old('KEEP_E-P018')
 symmetric=lambda x,y:float((x-y).volume()+(y-x).volume())
 palm_delta=symmetric(fused^visible,original_palm^visible);wrist_delta=symmetric(fused^functional,original_fork^functional)
 rows.append(dict(old_parts=['S2-P010','S2-P011'],new_part='S4-P010',frame='l_wrist_deviation',decision='MERGE_CONTINUOUS_PRINT',relative_motion_after_locking=False,removed_metal=['M2x20 x1','W2 x2','NL2 x1'],palm_visible_region_below_z_minus32_symmetric_volume_mm3=palm_delta,wrist_functional_region_above_z_minus20_symmetric_volume_mm3=wrist_delta,reason='No retained washer or later assembly requires this split. One continuous neck replaces the square socket and cross-bolt; the complete fork-and-hand is inserted in the same wrist assembly step.'))
 # Inherited printed-side-load comparison is explicitly scoped to unchanged P007.
 kit=load(OUT/'kit.json');oldkit={p['part_number']:p for p in load(R2/'kit.json')['structural_parts']};reuse=[]
 for p in kit['structural_parts']:
  if p.get('source_r2_print'):
   oldp=oldkit[p['source_r2_print']];same=sha(OUT/p['stl'])==sha(R2/oldp['stl']);assert same;reuse.append(dict(old=p['source_r2_print'],new=p['part_number'],stl_sha256=sha(OUT/p['stl']),byte_identical=True))
 groups=defaultdict(list)
 for p in olda:
  if p['role']=='structure':groups[p['frame']].append(p['part_number'])
 candidates=[x for x in groups.values() if len(x)>1];assert len(candidates)==4 and len(reuse)==10
 # Access to the retained wrist magnet seat from +Y remains open after merging.
 mp=np.array([-12.5,0,-16]);mag=cyl(mp+[0,-1.5,0],mp+[0,1.5,0],3);vols=[(mag.translate([0,float(d),0])^fused).volume() for d in np.linspace(30,0,121)];assert max(vols)<.02
 data=dict(status='PASS_MERGE_REVIEW',geometry_sha256=sha(OUT/'production_meshes.npz'),all_same_frame_print_groups_in_R2=candidates,reviewed_fixed_pairs=rows,reused_prints=reuse,required_reprint=['S4-P010'],retired_prints=['S2-P010','S2-P011'],magnet_entry_max_overlap_mm3=max(vols),parts_before=12,parts_after=11,hardware_before=134,hardware_after=130,seven_dof_retained=PROFILE==load(R2/'profiles/arm_profile.json'),scope='Every same-frame printed pair in the R2 arm reviewed. No load-carrying closure is removed solely because it is fixed after assembly. Quantitative clearance results are nominal geometry, not physical strength or fatigue.')
 put(OUT/'verification/merge_review.json',data);print('MERGE REVIEW',len(rows),'fixed pairs; reprint only S4-P010; reused',len(reuse),'magnet entry',max(vols),'surface deltas',palm_delta,wrist_delta,flush=True)
if __name__=='__main__':main()
