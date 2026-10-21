"""Run the narrow host audit. Requires Python 3.10+ and GCC on a Linux host.
No USB, network, flashing, CAD, KiCad or UE actions are performed.
"""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--cc',default='gcc');args=ap.parse_args()
    cc=shutil.which(args.cc)
    if not cc: raise SystemExit('Compiler unavailable. Run in a GCC host environment; do not mark the C checks passed.')
    identities=json.loads((ROOT/'source_identity.json').read_text())
    for name,item in identities.items():
        data=(ROOT/'source'/name).read_bytes()
        blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        if blob!=item['expected_git_blob_sha1']: raise SystemExit('Source identity mismatch: '+name)
    logs=[]
    def execute(name,cmd):
        r=subprocess.run(cmd,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        (ROOT/'results'/f'{name}.txt').write_text(r.stdout)
        logs.append({'name':name,'command':list(map(str,cmd)),'exit_code':r.returncode})
        print(r.stdout,end='');r.check_returncode()
    with tempfile.TemporaryDirectory(prefix='posedoll-o4-host-') as temp:
        flags=['-std=c11','-Wall','-Wextra','-Werror','-Wno-misleading-indentation']
        # A compiler-specific indentation warning is suppressed for unmodified one-line source.
        exe=Path(temp)/'original';retry=Path(temp)/'retry'
        execute('compile_original',[cc,*flags,'-include','fopen_compat.h','source/remote_link.c','source/test_remote_link.c','-o',str(exe)])
        execute('pdr4_original',[str(exe)])
        execute('compile_retry',[cc,*flags,'-Isource','source/remote_link.c','test_lost_response.c','-o',str(retry)])
        execute('pdr4_retry',[str(retry)])
        execute('static_window',[sys.executable,'check_static_window.py'])
    result={'scope':'Narrow host execution; not full repository/UE/CAD/physical qualification','commands':logs,'compiler_version':subprocess.check_output([cc,'--version'],text=True).splitlines()[0], 'tests_assert_current_deficiencies_not_fixes':True,'physical_tested':False,'UE_editor_rerun':False,'CAD_rerun':False,'KiCad_rerun':False,'ESP_IDF_rerun':False}
    (ROOT/'results/audit_run.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
