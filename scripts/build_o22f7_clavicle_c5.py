"""C5: compact single-bolt keyed overlap close to the original beam envelope."""
from o22f7_animation import *
from build_revo22_assembly import b
import o22f7_native as h
C=WORK/'structure_revision';x=Build();x.begin(x.g['steps'][3]);I=np.linalg.inv(x.mount)
def freeze(s):
 s.volume();return b.b.from_tri_exact(b.g.tri(s))
def shape(k):
 o=x.obs[k];m=x.scene['meshes'][o['mesh']];return b.g.move(b.b.from_tri_exact(x.verts[m['first']:m['first']+m['count'],:3].reshape(-1,3,3)),I@x.mats[k])
original=freeze(shape('frame/clavicle_l.protract_frame'));root_region=freeze(b.b.box([-200,-200,-200],[14,200,200])+b.b.box([14,-20,2.5],[22,20,20]));root=freeze(original^root_region);distal=freeze(original-root)
root=freeze(root+b.b.cyl(3.5,2.5,6.8).translate([17,0,0]));distal=freeze(distal+b.b.cyl(2.2,-1.5,2.5).translate([17,0,0]));distal=freeze(distal-root)
key=freeze(b.b.box([19.5,-2.5,1.3],[21,2.5,2.6])^original);root=freeze(root+key);distal=freeze(distal-b.b.box([19.3,-2.7,1.1],[21.2,2.7,2.7]));hole=b.b.cyl(1.15,-30,30).translate([17,0,0]);root=freeze(root-hole);distal=freeze(distal-hole);root=freeze(root-b.b.hexagon(4.3,4.7,15).translate([17,0,0]));distal=freeze(distal-b.b.cyl(2.1,-60,-1.49).translate([17,0,0]));combined=freeze(root+distal);added=freeze(combined-original);removed=freeze(original-combined)
stock={'nut_0':b.b.nut(2,4,1.6,4.8).translate([17,0,0]),'screw_0':b.b.screw(2,8,3.8,2,0).rotate([180,0,0]).translate([17,0,-1.5])}
ds=h.material_components(distal);assert len(ds)==1;distal=freeze(ds[0]);assert root.volume()>3000 and len(h.material_components(root))==1
assert(root^distal).volume()<1e-6
root_guard=b.b.cyl(12,-3,16);assert(removed^root_guard).volume()<1e-5 and(added^root_guard).volume()<1e-5
checks=[];allshape=freeze(combined+stock['nut_0']);allshape=freeze(allshape+stock['screw_0']);bb=np.array(allshape.bounding_box())
for k in x.obs:
 if k=='frame/clavicle_l.protract_frame':continue
 s=shape(k);bo=np.array(s.bounding_box())
 if np.any(np.minimum(bb[3:],bo[3:])<=np.maximum(bb[:3],bo[:3])+1e-7):continue
 v=max(0.,float((allshape^s).volume()));old=max(0.,float((original^s).volume()))
 if v>old+.001:checks.append({'part':k,'candidate_overlap_mm3':v,'original_overlap_mm3':old})
np.savez_compressed(C/'W005_C5.npz',root=b.g.tri(root),distal=b.g.tri(distal),added=b.g.tri(added),removed=b.g.tri(removed),**{k:b.g.tri(s) for k,s in stock.items()})
rec={'status':'CANDIDATE_NOT_RELEASED','root_volume':root.volume(),'distal_volume':distal.volume(),'added_mm3':added.volume(),'removed_mm3':removed.volume(),'new_static_conflicts':checks,'hardware':['M2x8 socket-head screw, 1','M2 nut, 1'],'key_clearance_mm':.2,'root_bearing_roi_unchanged':True,'physical_strength_tested':False};put(C/'W005_C5_geometry_review.json',rec);print(rec,flush=True)

