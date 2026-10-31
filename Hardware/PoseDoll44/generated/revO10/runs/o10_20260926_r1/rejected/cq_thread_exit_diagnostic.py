"""M3 reference mating threads with actual overlap under axial escape attempts."""
from pathlib import Path
import sys,json,hashlib,numpy as np,cadquery as cq
H=Path(__file__).resolve().parents[2];OUT=H/'generated/revO10/runs/o10_20260926_r1'
sys.path.insert(0,str(H/'cad/revO6'));from thread_geometry import thread_sweep,checked,RECEIPTS,overlap_volume

def cylinder(r):return cq.Workplane('XY').workplane(offset=5).circle(r).extrude(3.5).val()
def mesh(s):
 v,f=s.tessellate(.008,.045);v=np.array([x.toTuple() for x in v]);return v[np.array(f)]
def main():
 male_sweep=thread_sweep([(1.20,-.206),(1.5,-.033),(1.5,.033),(1.20,.206)],z0=5.25,height=3,pitch=.5)
 cutter=thread_sweep([(1.20,-.249),(1.55,-.048),(1.55,.048),(1.20,.249)],z0=5.25,height=4,pitch=.5)
 male=checked(cylinder(1.215),male_sweep,'fuse','M3 external reference thread')
 holder=checked(cylinder(4),cylinder(1.28),'cut','M3 female core bore');holder=checked(holder,cutter,'cut','M3 female reference groove')
 nominal=overlap_volume(male,holder);assert nominal<1e-5,nominal;pulls=[]
 for d in (-.15,.15):
  v=overlap_volume(male.translate((0,0,d)),holder);assert v>.05;pulls.append({'axial_translation_mm':d,'intersection_mm3':v})
 withdrawal=[]
 for d in (0,.25,.5,1,2,3,3.5):
  moved=male.rotate((0,0,0),(0,0,1),720*d).translate((0,0,d));v=overlap_volume(moved,holder);withdrawal.append({'outward_mm':d,'rotation_deg':720*d,'intersection_mm3':v});assert v<1e-5,withdrawal[-1]
 dest=OUT/'face_brake';np.savez_compressed(dest/'threads.npz',male=mesh(male),cutter=mesh(cutter));cq.exporters.export(male,str(dest/'M3_male_reference.step'));cq.exporters.export(holder,str(dest/'M3_female_reference_coupon.step'))
 (dest/'threads.json').write_text(json.dumps({'pitch_mm':.5,'nominal_engagement_mm':3.5,'full_male_helix_height_mm':3,'female_cut_helix_height_mm':4,'helical_withdrawal':withdrawal,'nominal_intersection_mm3':nominal,'axial_escape_checks':pulls,'volume_guards':RECEIPTS,'scope':'Actual nominal reference helices and axial retention example. Not an ISO fit-class, torque-to-preload, stripping/fatigue or production tapping approval.','generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'manufacturing_released':False},indent=2)+'\n');print('THREADS',nominal,pulls,flush=True)
if __name__=='__main__':main()

