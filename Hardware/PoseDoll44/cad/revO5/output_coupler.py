"""O5 output retention candidate and tool-clearance experiment, not a released joint.
An O3 shaft has only a short rear land. Preserve the O3 file; explicitly measure
what an extended D shaft and split collar cost before embedding it in the arm.
"""
from pathlib import Path
import argparse,json,hashlib,math
import cadquery as cq
ROOT=Path(__file__).resolve().parents[4];HW=ROOT/'Hardware/PoseDoll44'
def box(x,y,z,c):return cq.Workplane('XY').box(x,y,z).translate(c).val()
def cyl(r,a,b):return cq.Solid.makeCylinder(r,b-a,cq.Vector(0,0,a))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 original=HW/'generated/revO3/runs/o3_20260924_r3/joint';manifest_hash=sha(original/'manifest.json');manifest=json.loads((original/'manifest.json').read_text());consumed={}
 def load(name):
  row=next(p for p in manifest['parts'] if p['part_id']==name);p=original/row['step_file'];assert sha(p)==row['step_sha256'];consumed[p.relative_to(ROOT).as_posix()]=row['step_sha256'];return cq.importers.importStep(str(p)).val()
 shaft=load('measurement_shaft');extension=cyl(3,-34,-17.9).cut(box(5,8,17,(5,0,-26)))
 extended=shaft.fuse(extension).clean();assert extended.isValid() and len(extended.Solids())==1
 bore=cyl(3.025,-34.1,-25.9).cut(box(5,8,10,(5.025,0,-30)))
 collar=cyl(8,-34,-26).cut(bore)
 # Split gap is intentional; two transverse M2 clearance holes are modeled.
 for x in (-5.3,5.3):collar=collar.cut(cq.Solid.makeCylinder(1.1,20,cq.Vector(x,-10,-30),cq.Vector(0,1,0)))
 halves=[collar.intersect(box(30,15,12,(0,sign*7.65,-30))) for sign in (-1,1)]
 assert all(s.isValid() and len(s.Solids())==1 for s in halves)
 spanner=cyl(12.5,-24,-13.45).cut(cyl(4.2,-24.1,-13.4))
 cap=load('threaded_adjuster_cap');clash=[s.intersect(extended).Volume() for s in halves]
 tool_hits=[s.intersect(spanner).Volume() for s in halves]
 parts={'extended_measurement_shaft':extended,'output_clamp_minus':halves[0],'output_clamp_plus':halves[1],'spanner_workspace':spanner}
 for name,s in parts.items():cq.exporters.export(s,str(a.out/(name+'.step')))
 cq.exporters.export(cq.Compound.makeCompound([extended,*halves,cap]),str(a.out/'output_candidate.step'))
 # Declared force and friction grid, never promoted to known supplier maximum.
 load=[]
 for force in (200,326,450,600):
  for mu in (.08,.12,.18):load.append(dict(spring_force_N_assumed=force,mu_assumed=mu,double_face_torque_Nm=2*mu*force*(2/3*(12**3-4.2**3)/(12**2-4.2**2))/1000))
 assert manifest_hash==sha(original/'manifest.json') and all(sha(ROOT/k)==h for k,h in consumed.items())
 result=dict(input_sha256=consumed,generator_sha256=sha(Path(__file__)),schema='o5-output-candidate-v1',source_manifest_sha256=sha(original/'manifest.json'),candidate='Extended D shaft plus two-piece output collar, 8mm engagement',extra_rear_extent_mm=16,collar_shaft_intersection_mm3=clash,collar_spanner_intersection_mm3=tool_hits,nominal_bore_clearance_mm=.025,clamp_split_gap_mm=.3,attachment_state='DIGITAL_CANDIDATE_NOT_LOAD_RATED',positive_torque_path='D shaft flat to D collar flat; clamp provides axial retention only after qualified fastener/preload design',fasteners='M2 transverse clearance holes only; screw/nut/thread/material selection and preload unqualified',preload_force_max_N=None,spring_force_policy='326N is a catalog point, not a maximum; no multiplier grants qualification',conditional_torque_grid=load,front_backing_retention='OPEN',rear_loaded_slide='OPEN',interrupted_thread_and_thin_wall='OPEN',bond_coupons='NOT_RUN',physical_tested=False,manufacturing_released=False,decision='Do not freeze this larger rear output. Use the exact 16mm penalty in common-arm screening; compare a side flange/output integration next if it dominates fit.')
 (a.out/'output_candidate.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:result[k] for k in ('extra_rear_extent_mm','collar_shaft_intersection_mm3','collar_spanner_intersection_mm3')}))
if __name__=='__main__':main()
