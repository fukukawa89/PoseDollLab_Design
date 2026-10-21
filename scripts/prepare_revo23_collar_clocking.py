"""Preserve unaffected validated solids while reorienting both collar mounts."""
from build_revo23_continuous import *
import center_revo23_torso
import mirror_revo23_right_wrist

angle=center_revo23_torso.COLLAR_CLOCK_DEG
fit=read(B/'verification'/f'collar_clock_{angle:g}.json')
assert fit['passed'] and not fit['static_contacts']
source=DROOT/'source';checkpoint=DROOT/'checkpoints'/f'before_collar_clock_{angle:g}'
assert not checkpoint.exists(),'Preparation checkpoint already exists; do not run twice.'
checkpoint.mkdir(parents=True)
shutil.copytree(source,checkpoint/'source')
for path in (B/'assembly.npz',B/'profiles/device_profile.json',B/'profiles/daily_poses.json'):
    shutil.copy2(path,checkpoint/path.name)
old_p=read(source/'device_profile.json');old_keep=np.load(source/'retained_interfaces.npz')
old_keep={k:old_keep[k] for k in old_keep.files}
affected={'frame/chest','frame/clavicle_l.protract_frame','frame/clavicle_r.protract_frame'}
for key in affected:
    for suffix in ('.json','.npz'):
        path=DROOT/(key.replace('/','__')+suffix)
        shutil.copy2(path,checkpoint/path.name)
center_revo23_torso.main()
p=read(source/'device_profile.json')
old_cuts=np.load(checkpoint/'source/interface_edge_reliefs.npz')
filtered={k:old_cuts[k] for k in old_cuts.files if k.rsplit('|',1)[0] not in affected}
np.savez_compressed(source/'interface_edge_reliefs.npz',**filtered)
meta=read(checkpoint/'source/interface_edge_reliefs.json')
meta['profile_sha256']=profile_signature(p)
meta['rows']=[r for r in meta['rows'] if r['key'] not in affected]
meta['note']='Affected collar/chest lands rebuilt and rechecked; old cuts there are not transferred to the new orientation.'
put(source/'interface_edge_reliefs.json',meta)
mirror_revo23_right_wrist.main()
new=np.load(source/'retained_interfaces.npz');merged={k:new[k] for k in new.files}
for key in old_keep:
    if key.rsplit('|',1)[0] not in affected:merged[key]=old_keep[key]
np.savez_compressed(source/'retained_interfaces.npz',**merged)
meta['approved_keeps_sha256']=sha(source/'retained_interfaces.npz');put(source/'interface_edge_reliefs.json',meta)
spec=read(B/'profiles/daily_poses.json');spec['profile_sha256']=sha(source/'device_profile.json')
put(B/'profiles/daily_poses.json',spec)
error=0.
for q in spec['poses'].values():
    a=frames(old_p,q);b=frames(p,q)
    error=max(error,max(np.max(abs(a[k]-b[k])) for k in a if k.startswith('f:')))
assert error<1e-8,error
for path in DROOT.glob('frame__*.json'):
    r=read(path)
    if r['key'] in affected:continue
    shutil.copy2(path,checkpoint/path.name)
    r['validated_profile_sha256']=profile_signature(p)
    r['validated_keeps_sha256']=sha(source/'retained_interfaces.npz')
    r['validated_pose_sha256']=sha(B/'profiles/daily_poses.json')
    r['collar_clocking_reuse']=dict(body_frame_maximum_error=error,own_keeper_unchanged=True,
        note='Only two native collar modules and their three structural lands move. Unchanged carriers require final actual-solid collision checks with those neighbours.')
    put(path,r)
put(source/'collar_clocking.json',dict(angle_deg=angle,affected_structures=sorted(affected),
    body_frame_maximum_error=error,poses=len(spec['poses']),manufacturing_release=False))
print('COLLAR SOURCE PREPARED',error,flush=True)
