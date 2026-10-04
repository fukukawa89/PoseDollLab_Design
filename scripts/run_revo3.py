"""Fresh immutable O3 execution; read-only hardware tools, never flash/order/release."""
from revo3_evidence import *
import argparse,concurrent.futures,functools,http.server,threading

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run-id',required=True);ap.add_argument('--reuse-firmware-from');a=ap.parse_args();os.environ['REVO3_RUN_ID']=a.run_id;r=Run(a.run_id)
 py=str(REPO/'.venv/Scripts/python.exe');kpy='D:/ProgramFiles/KiCad/10.0/bin/python.exe';node='C:/Users/Ding/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
 env={'PYTHONPATH':str(REPO/'Tools/PoseDollSimulator/src')+';'+str(REPO/'Tools/PoseDollHardwareBridge'),'KICAD10_3DMODEL_DIR':'D:/ProgramFiles/KiCad/10.0/share/kicad/3dmodels'}
 cad=lambda script:[py,'-X','utf8','Hardware/PoseDoll44/tools/run_cad.py','Hardware/PoseDoll44/cad/revO3/'+script]
 def probe(cmd):
  p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);return {'command':cmd,'exit_code':p.returncode,'output':p.stdout.decode(errors='replace')}
 paths=[py,kpy,node,'D:/ProgramFiles/CQ-editor/CQ-editor.exe','D:/ProgramFiles/KiCad/10.0/bin/kicad-cli.exe','C:/Espressif/tools/xtensa-esp-elf/esp-15.2.0_20251204/xtensa-esp-elf/bin/xtensa-esp32s3-elf-gcc.exe','D:/ProgramFiles/esp/v6.1/esp-idf/tools/idf.py']
 save(r.path/'toolchain.json',{'executables_sha256':{p:sha(p) if Path(p).is_file() else 'MISSING' for p in paths},'cad_runtime':probe([py,'Hardware/PoseDoll44/tools/run_cad.py']),'idf_commit':probe(['git','-C','D:/ProgramFiles/esp/v6.1/esp-idf','rev-parse','HEAD']),'system_python':sys.version})
 def parallel(jobs):
  with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
   futures=[pool.submit(fn) for fn in jobs]
   for f in futures:f.result()
 r.step('baseline',[py,'scripts/stage_revo3_baseline.py'],expected_paths=[r.path/'baseline.json',r.path/'inputs.json',r.path/'toolchain.json'],artifact_roots=[r.out/'inherited'])
 r.step('compatibility',[py,'scripts/check_repository.py'])
 r.step('legacy_config',[py,'Firmware/PoseDollFullBody/tools/generate_config.py','--check'])
 r.step('python_tests',[py,'-m','pytest','Tools/PoseDollHardwareBridge','Tools/PoseDollSimulator/tests','scripts/tests/test_revo.py','scripts/tests/test_revo2.py','scripts/tests/test_revo3.py','-q','-p','no:cacheprovider'],extra_env=env)
 core=REPO/'.local/revo3'/a.run_id/'host'
 r.step('host_C',['cmd.exe','/c',str(REPO/'scripts/Run-RevO3-CoreTests.cmd'),str(core)],expected_paths=[core/'golden_pd41.bin'],artifact_roots=[core])
 r.step('golden_crosscheck',[py,'scripts/check_revo3_golden.py',str(core/'golden_pd41.bin')],dependencies=['host_C'],expected_paths=[r.path/'golden_crosscheck.json'])
 r.step('offline',[py,'scripts/collect_revo3_offline.py'],dependencies=['compatibility','legacy_config','python_tests','host_C','golden_crosscheck'],expected_paths=[r.path/'offline.json'])
 r.step('review_counterexamples',[py,'-X','utf8','Hardware/PoseDoll44/tools/run_cad.py','Hardware/PoseDoll44/docs/revO3_review_source/audit_revo2_focused.py','--output',str(r.path/'O2_counterexamples.json')],expected_paths=[r.path/'O2_counterexamples.json'])
 parallel([
  lambda:r.step('joint',cad('export_joint.py'),expected_paths=[r.path/'joint.json'],artifact_roots=[r.out/'joint']),
  lambda:r.step('electronics',[kpy,'-X','utf8','scripts/build_revo3_electronics.py'],extra_env=env,expected_paths=[r.path/'electronics.json'],artifact_roots=[r.out/'electronics']),
  lambda:r.step('firmware',([py,'scripts/import_revo3_firmware.py','--from-run',a.reuse_firmware_from] if a.reuse_firmware_from else [py,'scripts/build_revo3_firmware.py']),dependencies=['host_C'],expected_paths=[r.path/'firmware_builds.json']+([r.path/'firmware_origin.json'] if a.reuse_firmware_from else []),artifact_roots=[r.out/'firmware',r.path/'firmware'])])
 parallel([
  lambda:r.step('assembly',cad('check_assembly.py'),dependencies=['joint'],expected_paths=[r.path/'assembly.json']),
  lambda:r.step('lifecycle',cad('check_lifecycle.py'),dependencies=['joint'],expected_paths=[r.path/'lifecycle.json'],artifact_roots=[r.out/'joint_constraints.json']),
  lambda:r.step('pcba_geometry',cad('audit_layout.py'),dependencies=['electronics'],expected_paths=[r.path/'pcba_geometry.json'],artifact_roots=[r.out/'pcba'])])
 r.step('mass_mechanics',[py,'scripts/study_revo3.py'],dependencies=['joint','baseline'],expected_paths=[r.path/'mass_properties_revO3.json',r.path/'mechanics_analysis.json'],artifact_roots=[r.out/'layouts'])
 r.step('packaging',[py,'scripts/packaging_revo3.py'],dependencies=['joint','pcba_geometry'],expected_paths=[r.path/'packaging.json',r.out/'packaging_scene.json'])
 coredeps=['baseline','offline','joint','assembly','lifecycle','electronics','pcba_geometry','mass_mechanics','packaging','firmware']
 r.step('status',[py,'scripts/report_revo3.py'],dependencies=coredeps,expected_paths=[r.path/'status.json'])
 r.step('viewer',[py,'scripts/build_revo3_viewer.py'],dependencies=['joint','assembly','lifecycle','electronics','pcba_geometry','mass_mechanics','packaging','status'],expected_paths=[r.out/'review.html',r.path/'viewer_inputs.json'])
 browserdir=r.path/'browser';browserdir.mkdir()
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(HW)));threading.Thread(target=server.serve_forever,daemon=True).start()
 url=f'http://127.0.0.1:{server.server_address[1]}/generated/revO3/runs/{a.run_id}/review.html'
 try:r.step('browser',[node,'scripts/check_viewer_revo3.cjs',url,str(browserdir)],dependencies=['viewer','joint','packaging','status'],expected_paths=[browserdir/'browser.json'],artifact_roots=[browserdir])
 finally:server.shutdown();server.server_close()
 result=r.finish();print(json.dumps({'run_id':a.run_id,'execution_status':result['status'],'changed_sources':result['source_changed_during_run'],'integrity_errors':result['artifact_integrity_errors']},ensure_ascii=False),flush=True)
 if result['status']!='PASS_EXECUTION_ONLY':raise SystemExit(1)
if __name__=='__main__':main()
