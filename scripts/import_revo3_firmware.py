"""Import an actually built seven-role set only when its precise firmware inputs and tools match.
This is explicit evidence reuse, never a fresh-build claim or reuse after producer failure.
"""
from revo3_evidence import *
import argparse,shutil

def match_firmware_inputs(original,current):
 prefixes=('Firmware/PoseDollFullBody/revO3/','Firmware/PoseDollFullBody/main/','Firmware/PoseDollFullBody/tools/')
 selected={k:h for k,h in original.items() if k.startswith(prefixes) or k=='scripts/build_revo3_firmware.py'}
 actual={k:h for k,h in current.items() if k.startswith(prefixes) or k=='scripts/build_revo3_firmware.py'}
 if not selected or selected!=actual:raise BlockedInput('Firmware sources/config/build recipe differ from producer')
 return selected

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--from-run',required=True);a=ap.parse_args();v,o=run_paths();oldv,oldo=run_paths(a.from_run)
 execution=read(oldv/'firmware_execution.json')
 if execution['status']!='PASS':raise BlockedInput('Original firmware producer did not pass')
 sealed=verify_artifacts(execution['artifacts'],a.from_run);initial=read(oldv/'inputs.json');current=sources()
 selected=match_firmware_inputs(initial['source_sha256'],current)
 toolchain=read(oldv/'toolchain.json')
 for path,digest in toolchain['executables_sha256'].items():
  if not Path(path).is_file() or sha(path)!=digest:raise BlockedInput('Producer tool changed: '+path)
 commit=subprocess.check_output(['git','-C','D:/ProgramFiles/esp/v6.1/esp-idf','rev-parse','HEAD']).decode().strip()
 if commit!=toolchain['idf_commit']['output'].strip():raise BlockedInput('IDF commit changed')
 report=read(oldv/'firmware_builds.json')
 if sorted(q['role'] for q in report['builds'])!=['G0','N1','N2','N3','N4','N5','N6'] or any(q['status']!='PASS' for q in report['builds']):raise BlockedInput('Incomplete/failed original role set')
 for root in (oldv/'firmware',oldo/'firmware'):
  target=(v if root.parent==oldv else o)/'firmware'
  if target.exists():raise FileExistsError('Immutable firmware delivery exists')
  shutil.copytree(root,target)
 for q in report['builds']:
  oldbinary=REPO/q['binary'];newbinary=o/'firmware'/q['role']/oldbinary.name
  if sha(newbinary)!=q['binary_sha256']:raise BlockedInput('Copied binary differs')
  q['original_binary']=q['binary'];q['binary']=newbinary.relative_to(REPO).as_posix();q['execution_mode']='REUSED_HASH_VERIFIED_BUILD';q['original_build_run_id']=a.from_run
 report.update(run_id=os.environ['REVO3_RUN_ID'],execution_mode='REUSED_HASH_VERIFIED_BUILD',original_build_run_id=a.from_run,original_report_sha256=sha(oldv/'firmware_builds.json'))
 verify_artifacts(execution['artifacts'],a.from_run)
 save(v/'firmware_builds.json',report);save(v/'firmware_origin.json',{'original_execution':execution,'original_artifact_manifest':sealed,'matched_firmware_source_sha256':selected,'original_toolchain':toolchain,'scope':'Same binaries from the successful producer, source/config/build recipe/tools verified. No recompilation claimed.'})
 print('PASS verified reuse of seven actually built roles from',a.from_run,flush=True)
if __name__=='__main__':main()
