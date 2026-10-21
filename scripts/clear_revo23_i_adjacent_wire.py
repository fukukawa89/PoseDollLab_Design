"""Keep the left upper-arm cable envelope clear of the new chest fairing."""
from revo23_unified import *

parts,p,cfg=load_i();key='frame/chest';old=h_part(key);source=parts[key]['s']
seat=next(r for r in read(IROOT/'harness/wire_seats.json')['seats']if r['id']=='upperarm_l:tie2')
pose=read(IROOT/'profiles/daily_poses.json')['poses']['clavicle_l.elevate.elevate@-15'];F=frames(p,pose)
W=np.array(seat['transform_body_mm']);W[:3,3]=seat['wire_center_body_mm']
w,h=seat['reserved_channel_width_mm'],seat['reserved_channel_height_mm'];margin=.25
keepout=move(box([-w/2-margin,-h/2-margin,-6-margin],[w/2+margin,h/2+margin,6+margin]),np.linalg.inv(F[parts[key]['token']])@F[seat['token']]@W)
# The extra margin can touch the retained carrier; cut added fairing only.
candidate=source-(keepout-old)
missing=max(0.,(old-candidate).volume());added=max(0.,(candidate-source).volume())
assert missing<.01 and added<.01
save_s(IROOT/'chest_adjacent_wire_clear_candidate.npz',candidate)
put(IROOT/'chest_adjacent_wire_clear_candidate.json',dict(part=key,pose='clavicle_l.elevate.elevate@-15',seat=seat['id'],extra_clearance_mm=margin,
    old_core_removed_mm3=missing,added_mm3=added,removed_added_material_mm3=max(0.,(source-candidate).volume())))
print('WIRE RELIEF',read(IROOT/'chest_adjacent_wire_clear_candidate.json'),flush=True)
