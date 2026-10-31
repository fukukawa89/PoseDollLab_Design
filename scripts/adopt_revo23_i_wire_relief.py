"""Freeze passing I checks, adopt the one chest relief, and bind local checks."""
from revo23_unified import *

baseline=IROOT/'before_adjacent_wire_relief';baseline.mkdir(exist_ok=True)
assert not (baseline/'assembly.npz').exists(),'Already adopted; do not overwrite the baseline'
digest=sha(IROOT/'assembly.npz')
for name in ('daily_motion','edge_motion','functional_voids','external_contours'):
    r=read(IROOT/(name+'.json'));assert r['passed']and r['geometry_sha256']==digest,name
for path in list(IROOT.glob('*.json'))+[IROOT/'assembly.npz']:
    shutil.copy2(path,baseline/path.name)
key='frame/chest';src=IROOT/'chest_adjacent_wire_clear_candidate.npz';target=IROOT/'frame__chest.npz'
shutil.copy2(src,target);record=i_records(key);record.update(candidate_sha256=sha(target),adjacent_wire_relief=read(src.with_suffix('.json')));put(target.with_suffix('.json'),record)
parts,p,cfg=stage_i();current=read(IROOT/'staging.json');old_stage=read(baseline/'staging.json')
assert [k for k,h in old_stage['candidate_files'].items()if current['candidate_files'][k]!=h]==[key]
proof=dict(geometry_sha256=sha(IROOT/'assembly.npz'),baseline_geometry_sha256=digest,changed_parts=[key],unchanged_parts_verified_by_sha256=True)
put(IROOT/'wire_relief_transition.json',proof)
old=h_part(key);delta=parts[key]['s']-old
path=IROOT/'functional_voids.json';r=read(path);row=next(x for x in r['rows']if x['part']==key)
row.update(removed_H_material_mm3=max(0.,(old-parts[key]['s']).volume()),added_mm3=max(0.,delta.volume()),original_functional_void_intrusion_mm3=max(0.,(delta^functional_voids(key)).volume()))
row['passed']=row['removed_H_material_mm3']<.03 and row['original_functional_void_intrusion_mm3']<.03
r.update(geometry_sha256=proof['geometry_sha256'],incremental_proof=proof,unchanged_part_report_sha256=sha(baseline/path.name),passed=all(x['passed']for x in r['rows']));put(path,r)
path=IROOT/'external_contours.json';r=read(path);row=next(x for x in r['rows']if x['part']==key);z=np.load(IROOT/'contour_guards/frame__chest.npz');guard=solid(z['v'],z['f'])
row['remaining_beyond_approved_wall_mm3']=max(0.,(delta^guard).volume());row['passed']=row['remaining_beyond_approved_wall_mm3']<.03
r.update(geometry_sha256=proof['geometry_sha256'],incremental_proof=proof,unchanged_part_report_sha256=sha(baseline/path.name),passed=all(x['passed']for x in r['rows']));put(path,r)
print('ADOPTED WIRE RELIEF',proof,flush=True)
