"""Build seven separate identities; never flash. Preserve actual logs and hashes."""
import argparse
import datetime
import subprocess
from revo_common import *

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--roles',nargs='+',default=['G0','N1','N2','N3','N4','N5','N6'])
    a=parser.parse_args()
    fw=REPO/'Firmware/PoseDollFullBody/revO'
    logs=VERIFY/'firmware'; logs.mkdir(parents=True,exist_ok=True)
    report=logs/'builds.json'
    rows=read(report)['builds'] if report.exists() else {}
    for role in a.roles:
        assert role in ['G0','N1','N2','N3','N4','N5','N6']
        log=logs/(role+'.log')
        with log.open('wb') as stream:
            p=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(fw/'build.ps1'),'-Role',role],stdout=stream,stderr=subprocess.STDOUT)
        build=fw/('build_'+role)
        item={'status':'PASS' if p.returncode==0 else 'FAIL','exit_code':p.returncode,'log':str(log.relative_to(REPO))}
        if p.returncode==0:
            cfg=(build/'sdkconfig').read_text(encoding='utf-8')
            assert ('CONFIG_PD_EXTERNAL_GATEWAY=y' in cfg)==(role=='G0')
            assert ('CONFIG_PD_NODE_ID='+('1' if role=='G0' else role[1])) in cfg
            binary=build/'posedoll_revo_pd41.bin'
            item.update(binary=str(binary.relative_to(REPO)),binary_sha256=sha(binary),sdkconfig_sha256=sha(build/'sdkconfig'))
        rows[role]=item
        save(report,{'builds':rows,'tested_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha256':{p.relative_to(REPO).as_posix():sha(p) for p in (fw/'main').glob('*') if p.is_file()},'flashed':False,'hardware_tested':False})
        print(role,item['status'],flush=True)
        if p.returncode:
            print(log.read_text(encoding='utf-8',errors='replace')[-5000:])
            raise SystemExit(p.returncode)

if __name__=='__main__':main()
