from arm_kit import *
import re, shutil, zipfile

def main():
 raw=(ROOT/'output/playwright/o24ct4-browser-result.txt').read_text('utf-8-sig').strip();browser=json.loads(raw)
 geo=sha(OUT/'assembly_meshes.npz');assert browser['passed'] and browser['geometry_sha256']==geo
 data=json.loads((OUT/'assembly.json').read_text('utf8'));P={p['id']:p for p in data['parts']};checks={};maxerr=0.
 for state in browser['states']:
  q,r,w,v=state['angles'];F=transforms('arm' if state['mode']=='arm' else 'three',q,r,w,v)
  for id,mat in state['transforms'].items():
   p=P[id];expected=F[p['station']][p['frame']]
   if state['mode']!='arm' and state['mode']!='three':expected=a.T([-{'H':-65,'R':0,'W':65}[p['station']],0,0])@expected
   maxerr=max(maxerr,float(np.max(np.abs(expected-np.array(mat).reshape(4,4)))))
 checks['browser_matches_CAD_transforms']=maxerr<1e-10
 put(OUT/'verification/browser.json',dict(passed=browser['passed'] and maxerr<1e-10,geometry_sha256=geo,steps=browser['steps'],pose_states=len(browser['states']),max_matrix_error=maxerr,errors=browser['errors'],mobile_no_overflow=not browser['mobile']['overflow'],offline_ready=browser['offline']['ready']))
 reports=['geometry','installed_rom','bench_rom','assembly_paths','module_insertion','ue_alignment','mechanics','slicing','blender','browser','purchase','combined_printing','tutorial_paths','tutorial_browser']
 for name in reports:
  r=json.loads((OUT/'verification'/(name+'.json')).read_text('utf8'));checks[name]=bool(r['passed']) and r.get('geometry_sha256',geo)==geo
 printed=[p for p in data['parts'] if p['printable']]
 checks['exact_STL_inventory']={p.name for p in (OUT/'stl_print').glob('*.stl')}=={p['id']+'.stl' for p in printed}
 checks['STL_hashes']=all(sha(OUT/p['stl'])==p['stl_sha256'] for p in printed)
 checks['printed_count']=len(printed)==17 and sum(not p['bench_only'] for p in printed)==12
 model=trimesh.load(OUT/'O24C_T4_installed_forearm.glb',force='scene');checks['GLB_parts']=len(model.geometry)==107
 d=build();F=transforms();pts=[]
 for p in d.parts:
  if not p['bench_only']:pts.append(np.array(moved(p['s'],F[p['station']][p['frame']]).bounding_box()).reshape(2,3))
 expected=np.array([np.min([x[0] for x in pts],axis=0),np.max([x[1] for x in pts],axis=0)])
 checks['GLB_mm_scale']=bool(np.max(np.abs(model.bounds*1000-expected))<.002)
 viewer=json.loads((OUT/'viewer/data.js').read_text('utf8')[len('window.KIT='):-1]);checks['same_mesh_viewer']=viewer['geometry_sha256']==geo and [p['id'] for p in viewer['parts']]==list(P)
 counts={}
 for p in data['parts']:
  if p['sku']:counts[p['sku']]=counts.get(p['sku'],0)+1
 checks['BOM_counts']=counts=={r['sku']:r['qty'] for r in json.loads((OUT/'BOM.json').read_text('utf8'))}
 sliced=json.loads((OUT/'verification/slicing.json').read_text('utf8'));plates=json.loads((OUT/'printing/plates.json').read_text('utf8'))['plates']
 checks['project_hashes']=all(sha(OUT/p['file'])==p['sha256']==next(r['input_sha256'] for r in sliced['plates'] if r['id']==p['id']) for p in plates)
 combined=json.loads((OUT/'printing/combined_plate.json').read_text('utf8'))['plates'][0]
 combined_report=json.loads((OUT/'verification/combined_printing.json').read_text('utf8'))
 checks['combined_project_hash']=sha(OUT/combined['file'])==combined['sha256']==combined_report['plate']['input_sha256']
 checks['combined_exact_17_prints']={i['id'] for i in combined['items']}=={p['id'] for p in printed} and len(combined['items'])==17
 checks['combined_preserves_print_faces']=all(np.allclose(np.array(i['transform'])[:3,2],[0,0,1]) and abs(np.linalg.det(np.array(i['transform'])[:3,:3])-1)<1e-8 for i in combined['items'])
 tutorial_browser=json.loads((OUT/'verification/tutorial_browser.json').read_text('utf8'))
 checks['tutorial_final_assets_tested']=all(sha(OUT/'tutorial'/name)==digest for name,digest in tutorial_browser['checked_assets'].items())
 purchase=json.loads((OUT/'purchase_from_owned.json').read_text('utf8'))
 checks['purchase_baselines_unchanged']=all(sha(ROOT/r['path'])==r['sha256'] for r in purchase['sources'].values())
 reuse={}
 prior=H/'bench/revO24C_T3';previous=json.loads((prior/'assembly.json').read_text('utf8'));oldparts={r['id']:r for r in previous['parts']}
 for row in printed:
  if row['id'] in oldparts:reuse[row['id']]=sha(OUT/row['stl'])==sha(prior/oldparts[row['id']]['stl'])
 checks['claimed_reuse_identical']=len(reuse)==13 and all(reuse.values())
 zn=np.load(OUT/'assembly_meshes.npz');zo=np.load(prior/'assembly_meshes.npz');same=[]
 for row in data['parts']:
  if row['station'] in ['H','R']:
   was=oldparts[row['id']]
   same.append(all(np.array_equal(zn[k+str(row['index'])],zo[k+str(was['index'])]) for k in ['v','f']))
 checks['H_R_all_meshes_identical']=all(same)
 frozen=json.loads((prior/'manifest.json').read_text('utf8'))['files'];frozenbad=[r['path'] for r in frozen if sha(prior/r['path'])!=r['sha256']]
 checks['T3_unchanged']=not frozenbad
 put(OUT/'verification/reuse.json',dict(passed=checks['claimed_reuse_identical'] and checks['H_R_all_meshes_identical'] and checks['T3_unchanged'],geometry_sha256=geo,identical_STLs=reuse,unchanged_H_R_entries=len(same),T3_files_checked=len(frozen),T3_changes=frozenbad))
 links=[];missing=[]
 for p in list(OUT.glob('*.html'))+list((OUT/'viewer').glob('*.html'))+list((OUT/'tutorial').glob('*.html')):
  for rel in re.findall(r'(?:href|src)="([^"]+)"',p.read_text('utf8')):
   if rel.startswith(('http','data:','#')):continue
   target=p.parent/rel.split('#')[0].split('?')[0];links.append(str(target))
   if target.name=='PoseDoll_O24C_T4_Dual_Axis_Wrist_Kit.zip' or target==OUT/'verification/delivery.json':continue
   if not target.exists():missing.append(str(target))
 checks['local_links']=not missing
 old=[]
 for rev in ['revO24C_T1','revO24C_T2_H']:
  root=H/'bench'/rev;manifest=json.loads((root/'MANIFEST.sha256.json').read_text('utf8'));files=manifest['files']
  if isinstance(files,dict):files=[dict(path=k,sha256=v) for k,v in files.items()]
  bad=[r['path'] for r in files if not (root/r['path']).exists() or sha(root/r['path'])!=r['sha256']]
  old.append(dict(revision=rev,checked=len(files),mismatches=bad))
 checks['old_kits_unchanged']=all(not r['mismatches'] for r in old)
 # Accessible runtime note for source snapshots, not an installer.
 (OUT/'source').mkdir(exist_ok=True);(OUT/'source/REBUILD.txt').write_text('Source snapshots belong at Hardware/PoseDoll44/cad/revO24C_T4 in the original repository. They depend on revO24, revO24C_T1 and revO24C_T3 helpers and the repository Python environment. STL, 3MF and offline pages do not require rebuilding. Geometry: arm_kit.py, audit.py, assembly_checks.py, bench_checks.py, print_projects.py, Blender render.py. Existing geometry need not be regenerated for a tutorial update. Deliverables: combined_print.py, publish.py, owned_hardware.py, print_guide.py, tutorial_assets.py, tutorial.py, tutorial_checks.py. Browser: browser_review.js and tutorial_browser_review.js through Playwright CLI, then verify_tutorial_browser.py, verify_delivery.py, and publish.py --package. No files are sent to a printer.\n',encoding='utf8')
 (OUT/'REBUILD.txt').write_text((OUT/'source/REBUILD.txt').read_text('utf8'),encoding='utf8')
 report=dict(passed=all(checks.values()),geometry_sha256=geo,checks=checks,printed_parts=17,actual_joint_prints=12,detachable_tools=4,optional_coupon=1,link_count=len(links),missing_links=missing,unchanged_old_packages=old,reused_STL_identical=reuse,GLB_bounds_mm=(model.bounds*1000).tolist(),physical_tests_passed=False)
 put(OUT/'verification/delivery.json',report);print(json.dumps(report,ensure_ascii=False),flush=True)
 if not report['passed']:raise SystemExit(1)

if __name__=='__main__':main()
