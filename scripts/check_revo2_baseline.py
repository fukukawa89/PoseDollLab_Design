"""Missing historical local CAD is explicitly BLOCKED, never a new-design failure/pass."""
from revo2_evidence import *

def main():
 verify,out=run_paths();inventory=read(HW/'verification/revO/fallback_91cm_inventory.json');missing=[];changed=[]
 for item in inventory['files']:
  p=REPO/item['path']
  if not p.is_file():missing.append(item['path'])
  elif sha(p)!=item['sha256']:changed.append(item['path'])
 old_changes=subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=REPO).decode().splitlines()
 old_changes=[p for p in old_changes if p not in ('README.md','scripts/Start-Viewer.ps1')]
 tag='fallback/revN1-91cm-20260923';expected_tag_commit='458f3b0646f724f3b74769defc98f5f6e9ec45a8'
 tag_result=subprocess.run(['git','rev-parse',tag+'^{commit}'],cwd=REPO,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 tag_commit=tag_result.stdout.decode().strip() if tag_result.returncode==0 else None
 status='FAIL_CHANGED_BASELINE' if changed or old_changes or tag_commit!=expected_tag_commit else ('BLOCKED_MISSING_LOCAL_ARTIFACT' if missing else 'PASS')
 save(verify/'baseline.json',{'status':status,'inventory_sha256':sha(HW/'verification/revO/fallback_91cm_inventory.json'),'files_checked':len(inventory['files']),'missing_local_artifacts':missing,'changed_inventory_files':changed,'changed_preexisting_tracked_files':old_changes,'fallback_tag':tag,'fallback_tag_commit':tag_commit,'expected_fallback_tag_commit':expected_tag_commit})
 print(status,'checked',len(inventory['files']),'missing',len(missing),'changed',len(changed),flush=True)
 if status!='PASS':raise SystemExit(1)
if __name__=='__main__':main()
