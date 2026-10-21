"""Run actual compatibility, new-design and C gateway checks; save commands and logs."""
import datetime
import os
import subprocess
from revo_common import *
def main():
    directory=VERIFY/'offline';directory.mkdir(parents=True,exist_ok=True)
    python=str(REPO/'.venv/Scripts/python.exe')
    env=os.environ.copy();env['PYTHONPATH']=str(REPO/'Tools/PoseDollSimulator/src')+';'+str(REPO/'Tools/PoseDollHardwareBridge')
    commands=[
      ['powershell.exe','-NoProfile','-File','scripts/Build-Design.ps1','-Stage','OfflineTests'],
      [python,'-m','pytest','scripts/tests/test_revo.py','-q','-p','no:cacheprovider'],
      ['cmd.exe','/c',str(REPO/'scripts/Run-RevO-CoreTests.cmd')],
      [python,'scripts/check_repository.py','--golden','.local/revO-core/golden_pd41.bin'],
      [python,'scripts/freeze_revo_baseline.py','--check']]
    results=[]
    for i,command in enumerate(commands,1):
        run=subprocess.run(command,cwd=REPO,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        path=directory/f'{i:02d}.txt';path.write_bytes(run.stdout)
        results.append(dict(command=command,exit_code=run.returncode,status='PASS' if run.returncode==0 else 'FAIL',log=path.relative_to(REPO).as_posix(),log_sha256=sha(path)))
        print(i,results[-1]['status'],run.stdout.decode('utf-8',errors='replace')[-2200:],flush=True)
    save(directory/'results.json',dict(status='PASS' if all(x['exit_code']==0 for x in results) else 'FAIL',commands=results,
         tested_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),hardware_tested=False,UE_editor_regression='NOT_RUN_UNMODIFIED_SOFTWARE'))
    if any(x['exit_code'] for x in results):raise SystemExit(1)
if __name__=='__main__':main()
