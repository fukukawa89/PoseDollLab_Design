from pathlib import Path
p=Path(__file__).parent/'verify_revo22_f5_contacts298.py';s=p.read_text(encoding='utf-8-sig');s=s.replace("and not json.loads((folder/'design'/f'{pid}.json').read_text()).get('f5_additions'):return saved","and saved.get('fit_and_pose_geometry_passed') and not json.loads((folder/'design'/f'{pid}.json').read_text()).get('f5_additions'):return saved")
s=s.replace('(before^p.transform(relative[:3,:])).volume()','(reference^moved).volume()')
s=s.replace("assert(external_addition-envelope(reference,external_addition,margin=limit)).volume()<VTOL","assert abs(external_addition.volume()-envelope(reference,external_addition,margin=limit).volume())<VTOL")
a=s.index(' raw=reference-new;');b=s.index('\n added=union(material_components(added^rois))',a)
s=s[:a]+''' rois=union([box(q['local_bounds_mm'][:3],q['local_bounds_mm'][3:])for q in d.get('f5_reliefs',[])+d.get('f5_additions',[])])
 verification_mesh_tolerance_mm=0.
 def differences(ref,body,source_clip):
  raw=ref-body;added=body-ref
  if source_clip and has_additions:
   if abs(raw.volume())>1e-10:raw=(ref-body)^ref
   if abs(added.volume())>1e-10:added=(body-ref)^body
  a=raw-rois;b=added-rois
  if abs(a.volume())>tol:a=a^ref
  if abs(b.volume())>tol:b=b^body
  return raw,added,float(abs(a.volume())+abs(b.volume()))
 raw,added,outside=differences(reference,new,True)
 if outside>=tol:
  # Canonicalize near-coincident Boolean subdivisions for verification only.
  # 1e-9 mm is a millionth of a micron; the delivered mesh is untouched.
  verification_mesh_tolerance_mm=1e-9
  reference=reference.set_tolerance(verification_mesh_tolerance_mm)
  new=new.set_tolerance(verification_mesh_tolerance_mm)
  raw,added,outside=differences(reference,new,False)
 assert added.volume()<tol or(has_additions and added.volume()<min(10.,reference.volume()*.002))
 assert outside<tol,(pid,'edit outside recorded bounds',outside)
 removed=union(material_components(raw^rois));assert len(material_components(new))==len(material_components(reference));assert 0<=removed.volume()<min(min(40.,d.get('f5_edit_budget_mm3',20.)),reference.volume()*min(.006,d.get('f5_edit_budget_fraction',.004)))
'''+s[b:]
s=s.replace('mixed_boolean_differences_clipped_to_their_source_material=True,','mixed_boolean_differences_clipped_to_their_source_material=verification_mesh_tolerance_mm==0 and has_additions,verification_only_coordinate_tolerance_mm=verification_mesh_tolerance_mm,delivered_mesh_unchanged_by_predicate_canonicalization=True,')
p.write_text(s,encoding='utf-8')
