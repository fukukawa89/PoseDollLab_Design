"""Single-joint hollow spanner access; excludes hands and installed multi-axis links."""
from pathlib import Path
import argparse,hashlib,json,sys
import cadquery as cq
R=Path(__file__).resolve().parents[4];H=R/'Hardware/PoseDoll44'
sys.path.insert(0,str(H/'cad/revO3'))
from compact_joint import ring,cyl
from thread_geometry import overlap_volume
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True);results=[]
 for family,folder,ro,ri,pin_r,pin_x,pin_depth in [('L6','joint_L6_validated',12.5,4.2,.8,10.5,1.4),('M4','joint_M4_validated',8.5,2.2,.55,7.2,1.1)]:
  src=H/'generated/revO6/runs/o6_20260924_r1'/folder;m=json.loads((src/'manifest.json').read_text());inputs={str((src/'manifest.json').relative_to(R)).replace('\\','/'):sha(src/'manifest.json')};parts={}
  for r in m['parts']:
   p=src/r['step_file'];assert sha(p)==r['step_sha256'];inputs[p.relative_to(R).as_posix()]=sha(p);parts[r['part_id']]=cq.importers.importStep(str(p)).val()
  back=parts['threaded_adjuster_cap'].BoundingBox().zmin
  tool=ring(ro,ri,back-12,back)
  for x in (-pin_x,pin_x):tool=tool.fuse(cyl(pin_r,back,back+pin_depth).translate((x,0,0)))
  assert tool.isValid() and len(tool.Solids())==1
  cq.exporters.export(tool,str(a.out/(family+'_hollow_pin_spanner.step')))
  removed=[n for n in parts if n.startswith('output_') or n in ('taper_output_hub','cap_lock_dog_screw')]
  remaining={n:s for n,s in parts.items() if n not in removed};cases=[]
  for dz in (30,20,10,5,2,1,.5,.1,0):
   t=tool.translate((0,0,-dz));hits=[]
   for n,s in remaining.items():
    v=overlap_volume(t,s)
    if v>1e-4:hits.append({'part':n,'volume_mm3':v})
   cases.append({'approach_mm':dz,'intersections':hits})
  result={'family':family,'removed_for_service':removed,'tool_geometry':{'body_OD_mm':ro*2,'through_bore_mm':ri*2,'pin_radius_mm':pin_r,'pin_radius_from_axis_mm':pin_x},'cases':cases,'status':'FAIL' if any(x['intersections'] for x in cases) else 'PASS_SINGLE_JOINT_AXIAL_APPROACH','scope':'Nominal adjuster position; output/yoke and locking dog removed. No hand envelope, wrench handle, adjacent joints, turning sweep, strength or supplier tool rating.','input_sha256':inputs,'physical_tested':False};results.append(result);print(family,result['status'],flush=True)
 paths=[Path(__file__),H/'cad/revO6/thread_geometry.py',H/'cad/revO3/compact_joint.py']
 (a.out/'service.json').write_text(json.dumps({'families':results,'input_sha256':{p.relative_to(R).as_posix():sha(p) for p in paths},'physical_tested':False,'manufacturing_released':False},indent=2)+'\n')
if __name__=='__main__':main()

