"""Independent keyed lap candidate. No released geometry is changed."""
from o22f7_animation import *
from build_revo22_assembly import b
C=WORK/'structure_revision';x=Build();x.begin(x.g['steps'][3]);I=np.linalg.inv(x.mount)
def shape(k):
 o=x.obs[k];m=x.scene['meshes'][o['mesh']];return b.g.move(b.b.from_tri_exact(x.verts[m['first']:m['first']+m['count'],:3].reshape(-1,3,3)),I@x.mats[k])
original=shape('frame/clavicle_l.protract_frame');fixed={k:shape(k) for k in x.obs if k!='frame/clavicle_l.protract_frame'};bounds={k:np.array(s.bounding_box()) for k,s in fixed.items()}
# Retain the complete lever-cup through local x=14 and the distal functional end.
root_original=original^b.b.box([-200,-200,-200],[14,200,200]);distal_original=original-b.b.box([-200,-200,-200],[20,200,200]);rows=[]
for plane in [2.5,4.5,0.5]:
 for width in [12,10]:
  z=plane;root=root_original+b.b.box([13,-width/2,z],[33,width/2,z+5]);distal=distal_original+b.b.box([14.25,-width/2,z-5],[33,width/2,z]);distal-=root_original
  # Alignment key remains clear of the two screw bores.
  key=b.b.box([22,-3,z-1.5],[24,3,z+.1]);root+=key;distal-=b.b.box([21.8,-3.2,z-1.7],[24.2,3.2,z+.2])
  stock={}
  for j,xx in enumerate([18,29]):
   drill=b.b.cyl(1.7,z-8,z+8).translate([xx,0,0]);root-=drill;distal-=drill
   root-=b.b.hexagon(5.8,z+2.4,z+5.1).translate([xx,0,0])
   stock[f'nut_{j}']=b.b.nut(3,5.5,2.4,z+2.5).translate([xx,0,0])
   stock[f'screw_{j}']=b.b.screw(3,12,5.6,3,0).rotate([180,0,0]).translate([xx,0,z-5])
  overlap=float((root^distal).volume());added=(root+distal)-original;checks=[];bb=np.array((root+distal).bounding_box())
  for k,s in fixed.items():
   bo=bounds[k]
   if np.any(np.minimum(bb[3:],bo[3:])<=np.maximum(bb[:3],bo[:3])+1e-6):continue
   vol=float((added^s).volume())
   if vol>.001:checks.append({'part':k,'added_overlap_mm3':vol})
  rec={'plane':plane,'width':width,'root_components':b.g.solid_count(root),'distal_components':b.g.solid_count(distal),'part_overlap':overlap,'added_volume':added.volume(),'new_conflicts':checks};rows.append(rec);print(rec,flush=True)
  name=f'lap_z{plane}_w{width}';np.savez_compressed(C/(name+'.npz'),root=b.g.tri(root),distal=b.g.tri(distal),added=b.g.tri(added),**{k:b.g.tri(s) for k,s in stock.items()})
put(C/'lap_candidate_review.json',{'status':'CANDIDATE_NOT_RELEASED','coordinates':'left protract mount at S04 neutral angle','rows':rows,'physical_strength_tested':False})
