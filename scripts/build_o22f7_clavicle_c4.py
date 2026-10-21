"""Independent keyed lap candidate. No released geometry is changed."""
from o22f7_animation import *
from build_revo22_assembly import b
def freeze(s):
 s.volume();return b.b.from_tri_exact(b.g.tri(s))
C=WORK/'structure_revision';x=Build();x.begin(x.g['steps'][3]);I=np.linalg.inv(x.mount)
def shape(k):
 o=x.obs[k];m=x.scene['meshes'][o['mesh']];return b.g.move(b.b.from_tri_exact(x.verts[m['first']:m['first']+m['count'],:3].reshape(-1,3,3)),I@x.mats[k])
original=shape('frame/clavicle_l.protract_frame');fixed={k:shape(k) for k in x.obs if k!='frame/clavicle_l.protract_frame'};bounds={k:np.array(s.bounding_box()) for k,s in fixed.items()}
# Retain the complete lever-cup through local x=14 and the distal functional end.
root_original=freeze(original^b.b.box([-200,-200,-200],[14,200,200]));distal_original=freeze(original-b.b.box([-200,-200,-200],[20,200,200]));rows=[]
for plane in [2.5]:
 for width in [8]:
  z=plane;root=freeze(root_original+b.b.box([13,-width/2,z],[27,width/2,z+5]));distal=freeze(distal_original+b.b.box([14.25,-width/2,z-5],[27,width/2,z]));distal=freeze(distal-root)
  # Alignment key remains clear of the two screw bores.
  key=b.b.box([19,-2.5,z-1.2],[21,2.5,z+.1]);root=freeze(root+key);distal=freeze(distal-b.b.box([18.8,-2.7,z-1.4],[21.2,2.7,z+.2]))
  stock={}
  for j,xx in enumerate([17,23]):
   drill=b.b.cyl(1.15,z-8,z+8).translate([xx,0,0]);root=freeze(root-drill);distal=freeze(distal-drill);distal=freeze(distal-b.b.cyl(2.1,z-70,z-4.99).translate([xx,0,0]))
   root=freeze(root-b.b.hexagon(4.3,z+3.2,z+5.1).translate([xx,0,0]))
   stock[f'nut_{j}']=b.b.nut(2,4,1.6,z+3.3).translate([xx,0,0])
   stock[f'screw_{j}']=b.b.screw(2,10,3.8,2,0).rotate([180,0,0]).translate([xx,0,z-5])
  overlap=float((root^distal).volume());combined=freeze(root+distal);guard=b.b.cyl(12,-3,16);assert ((original-combined)^guard).volume()<1e-5;assert ((combined-original)^guard).volume()<1e-5;assert root.volume()>3000;added=freeze(combined-original);checks=[];bb=np.array((root+distal).bounding_box())
  for k,s in fixed.items():
   bo=bounds[k]
   if np.any(np.minimum(bb[3:],bo[3:])<=np.maximum(bb[:3],bo[:3])+1e-6):continue
   vol=float((added^s).volume())
   if vol>.001:checks.append({'part':k,'added_overlap_mm3':vol})
  rec={'plane':plane,'width':width,'root_components':b.g.solid_count(root),'distal_components':b.g.solid_count(distal),'part_overlap':overlap,'added_volume':added.volume(),'new_conflicts':checks};rows.append(rec);print(rec,flush=True)
  name='W005_C4';np.savez_compressed(C/(name+'.npz'),root=b.g.tri(root),distal=b.g.tri(distal),added=b.g.tri(added),**{k:b.g.tri(s) for k,s in stock.items()})
put(C/'W005_C4_geometry_review.json',{'status':'CANDIDATE_NOT_RELEASED','coordinates':'left protract mount at S04 neutral angle','rows':rows,'physical_strength_tested':False})



