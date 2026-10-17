"""C7: recess the joint screw and relieve only added boss material."""
from pathlib import Path
src=Path('scripts/check_o22f7_clavicle_c5_function.py').read_text('utf-8-sig');exec(src.split('cache={};new_hits=')[0])
raws=dict(poses);cuts=[]
for issue in read(C/'W005_C5_contact_components.json')['rows']:
 if issue['details']['added']['overlap']<.001:continue
 raw=raws[issue['pose']];ff,oo=kin.owners(raw);t=owners[issue['part']];od=(ff[t[1]] if t[0]=='f' else oo[t[1:]])@inverse0[t];own=ff['clavicle_l.protract_frame']@invown;obs=b.g.move(world[issue['part']],I@np.linalg.inv(own)@od);bb=np.array(new['added'].bounding_box());crop=obs^b.b.box(bb[:3]-.3,bb[3:]+.3);v=np.array(crop.to_mesh64().vert_properties)[:,:3];offsets=np.array(list(itertools.product([-.12,.12],repeat=3)));cut=b.b.md.Manifold.hull_points((v[:,None]+offsets).reshape(-1,3));cuts.append(cut)
union=b.b.md.Manifold.batch_boolean(cuts,b.b.md.OpType.Add);removed_new=freeze(new['added']^union);root=freeze(new['root']-union);distal=freeze(new['distal']-b.b.cyl(2.1,-60,.5).translate([17,0,0]));screw=b.b.screw(2,6,3.8,2,0).rotate([180,0,0]).translate([17,0,.5]);nut=b.b.nut(2,4,1.6,4.7).translate([17,0,0]);distal=freeze(distal-b.b.box([13.99,-20,-100],[14.2,20,2.5]));distal=freeze(distal-b.b.box([22,-20,2.5],[22.2,20,20]));combined=freeze(root+distal)
# Limit added-material extraction to the small edit envelope; all remote surfaces
# are inherited. This avoids false near-coincident shells after world transforms.
editbox=b.b.box([12,-5,-25],[32,16,12]);orig_local=original
added=freeze(freeze(new['added']^root)+freeze(new['added']^distal));removed=freeze((orig_local-combined)^editbox)
assert root.volume()>3000 and b.g.solid_count(root)==1
import o22f7_native as h
assert len(h.material_components(distal))==1 and(root^distal).volume()<1e-6
print('removed new boss',removed_new.volume(),'nut gap',removed_new.min_gap(nut,1),'root volume',root.volume(),flush=True)
foot=b.b.hexagon(4,4.69,4.7).translate([17,0,0])-b.b.cyl(1.15,4.68,4.71).translate([17,0,0]);nut_area=(root^foot).volume()/.01;nut_expected=foot.volume()/.01
foot=(b.b.cyl(1.9,.5,.51)-b.b.cyl(1.15,.49,.52)).translate([17,0,0]);head_area=(distal^foot).volume()/.01;head_expected=foot.volume()/.01
assert nut_area/nut_expected>.99 and head_area/head_expected>.99
clamp_area=(root.slice(2.50001)^distal.slice(2.49999)).area();print('clamp',clamp_area,'nut',nut_area/nut_expected,'head',head_area/head_expected,flush=True)
np.savez_compressed(C/'W005_C7.npz',root=b.g.tri(root),distal=b.g.tri(distal),added=b.g.tri(added),removed=b.g.tri(removed),nut_0=b.g.tri(nut),screw_0=b.g.tri(screw))
put(C/'W005_C7_geometry_review.json',{'status':'CANDIDATE_NOT_RELEASED','nut_bearing_area_mm2':nut_area,'head_bearing_area_mm2':head_area,'nut_bearing_fraction':nut_area/nut_expected,'head_bearing_fraction':head_area/head_expected,'clamp_contact_area_mm2':clamp_area,'end_face_clearance_mm':.2,'source_candidate_sha256':sha(C/'W005_C5.npz'),'new_boss_relief_mm3':float(removed_new.volume()),'relief_to_nut_gap_mm_capped_at_1':float(removed_new.min_gap(nut,1)),'hardware':['M2x6 socket-head screw, 1','M2 nut, 1'],'head_seat_local_z':.5,'distal_clamp_web_mm':2.0,'root_clamp_web_mm':2.2,'registered_clamp_plane_local_z':2.5,'key_clearance_mm':.2,'stock_head_geometry_unchanged':True,'head_moved_into_counterbore_mm':2,'physical_strength_tested':False})

