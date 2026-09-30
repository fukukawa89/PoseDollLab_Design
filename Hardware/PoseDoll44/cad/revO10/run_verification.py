"""Fail-fast verification with source receipts around each subprocess."""
from pathlib import Path
import sys,subprocess,time,json,hashlib
H=Path(__file__).resolve().parents[2];R=H.parents[1];P=Path(__file__).parent;G=H/'generated/revO10/runs/o10_20260926_r1';group=sys.argv[1]
groups={'geometry':[['audit_retention_and_clavicle.py'],['check_assembly_tools.py'],['boolean_face_brake.py'],['check_braked_module.py']],'mass':[['face_axis_loads.py'],['build_bench_coupon.py']],'methods':[['test_methods.py']],'clavicle':[['clavicle_trial.py','--candidate','-60,20,10']]}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inputs(name):
 files={H/'cad/model.py',H/'tools/run_cad.py'}
 for d in (P,H/'cad/revO8',H/'cad/revO9'):files.update(d.glob('*.py'))
 for d in (G/'braked_module',G/'old_modules'):files.update(d.glob('*.npz'))
 files.update([G/'face_brake/parts.npz',G/'face_brake/threads.npz',G/'face_brake/build.json',G/'braked_module/build.json',G/'shoulder_assembly/states.json',H/'generated/revO8/runs/o8_20260925_r1/fastened_core/fasteners.npz',H/'generated/revO9/runs/o9_20260926_r1/bounded_mapping.json',H/'generated/revO9/runs/o9_20260926_r1/cup_relief_L3_R0p35/core_meshes.npz',H/'generated/revO6/runs/o6_20260924_r1/joint_M4_validated/manifest.json',H/'generated/revO7/runs/o7_20260924_r1/LP6_current/manifest.json'])
 files.update((H/'generated/revO7/runs/o7_20260924_r1/bilateral_current').glob('*.json'))
 if name=='build_bench_coupon.py':files.add(G/'face_axis_loads.json')
 if name=='test_methods.py':files.update([H/'bench/revO10/plan.json',H/'bench/revO10/measurement_template.json'])
 return {p.relative_to(H).as_posix():sha(p) for p in sorted(files)}
rows=[]
for spec in groups[group]:
 name=spec[0];before=inputs(name);args=[sys.executable,'-X','utf8']
 if group=='methods':args+=[str(H/'tools/run_cad.py')]
 args+=[str(P/name),*spec[1:]];start=time.time();log=G/(name.replace('.py','')+'_final.log')
 with log.open('w',encoding='utf-8') as f:r=subprocess.run(args,cwd=R,stdout=f,stderr=subprocess.STDOUT)
 after=inputs(name);assert before==after,('Inputs changed during check',name)
 rows.append({'script':name,'exit_code':r.returncode,'seconds':time.time()-start,'log':log.relative_to(H).as_posix(),'input_sha256':before});print(name,r.returncode,round(time.time()-start,2),flush=True)
 if r.returncode:raise SystemExit(r.returncode)
(G/f'verification_{group}.json').write_text(json.dumps({'complete':True,'processes':rows},indent=2)+'\n')
