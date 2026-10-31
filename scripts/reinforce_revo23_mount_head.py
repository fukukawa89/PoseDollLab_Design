"""Replace a clipped thin carrier remnant with a continuous flat mounting head.

The original carrier and holes are retained. Added material is confined to its
convex envelope, and a planar rear relief protects the controller box.
"""
from repair_revo23_endfaces import *

parts,p,cfg=load_h();N=frames(p,p['neutral_raw_deg']);key='frame/clavicle_l.protract_frame';mount=1
M=N[parts[key]['token']];native=native_hosts(key,parts,p,N,baseline=True)[mount]
envelope=md.Manifold.hull_points(vf(native)[0]);voids=move(wire_spaces(key),M)
space=Space(key,parts,p,N,False);bb=np.array(native.bounding_box());options=[]
for axis in range(3):
    for sign in (-1,1):
        for cut in np.arange(bb[axis]+1,bb[axis+3],1.):
            lo=bb[:3]-1;hi=bb[3:]+1
            if sign>0:lo[axis]=cut
            else:hi[axis]=cut
            candidate=native+((envelope^box(lo,hi))-voids)
            addition=candidate-native
            if addition.volume()>25:options.append((addition.volume(),axis,sign,cut,candidate,addition))
options.sort(key=lambda x:-x[0]);selected=None
for volume,axis,sign,cut,head,added in options:
    ok,why=space.clear(added)
    if ok:
        selected=(axis,sign,cut);break
assert selected is not None,'No clean planar carrier reinforcement clears all adjacent poses'
assert (added^voids).volume()<.01
assert (native-head).volume()<.0001
cc=[s for s in head.decompose() if s.volume()>.001];assert len(cc)==1
dest=HROOT/'mount_reinforcement';dest.mkdir(exist_ok=True);path=dest/(key.replace('/','__')+'.npz')
save_s(path,move(head,np.linalg.inv(M)))
record=dict(part=key,mount=mount,geometry_sha256=sha(path),source_geometry_sha256=GHASH,
    original_volume_mm3=native.volume(),reinforced_volume_mm3=head.volume(),added_volume_mm3=added.volume(),
    functional_void_overlap_mm3=(added^voids).volume(),all_adjacent_poses_clear=ok,
    original_material_retained=True,planar_relief=dict(axis=int(selected[0]),sign=int(selected[1]),coordinate_mm=float(selected[2])),method='Convex native carrier envelope with one planar clearance relief; original functional apertures retained. No rod is clipped or notched.')
put(path.with_suffix('.json'),record);print(record,flush=True)
