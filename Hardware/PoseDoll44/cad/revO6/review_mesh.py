"""Export deterministic review meshes from actual, hashed STEP parts."""
from pathlib import Path
import argparse,json,hashlib
import cadquery as cq
R=Path(__file__).resolve().parents[4];H=R/'Hardware/PoseDoll44'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();result=[]
 for family,folder in [('L6','joint_L6_validated'),('M4','joint_M4_validated')]:
  root=H/'generated/revO6/runs/o6_20260924_r1'/folder;m=json.loads((root/'manifest.json').read_text());parts=[]
  for r in m['parts']:
   if r['part_id'] in ('brake_cup_front_loading','housing_L'):continue
   p=root/r['step_file'];assert sha(p)==r['step_sha256'];s=cq.importers.importStep(str(p)).val();vertices,faces=s.tessellate(.2,.18)
   parts.append({'name':r['part_id'],'material':r['material'],'vertices':[list(v.toTuple()) for v in vertices],'faces':faces})
  result.append({'family':family,'mass_g':m['modeled_mass_g'],'bounds_mm':m['bounds_mm'],'parts':parts,'manifest_sha256':sha(root/'manifest.json')})
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps({'models':result,'display_hidden_parts':['brake_cup_front_loading','housing_L'],'view_only':True}));print([(m['family'],sum(len(p['faces']) for p in m['parts'])) for m in result])
if __name__=='__main__':main()

