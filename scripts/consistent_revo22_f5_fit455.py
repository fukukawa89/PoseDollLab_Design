from pathlib import Path
p=Path(__file__).parent/'verify_revo22_f5_contacts298.py';s=p.read_text(encoding='utf-8-sig')
s=s.replace('raw=(reference-new).as_original();added=(new-reference).as_original()','raw=reference-new;added=new-reference')
s=s.replace('if has_additions and abs(raw.volume())>VTOL and abs(added.volume())>VTOL:\n  raw=(raw^reference).as_original();added=(added^new).as_original()', 'if has_additions:\n  if abs(raw.volume())>1e-10:raw=(reference-new)^reference\n  if abs(added.volume())>1e-10:added=(new-reference)^new')
a="outside=float((raw-rois).volume()+abs((added-rois).volume()));assert abs(outside)<tol"
b="outside_raw=raw-rois;outside_added=added-rois;outside_raw=outside_raw^reference if abs(outside_raw.volume())>tol else outside_raw;outside_added=outside_added^new if abs(outside_added.volume())>tol else outside_added;outside=float(abs(outside_raw.volume())+abs(outside_added.volume()));assert abs(outside)<tol"
assert a in s;s=s.replace(a,b)
s=s.replace('relative_cache[ck]=(changed,bi,ai)',"global_bi=float(max(0.,(before^p.transform(relative[:3,:])).volume())) if changed>VTOL and bi<.01 else bi\n    relative_cache[ck]=(changed,bi,ai,global_bi)")
s=s.replace('changed,bi,ai=relative_cache[ck];q=dict(', 'changed,bi,ai,global_bi=relative_cache[ck];q=dict(before_full_intersection_for_pose_validity_mm3=global_bi,')
s=s.replace("(has_additions and name!='base' and bi>=.01)","(has_additions and name!='base' and global_bi>=.01)")
s=s.replace('if bi>=.01:preexisting.append(q)','if global_bi>=.01:preexisting.append(q)')
p.write_text(s,encoding='utf-8')
