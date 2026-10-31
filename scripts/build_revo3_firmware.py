"""Seven new build directories, roles checked from actual sdkconfig, no flashing."""
from revo3_evidence import *
import subprocess,shutil

def main():
 verify,out=run_paths();rid=os.environ['REVO3_RUN_ID'];root=REPO/'.local/revo3'/rid/'firmware';fw=REPO/'Firmware/PoseDollFullBody/revO3';reports=[]
 if root.exists():raise FileExistsError('Refusing to reuse firmware build tree '+str(root))
 root.mkdir(parents=True);(verify/'firmware').mkdir()
 for role in ['G0','N1','N2','N3','N4','N5','N6']:
  command=['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(fw/'build.ps1'),'-Role',role,'-BuildRoot',str(root)]
  log=verify/'firmware'/(role+'.txt')
  with log.open('wb') as stream:proc=subprocess.run(command,cwd=REPO,stdout=stream,stderr=subprocess.STDOUT)
  build=root/role;binary=build/'posedoll_revo_pd41.bin';config=build/'sdkconfig';result={'role':role,'exit_code':proc.returncode,'status':'FAIL','command':command,'log_sha256':sha(log)}
  if proc.returncode==0 and binary.is_file() and config.is_file():
   text=config.read_text();gateway='CONFIG_PD_EXTERNAL_GATEWAY=y' in text;node='CONFIG_PD_NODE_ID='+('1' if role=='G0' else role[1]);valid=gateway==(role=='G0') and node+'\n' in text
   delivery=out/'firmware'/role;delivery.mkdir(parents=True,exist_ok=True)
   for artifact in ('posedoll_revo_pd41.bin','sdkconfig','compile_commands.json'):shutil.copy2(build/artifact,delivery/artifact)
   result.update(status='PASS' if valid else 'FAIL_ROLE_CONFIG',config_role_checked=valid,binary=str((delivery/binary.name).relative_to(REPO)),binary_sha256=sha(binary),sdkconfig_sha256=sha(config),binary_bytes=binary.stat().st_size)
   save(verify/'firmware'/(role+'_config.json'),{'role':role,'config_source':str(config.relative_to(REPO)),'sdkconfig_sha256':sha(config),'role_lines':[q for q in text.splitlines() if q.startswith('CONFIG_PD_')],'compile_commands_sha256':sha(build/'compile_commands.json')})
  reports.append(result);save(verify/'firmware_builds.json',{'builds':reports,'expected_roles':['G0','N1','N2','N3','N4','N5','N6'],'flashed':False,'physical_tested':False});print(role,result['status'],flush=True)
  if result['status']!='PASS':print(log.read_text(errors='replace')[-3500:],flush=True)
 if any(x['status']!='PASS' for x in reports):raise SystemExit(1)
if __name__=='__main__':main()
