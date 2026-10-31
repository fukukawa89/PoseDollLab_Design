"""Restore clearance exposed by the independent post-trim fixed-mate check."""
from build_revo23_wire_seats import *
from build_revo23_reinforced import padded_hull
from audit_revo23_load_paths import screen

parts,p,cfg=load_e();base,_,_=load_d();F=frames(p,p['neutral_raw_deg'])
key='frame/clavicle_r';mate='clavicle_r.elevate/magnet_cartridge'
host=parts[key]['s'];native=move(parts[mate]['s'],np.linalg.inv(F[parts[key]['token']])@F[parts[mate]['token']])
hit=host^native
if hit.volume()>.01:
    cutter=(padded_hull(native,.2)^padded_hull(hit,.8))-base[key]['s']
    result=host-cutter
    v,f=vf(result);result=solid(v,f)
    assert max(0.,(result^native).volume())<.01
    assert len([c for c in result.decompose() if c.volume()>.001])==1
    path=EROOT/'frame__clavicle_r.npz'
    backup=EROOT/'checkpoints/before_final_magnet_clearance';backup.mkdir(parents=True,exist_ok=True)
    if not (backup/path.name).exists():shutil.copy2(path,backup/path.name)
    np.savez_compressed(path,v=v,f=f)
    kz=np.load(DHISTORY/'source/retained_interfaces.npz')
    audit=screen(key,result,solid(kz[key+'|v'],kz[key+'|f']),local_skin(key,p,cfg),1.)
    audit['candidate_mesh_sha256']=sha(path)
    put(EROOT/'load_paths_candidate/frame__clavicle_r.json',audit)
    put(EROOT/'final_magnet_clearance.json',dict(part=key,mate=mate,
        before_mm3=hit.volume(),after_mm3=max(0.,(result^native).volume()),
        removed_mm3=host.volume()-result.volume(),D_material_removed_mm3=max(0.,((host-result)^base[key]['s']).volume())))
print('FINAL MAGNET CLEARANCE',hit.volume(),flush=True)
