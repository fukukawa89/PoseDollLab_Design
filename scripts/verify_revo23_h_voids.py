"""Compare added H material with the G print package's frozen small-hole masks."""
from revo23_endfaces import *

parts,p,cfg=load_h();old=np.load(GHISTORY/'assembly.npz');rows=[]
(HROOT/'void_intrusions').mkdir(exist_ok=True)
source=B/'print_optimization_G/guards_v5'
for r in read(B/'design/export_repair_G/repair.json')['rows']:
    key=r['key'];i=str(parts[key]['index']);original=solid(old[i+'v'],old[i+'f']);added=parts[key]['s']-original
    path=source/(r['id']+'.npz');z=np.load(path);guard=solid(z['v'],z['f']);hit=added^guard;vol=max(0.,hit.volume())
    row=dict(part=key,id=r['id'],added_material_in_existing_small_holes_or_wiring_mm3=vol,
        guard_sha256=sha(path),passed=vol<.03,hit_bounds_body_mm=None if hit.is_empty() else hit.bounding_box())
    if vol>.03:save_s(HROOT/'void_intrusions'/(key.replace('/','__')+'.npz'),hit)
    rows.append(row);print('VOID',key,round(vol,5),row['passed'],flush=True)
put(HROOT/'functional_voids.json',dict(rows=rows,passed=all(r['passed']for r in rows),baseline_geometry_sha256=GHASH,geometry_sha256=sha(HROOT/'assembly.npz'),
    scope='Added material checked against the frozen G v5 small closed-aperture and exact wire masks. Any hit requires feature-level inspection; large open assembly/tool-access recesses require separate visual review.'))
