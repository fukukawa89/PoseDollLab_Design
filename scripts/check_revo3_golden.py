from revo3_evidence import *
import argparse,subprocess

def main():
 ap=argparse.ArgumentParser();ap.add_argument('golden',type=Path);a=ap.parse_args();v,o=run_paths();r=ArtifactReader('host_C');p=r.path(a.golden)
 code=subprocess.run([sys.executable,'scripts/check_repository.py','--golden',str(p)],cwd=REPO).returncode
 save(v/'golden_crosscheck.json',{'status':'PASS' if code==0 else 'FAIL','consumed_inputs':r.receipt()});raise SystemExit(code)
if __name__=='__main__':main()
