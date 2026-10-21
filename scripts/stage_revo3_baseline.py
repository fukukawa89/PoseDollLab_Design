from revo3_evidence import *
import shutil,subprocess
OLD=HW/'verification/revO2/runs/o2_20260923_r1'
def main():
 v,o=run_paths();baseline=read(HW/'verification/revO/fallback_91cm_inventory.json');issues=[]
 for q in baseline['files']:
  p=REPO/q['path']
  if not p.is_file() or sha(p)!=q['sha256']:issues.append(q['path'])
 previous=read(OLD/'run.json');oldbad=[]
 for name,digest in previous['output_sha256'].items():
  p=REPO/name
  if not p.is_file() or sha(p)!=digest:oldbad.append(name)
 tag=subprocess.check_output(['git','rev-parse','fallback/revN1-91cm-20260923^{commit}'],cwd=REPO).decode().strip()
 changes=subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=REPO).decode().splitlines()
 # New files are allowed; legacy tracked source stays frozen, except current entry links.
 forbidden=[q for q in changes if q not in ('README.md','scripts/Start-Viewer.ps1') and '/revO3/' not in q and 'revo3' not in q.lower()]
 if tag!='458f3b0646f724f3b74769defc98f5f6e9ec45a8':issues.append('fallback tag moved')
 source=HW/'docs/revO3_review_source';package=read(source/'package_manifest.json')
 entries=package.get('files',package)
 # Original package entries are checked by the source package's explicit filenames.
 package_bad=[]
 if isinstance(entries,dict):
  for name,value in entries.items():
   p=source/name;expected=value if isinstance(value,str) else value['sha256']
   if not p.is_file() or sha(p)!=expected:package_bad.append(name)
 else:
  for q in entries:
   name=q.get('path',q.get('file',q.get('name')));p=source/name
   if not p.is_file() or sha(p)!=q['sha256']:package_bad.append(name)
 inherited=o/'inherited';inherited.mkdir()
 records=[]
 for name in ('legacy_mass_reference.json','power_budget.json','mass_properties_revO2.json','joint.json','mechanics_analysis.json'):
  p=OLD/name;dest=inherited/name;shutil.copy2(p,dest);records.append({'original':p.relative_to(REPO).as_posix(),'copy':dest.relative_to(REPO).as_posix(),'sha256':sha(p),'original_run_id':'o2_20260923_r1','status':'INHERITED_REFERENCE_NOT_RERUN'})
 status='PASS' if not (issues or oldbad or forbidden or package_bad) else 'FAIL_OR_BLOCKED_BASELINE'
 save(v/'baseline.json',{'status':status,'fallback_files_checked':len(baseline['files']),'fallback_issues':issues,'O2_output_files_checked':len(previous['output_sha256']),'O2_output_issues':oldbad,'forbidden_legacy_changes':forbidden,'review_package_issues':package_bad,'inherited_references':records,'user_override':read(HW/'mechanical_manifest/requirements_revO3.json')['mass_policy']})
 print(status,flush=True)
 if status!='PASS':raise SystemExit(1)
if __name__=='__main__':main()
