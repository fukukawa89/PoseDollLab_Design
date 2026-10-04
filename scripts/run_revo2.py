"""Run immutable, dependency-aware O2 evidence. Does not flash, order parts, or alter legacy CAD."""
from revo2_evidence import *
from report_revo2 import assess,REPORTS
import argparse,subprocess,threading,http.server,functools,shutil

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run-id',required=True);a=ap.parse_args();os.environ['REVO2_RUN_ID']=a.run_id;r=Run(a.run_id)
 py=str(REPO/'.venv/Scripts/python.exe');kpy='D:/ProgramFiles/KiCad/10.0/bin/python.exe';node='C:/Users/Ding/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
 env={'PYTHONPATH':str(REPO/'Tools/PoseDollSimulator/src')+';'+str(REPO/'Tools/PoseDollHardwareBridge'),'KICAD10_3DMODEL_DIR':'D:/ProgramFiles/KiCad/10.0/share/kicad/3dmodels'}
 captured_reports={}
 cad=lambda script:[py,'-X','utf8','Hardware/PoseDoll44/tools/run_cad.py','Hardware/PoseDoll44/cad/revO2/'+script]
 def probe(cmd):
  try:
   result=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);return {'command':cmd,'exit_code':result.returncode,'output':result.stdout.decode(errors='replace')}
  except OSError as e:return {'command':cmd,'status':'BLOCKED_TOOL_UNAVAILABLE','error':str(e)}
 toolpaths=[py,kpy,node,'C:/Espressif/tools/cmake/4.0.3/bin/cmake.exe','C:/Espressif/tools/ninja/1.12.1/ninja.exe','C:/Espressif/tools/xtensa-esp-elf/esp-15.2.0_20251204/xtensa-esp-elf/bin/xtensa-esp32s3-elf-gcc.exe','D:/ProgramFiles/esp/v6.1/esp-idf/tools/idf.py']
 toolchain={'python_version':sys.version,'executable_sha256':{p:sha(p) if Path(p).is_file() else 'MISSING' for p in toolpaths},'idf_commit':probe(['git','-C','D:/ProgramFiles/esp/v6.1/esp-idf','rev-parse','HEAD']),'idf_python':'C:/Espressif/tools/python/v6.1/venv/Scripts/python.exe','compiler':'xtensa-esp-elf esp-15.2.0_20251204','cad_probe':probe([py,'Hardware/PoseDoll44/tools/run_cad.py'])}
 save(r.path/'toolchain.json',toolchain)
 r.step('baseline',[py,'scripts/check_revo2_baseline.py'],expected_paths=[r.path/'baseline.json'])
 r.step('compatibility',[py,'scripts/check_repository.py'])
 r.step('legacy_config',[py,'Firmware/PoseDollFullBody/tools/generate_config.py','--check'])
 r.step('python_tests',[py,'-m','pytest','Tools/PoseDollHardwareBridge','Tools/PoseDollSimulator/tests','scripts/tests/test_revo.py','scripts/tests/test_revo2.py','-q','-p','no:cacheprovider'],extra_env=env)
 core=REPO/'.local/revo2'/a.run_id/'host'
 r.step('host_C',['cmd.exe','/c',str(REPO/'scripts/Run-RevO2-CoreTests.cmd'),str(core)],expected_paths=[core/'golden_pd41.bin'])
 r.step('golden_crosscheck',[py,'scripts/check_repository.py','--golden',str(core/'golden_pd41.bin')],dependencies=['host_C'])
 save(r.path/'offline.json',{'steps':{n:r.steps[n] for n in ['compatibility','legacy_config','python_tests','host_C','golden_crosscheck']},'status':'PASS' if all(r.steps[n]['status']=='PASS' for n in ['compatibility','legacy_config','python_tests','host_C','golden_crosscheck']) else 'FAIL','physical_tested':False})
 captured_reports['offline']=sha(r.path/'offline.json')
 r.step('joint',cad('export_joint.py'),expected_paths=[r.path/'joint.json',r.out/'joint/L6_R2_assembly.step'])
 r.step('assembly',cad('check_assembly.py'),dependencies=['joint'],expected_paths=[r.path/'assembly.json'])
 r.step('electronics',[kpy,'-X','utf8','scripts/build_revo2_electronics.py'],extra_env=env,expected_paths=[r.path/'electronics.json'])
 r.step('pcba_geometry',cad('audit_layout.py'),dependencies=['electronics'],expected_paths=[r.path/'pcba_geometry.json',r.path/'legacy_mass_reference.json'])
 r.step('mass_mechanics',[py,'scripts/study_revo2.py'],dependencies=['joint','pcba_geometry'],expected_paths=[r.path/'mass_properties_revO2.json',r.path/'mechanics_analysis.json',r.path/'power_budget.json'])
 r.step('packaging',[py,'scripts/packaging_revo2.py'],dependencies=['electronics','pcba_geometry'],expected_paths=[r.path/'packaging.json'])
 r.step('firmware',[py,'scripts/build_revo2_firmware.py'],dependencies=['host_C'],expected_paths=[r.path/'firmware_builds.json'])
 # Keep reviewable native boards outside ignored generated trees, with identity hashes.
 native=HW/'electronics/revO2'/a.run_id;delivery=[]
 if r.steps['electronics']['status']=='PASS':
  for kind in ('proximal5','distal4','distal4_narrow'):
   source=r.out/'electronics'/kind
   for p in source.rglob('*'):
    if p.is_file() and not p.name.startswith('placement.') and (p.suffix in ('.kicad_sch','.kicad_pcb','.kicad_pro','.kicad_mod','.kicad_sym') or p.name in ('fp-lib-table','sym-lib-table','layout.json')):
     dest=native/kind/p.relative_to(source);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);delivery.append({'path':dest.relative_to(REPO).as_posix(),'sha256':sha(dest)})
 save(r.path/'native_delivery.json',{'files':delivery,'generated_native_sources':str(r.out.relative_to(REPO))})
 save(r.path/'status.json',assess(r.path,a.run_id,r.steps))
 r.step('viewer',[py,'scripts/build_revo2_viewer.py'],dependencies=['joint','packaging','mass_mechanics'],expected_paths=[r.out/'review.html'])
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(HW)));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 url=f'http://127.0.0.1:{server.server_address[1]}/generated/revO2/runs/{a.run_id}/review.html'
 try:r.step('browser',[node,'scripts/check_viewer_revo2.cjs',url,str(r.path)],dependencies=['viewer'],expected_paths=[r.path/'browser.json'])
 finally:server.shutdown();server.server_close()
 hashes=dict(captured_reports)
 for step in r.steps.values():
  for rel,digest in step.get('outputs',{}).items():
   if Path(rel).stem in REPORTS and Path(rel).suffix=='.json':hashes[Path(rel).stem]=digest
 save(r.path/'report_hashes.json',{'reports':hashes})
 status=assess(r.path,a.run_id,r.steps,hashes)
 if sources()!=r.inputs:status['evidence_issues'].append('Input changed during run');status['gates']['V0']['status']='FAIL'
 save(r.path/'status.json',status);result=r.finish();print(json.dumps({'run_id':a.run_id,'execution':result['status'],'gates':status['gates']},ensure_ascii=False),flush=True)
 if result['status']!='PASS_EXECUTION_ONLY' or status['gates']['V0']['status']!='PASS':raise SystemExit(1)
if __name__=='__main__':main()
