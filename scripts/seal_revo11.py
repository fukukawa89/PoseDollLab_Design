"""Seal O11 evidence without declaring unresolved hardware or body work passed."""
from pathlib import Path
import json,hashlib,sys,subprocess
R=Path(__file__).resolve().parents[1];H=R/'Hardware/PoseDoll44';G=H/'generated/revO11/runs/o11_20260926_r1';DEST=G/'evidence_manifest.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'),parse_constant=lambda v:(_ for _ in ()).throw(ValueError('Nonfinite '+v)))
def old_check():
 result=subprocess.run([sys.executable,'-X','utf8',str(R/'scripts/seal_revo10.py'),'--verify'],cwd=R,capture_output=True,text=True,encoding='utf-8');assert result.returncode==0,result.stdout+result.stderr;return json.loads(result.stdout)
def check_dependencies(report):
 for field in ('input_sha256','inputs_sha256'):
  for n,digest in report.get(field,{}).items():assert sha(H/n)==digest,('stale dependency',n)
def main():
 if '--verify' in sys.argv:
  data=read(DEST);bad=[n for n,d in data['repository_files_sha256'].items() if not (R/n).exists() or sha(R/n)!=d];old=old_check();print(json.dumps({'verified':not bad,'files':len(data['repository_files_sha256']),'errors':bad,'upstream_O10_verified':old['verified'],'physical_tested':False,'manufacturing_released':False}));raise SystemExit(bool(bad))
 assert not DEST.exists(),'Do not replace a sealed run; create a new run.'
 old=old_check();summary=read(G/'summary.json');target=read(G/'braked_module/target_motion.json');body=read(G/'clavicle_trial/motion.json');yoke=read(G/'printed_core/continuous_yokes.json');assembly=read(G/'assembly_and_stack.json');loads=read(G/'loads.json');core=read(G/'printed_core/build.json');module=read(G/'braked_module/build.json');bench=read(H/'bench/revO11/plan.json');page=read(H/'tutorials/print-first/verification/checks.json');sources=read(H/'tutorials/print-first/model_sources.json')
 for report in (target,body,yoke,assembly,loads):check_dependencies(report)
 assert target['complete'] and len(target['cases'])==204 and not any(r['findings'] for r in target['cases'])
 assert body['complete'] and len(body['cases'])==102
 assert summary['remainingCollisions']==[r for r in body['cases'] if r['findings']]
 assert summary['summary']['bodyFailures']==sum(bool(r['findings']) for r in body['cases'])
 assert yoke['status']=='CERTIFIED_NOMINAL_YOKE_PAIR_ONLY' and yoke['area_deg2']==10976 and not yoke['failed_cells'] and not yoke['unknown_cells']
 assert core['generator_sha256']==sha(H/'cad/revO11/build_printed_core.py') and not core['assembled_findings']
 assert all(v['solid_components']==1 and v['volume_mm3']>0 for v in core['parts'].values())
 assert module['source_sha256']==sha(G/'printed_core/parts.npz')
 assert all(v['solid_components']==1 and v['volume_mm3']>0 for c in module['characters'] for v in c['parts'].values())
 assert not any(r['hits'] for r in assembly['straight_AF2_tool_shank']) and not any(r['findings'] for r in assembly['catalogue_tolerance_cases'])
 assert max(r['volume_mm3'] for row in assembly['ring_inserts'] for r in row['insertion_from_open_split_plane'])<1e-4
 assert min(r['volume_mm3'] for row in assembly['ring_inserts'] for r in row['outward_pull'])>.01
 assert bench['target_source_sha256']==sha(G/'loads.json') and bench['generator_sha256']==sha(H/'cad/revO11/build_printed_bench.py') and bench['stack_generator_sha256']==sha(H/'cad/revO11/build_printed_core.py')
 assert len(bench['parts'])==15 and bench['custom_metal_parts']==0 and not bench['nominal_volume_findings']
 assert all(v is None for k,v in read(H/'bench/revO11/measurement_template.json').items() if k!='schema')
 assert page['status']=='PASS' and not page['errors']
 assert sources['bench_sha256']==sha(H/'bench/revO11/parts.npz') and sources['core_sha256']==sha(G/'printed_core/parts.npz') and sources['generator_sha256']==sha(H/'cad/revO11/export_print_pack.py')
 files={Path(__file__),H/'docs/O11_PRINT_FIRST.zh-CN.md',H/'generated/revO10/runs/o10_20260926_r1/evidence_manifest.json'}
 for root in (H/'cad/revO11',G,H/'bench/revO11',H/'research/revO11',H/'tutorials/print-first'):
  files.update(p for p in root.rglob('*') if p.is_file() and p!=DEST and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.log'))
 data={'schema':'o11-print-first-evidence-v1','run_id':'o11_20260926_r1','status':'SCOPED_DIGITAL_CANDIDATE_WITH_OPEN_FULL_BODY_COLLISION','summary':summary['summary'],'preserved_failures':summary['remainingCollisions'],'upstream':old,'repository_files_sha256':{p.relative_to(R).as_posix():sha(p) for p in sorted(files)},'physical_tested':False,'slicer_tested':False,'full_joint_pass':False,'full_body_pass':False,'manufacturing_released':False,'scope':'Integrity of recorded digital results, not strength, creep, printer tolerances, electronics, wiring or manufacturing approval. Independent coupon testing cannot clear the remaining body collision.'}
 DEST.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'files':len(files),'summary':data['summary']},ensure_ascii=False))
if __name__=='__main__':main()
