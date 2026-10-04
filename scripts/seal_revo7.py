"""Seal current O7 evidence and editable inputs without implying a design release."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,zipfile
R=Path(__file__).resolve().parents[1];H=R/'Hardware/PoseDoll44';G=H/'generated/revO7/runs/o7_20260924_r1';V=H/'verification/revO7/runs/o7_20260924_r1';OUT=H/'verification/revO7/delivery'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def verify():
 m=read(OUT/'DELIVERY_MANIFEST.json');errors=[];count=0
 for n,h in m['files_sha256'].items():
  p=R/n;count+=1
  if not p.is_file() or sha(p)!=h:errors.append(n)
 zpath=R/m['archive']
 if not zpath.is_file() or sha(zpath)!=m['archive_sha256']:errors.append(m['archive'])
 else:
  with zipfile.ZipFile(zpath) as z:
   if set(z.namelist())!=set(m['members_sha256']):errors.append('member set')
   for n,h in m['members_sha256'].items():
    count+=1
    if n not in z.namelist() or hashlib.sha256(z.read(n)).hexdigest()!=h:errors.append('archive:'+n)
 print(json.dumps({'verified':not errors,'checked_hashes':count,'errors':errors,'physical_tested':False,'full_body_pass':False,'manufacturing_released':False}));return int(bool(errors))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--verify',action='store_true');a=ap.parse_args()
 if a.verify:return verify()
 assert not (OUT/'DELIVERY_MANIFEST.json').exists(),'Create a new delivery instead of modifying a sealed one.'
 q=subprocess.run([sys.executable,str(R/'scripts/summarize_revo7.py'),'--verify'],cwd=R,capture_output=True);assert q.returncode==0,q.stdout+q.stderr
 result=read(V/'results.json');assert not result['physical_tested'] and not result['manufacturing_released']
 roots=[H/'bench/revO7',H/'references/revO7',G/'LP6_current',G/'bilateral_current',V/'LP6_current',V/'L6_preload',V/'M4_preload',V/'bilateral_current',V/'back_paths']
 files={p for root in roots for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
 files.update(p for p in (H/'cad/revO7').glob('*.py') if not p.name.startswith('diagnose'));files.update((R/'scripts').glob('*revo7*.py'))
 files.update([G/'review.png',G/'review_mesh.json',V/'results.json',V/'SUPERSEDED.json',H/'docs/O7_DIGITAL_AND_BENCH.zh-CN.md',H/'docs/REVIEW_REQUEST_REVO7.zh-CN.md',H/'mechanical_manifest/requirements_revO7.json',H/'tools/run_cad.py',H/'verification/revO6/delivery/DELIVERY_MANIFEST.json',H/'verification/revO5CN/delivery/DELIVERY_MANIFEST.json',H/'verification/revO5/deliveries/o5_20260924_d1/DELIVERY_MANIFEST.json',H/'verification/revO5/deliveries/o5_20260924_d1/FINAL_SOURCE_LOCK.json'])
 files.update(R/n for n in result['evidence_sha256']);files.update(R/n for n in result['dependency_sha256'])
 OUT.mkdir(parents=True,exist_ok=True);archive=OUT/'o7_current_design_and_bench.zip';members={}
 with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in sorted(files):
   assert p.resolve().is_relative_to(R);n=p.relative_to(R).as_posix();data=p.read_bytes();z.writestr(n,data);members[n]=hashlib.sha256(data).hexdigest()
 for n,h in members.items():assert sha(R/n)==h,('input changed during packaging',n)
 d={'schema':'o7-current-design-and-bench-seal-v1','files_sha256':members,'archive':archive.relative_to(R).as_posix(),'archive_sha256':sha(archive),'members_sha256':members,'content_scope':'Current LP6/native STEP, mixed-arm profiles and scoped reports, empty-back-reservation paths, material specimen STEP and empty measurement templates, editable scripts and locked project inputs. Prior failed trial solids/debug probes excluded; historical markers retained.','hash_integrity_is_not_engineering_qualification':True,'physical_tested':False,'full_body_pass':False,'manufacturing_released':False}
 (OUT/'DELIVERY_MANIFEST.json').write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8');return verify()
if __name__=='__main__':raise SystemExit(main())
