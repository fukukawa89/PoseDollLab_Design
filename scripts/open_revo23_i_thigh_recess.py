"""Open the microscopic outlet of a new nonfunctional fairing recess."""
from export_revo23_i import *

key='frame/thigh_r';parts,p,cfg=load_i();source=parts[key]['s'];old=h_part(key)
z=np.load(IROOT/'thigh_r_microcavity.npz');cavity=solid(z['v'],z['f'])
assert (cavity^functional_voids(key)).volume()<.001
v=vf(cavity)[0];offsets=np.array(list(itertools.product((-.25,.25),repeat=3)))
v=(v[:,None,:]+offsets).reshape(-1,3);bb=np.array(source.bounding_box());candidates=[]
for direction in [np.array(d,float)for d in ((-1,0,0),(0,-1,0),(0,1,0),(1,0,0),(0,0,-1),(0,0,1))]:
    corners=np.array(list(itertools.product(*zip(bb[:3],bb[3:]))));distance=max(corners@direction)-min(v@direction)+2
    channel=md.Manifold.hull_points(np.vstack([v,v+direction*distance]));candidate=source-(channel-old)
    missing=max(0.,(old-candidate).volume());added=max(0.,(candidate-source).volume());removed=max(0.,(source-candidate).volume())
    if missing>.01 or added>.01:continue
    candidates.append((removed,direction,channel,candidate))
for removed,direction,channel,candidate in sorted(candidates,key=lambda r:r[0]):
    cv,cf=vf(candidate.simplify(1e-4));mesh,report=quantized_cleanup(cv,cf)
    stats=common.exporter.mesh_stats(mesh)
    if not stats['watertight']or stats['degenerate_faces']or len(mesh.split(only_watertight=False))!=1:continue
    target=IROOT/(key.replace('/','__')+'.npz');save_s(IROOT/'thigh_r_before_vent.npz',source);save_s(target,candidate)
    record=i_records(key);record.update(candidate_sha256=sha(target),fairing_recess_vent=dict(direction_body=direction,opening_expansion_mm=.25,removed_added_material_mm3=removed,old_core_missing_mm3=max(0.,(old-candidate).volume()),added_relative_to_previous_mm3=max(0.,(candidate-source).volume())))
    put(target.with_suffix('.json'),record);save_s(IROOT/'thigh_r_recess_vent.npz',channel)
    stage_i();print('OPEN RECESS',removed,direction,sha(IROOT/'assembly.npz'),flush=True);break
else:raise RuntimeError('No clean outlet without altering the retained core')
