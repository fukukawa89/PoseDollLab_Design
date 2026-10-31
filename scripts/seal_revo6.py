"""Seal active O6 source/STEP/evidence; a valid seal does NOT mean design pass."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,zipfile
R=Path(__file__).resolve().parents[1];H=R/'Hardware/PoseDoll44';G=H/'generated/revO6/runs/o6_20260924_r1';V=H/'verification/revO6/runs/o6_20260924_r1';OUT=H/'verification/revO6/delivery'

def digest(b):return hashlib.sha256(b).hexdigest()
def sha(p):return digest(p.read_bytes())
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def verify():
 m=read(OUT/'DELIVERY_MANIFEST.json');errors=[];count=0
 for n,h in m['files_sha256'].items():
  p=R/n;count+=1
  if not p.is_file() or sha(p)!=h:errors.append(n)
 zpath=R/m['archive']
 if not zpath.is_file() or sha(zpath)!=m['archive_sha256']:errors.append(m['archive'])
 else:
  with zipfile.ZipFile(zpath) as z:
   if set(z.namelist())!=set(m['members_sha256']):errors.append('archive member set')
   for n,h in m['members_sha256'].items():
    count+=1
    if n not in z.namelist() or digest(z.read(n))!=h:errors.append('archive:'+n)
 print(json.dumps({'verified':not errors,'checked_hashes':count,'errors':errors,'full_design_pass':False,'physical_tested':False,'manufacturing_released':False}))
 return 1 if errors else 0

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--verify',action='store_true');a=ap.parse_args()
 if a.verify:return verify()
 assert not (OUT/'DELIVERY_MANIFEST.json').exists(),'Do not overwrite a sealed run; start a new delivery.'
 proc=subprocess.run([sys.executable,str(R/'scripts/summarize_revo6.py'),'--verify'],cwd=R,capture_output=True);assert proc.returncode==0,proc.stdout+proc.stderr
 result=read(V/'results.json');assert result['overall_status'].endswith('NOT_RELEASED')
 bases=[H/'cad/revO6',R/'Firmware/PoseDollFullBody/revO6',H/'references/revO6',G/'joint_L6_validated',G/'joint_M4_validated',G/'bilateral_search',V/'joint_L6_final',V/'joint_M4_validated',V/'service',V/'bilateral_search',V/'backpack',V/'backspace',V/'daisy',V/'thread_diagnostics']
 files={p for base in bases for p in base.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
 files.update((R/'scripts').glob('*revo6*.py'));files.update([V/'results.json',V/'SUPERSEDED.json',V/'power.json',G/'review_mesh.json',G/'review.png',H/'docs/O6_DESIGN_AND_BACKPACK.zh-CN.md',H/'docs/REVIEW_REQUEST_REVO6.zh-CN.md',H/'mechanical_manifest/requirements_revO6.json',H/'tools/run_cad.py'])
 files.update(R/n for n in result['dependency_sha256']);files.update(R/n for n in result['evidence_sha256'])
 # Extra direct Python imports are bundled even when an older caller only locked
 # its top-level script. They are disclosure inputs, not retroactive old receipts.
 files.update([R/'scripts/revo_common.py',R/'scripts/study_revo.py',H/'cad/model.py'])
 files.update([H/'verification/revO5/deliveries/o5_20260924_d1/DELIVERY_MANIFEST.json',H/'verification/revO5/deliveries/o5_20260924_d1/FINAL_SOURCE_LOCK.json',H/'verification/revO5CN/delivery/DELIVERY_MANIFEST.json'])
 OUT.mkdir(parents=True,exist_ok=True);zpath=OUT/'o6_active_native_and_evidence.zip';members={}
 with zipfile.ZipFile(zpath,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in sorted(files):
   assert p.resolve().is_relative_to(R),p
   n=p.relative_to(R).as_posix();data=p.read_bytes();z.writestr(n,data);members[n]=digest(data)
 for n,h in members.items():assert sha(R/n)==h,('changed while packaging',n)
 save(OUT/'DELIVERY_MANIFEST.json',{'schema':'o6-active-sealed-evidence-v1','files_sha256':members,'archive':zpath.relative_to(R).as_posix(),'archive_sha256':sha(zpath),'members_sha256':members,'contains':'Active geometry and active reports, editable O6 sources, actual locked project inputs, old sealed manifest receipts and thread diagnostics. Earlier failed experimental meshes are excluded; see SUPERSEDED.json.','evidence_pass_is_not_design_pass':True,'full_design_pass':False,'physical_tested':False,'manufacturing_released':False})
 return verify()
if __name__=='__main__':raise SystemExit(main())
