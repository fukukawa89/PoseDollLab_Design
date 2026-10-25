"""Freeze the T6 delivery only after CAD, slicing and actual browser checks."""
from arm_kit import *
import re,zipfile,shutil,collections,xml.etree.ElementTree as ET

def main():
 raw=(ROOT/'output/playwright/o24ct6-browser-raw.txt').read_text('utf-8-sig');assert '### Result\n' in raw
 browser=json.JSONDecoder().raw_decode(raw.split('### Result\n',1)[1].lstrip())[0]
 geo=sha(OUT/'assembly_meshes.npz');assert browser['passed'] and browser['geometry_sha256']==geo
 data=json.loads((OUT/'assembly.json').read_text('utf8'));P={p['id']:p for p in data['parts']};checks={};maxerr=0.
 for state in browser['states']:
  q,r,w,v=state['angles'];F=transforms('arm' if state['mode']=='arm' else 'three',q,r,w,v)
  for id,mat in state['transforms'].items():
   p=P[id];expected=F[p['station']][p['frame']]
   if state['mode'] not in ['arm','three']:expected=a.T([-{'H':-65,'R':0,'W':65}[p['station']],0,0])@expected
   maxerr=max(maxerr,float(np.max(np.abs(expected-np.array(mat).reshape(4,4)))))
 checks['browser_matches_CAD_transforms']=maxerr<1e-10
 put(OUT/'verification/browser.json',dict(passed=browser['passed'] and maxerr<1e-10,geometry_sha256=geo,steps=browser['steps'],pose_states=len(browser['states']),max_matrix_error=maxerr,errors=browser['errors'],mobile_no_overflow=not browser['mobile']['overflow'],offline_ready=browser['offline']['ready']))
 reports=['geometry','installed_rom','bench_rom','module_insertion','ue_alignment','mechanics','slicing','blender','browser','combined_printing','tutorial_paths','tutorial_browser','reuse']
 for name in reports:
  r=json.loads((OUT/'verification'/(name+'.json')).read_text('utf8'));checks[name]=bool(r['passed']) and r.get('geometry_sha256',geo)==geo
 printed=[p for p in data['parts'] if p['printable']]
 checks['exact_STL_inventory']={p.name for p in (OUT/'stl_print').glob('*.stl')}=={p['id']+'.stl' for p in printed}
 checks['STL_hashes']=all(sha(OUT/p['stl'])==p['stl_sha256'] for p in printed)
 checks['printed_count']=len(printed)==14 and sum(not p['bench_only'] for p in printed)==9
 meshes={r['id']:trimesh.load(OUT/r['stl'],process=True) for r in printed}
 checks['all_prints_watertight_connected_positive']=all(m.is_watertight and m.volume>0 and len(m.split(only_watertight=False))==1 for m in meshes.values())
 model=trimesh.load(OUT/'O24C_T6_installed_forearm.glb',force='scene');checks['GLB_parts']=len(model.geometry)==94
 d=build();F=transforms();pts=[]
 for p in d.parts:
  if not p['bench_only']:pts.append(np.array(moved(p['s'],F[p['station']][p['frame']]).bounding_box()).reshape(2,3))
 expected=np.array([np.min([x[0] for x in pts],axis=0),np.max([x[1] for x in pts],axis=0)])
 checks['GLB_mm_scale']=bool(np.max(np.abs(model.bounds*1000-expected))<.002)
 viewer=json.loads((OUT/'viewer/data.js').read_text('utf8')[len('window.KIT='):-1]);checks['same_mesh_viewer']=viewer['geometry_sha256']==geo and [p['id'] for p in viewer['parts']]==list(P)
 counts=dict(collections.Counter(p['sku'] for p in data['parts'] if p['sku']))
 checks['BOM_counts']=counts=={r['sku']:r['qty'] for r in json.loads((OUT/'BOM.json').read_text('utf8'))}
 delta=json.loads((OUT/'hardware_delta_from_T5.json').read_text('utf8'));checks['exact_hardware_changes']={r['sku']:r['delta'] for r in delta if r['delta']}=={'NL3':7,'N3':-7,'RW3':-7,'W3':7,'W4':14}
 sliced=json.loads((OUT/'verification/slicing.json').read_text('utf8'));plates=json.loads((OUT/'printing/plates.json').read_text('utf8'))['plates']
 checks['project_hashes']=all(sha(OUT/p['file'])==p['sha256']==next(r['input_sha256'] for r in sliced['plates'] if r['id']==p['id']) for p in plates)
 checks['exact_three_replacements']={p['id'] for p in plates[0]['items']}=={'H6-01','R6-01','W6-01'}
 checks['exact_fit_coupon']={p['id'] for p in plates[1]['items']}=={'C6-01'}
 combined=json.loads((OUT/'printing/combined_plate.json').read_text('utf8'))['plates'][0];rep=json.loads((OUT/'verification/combined_printing.json').read_text('utf8'))
 checks['combined_project_hash']=sha(OUT/combined['file'])==combined['sha256']==rep['plate']['input_sha256']
 checks['combined_exact_14_prints']={i['id'] for i in combined['items']}==set(meshes) and len(combined['items'])==14
 checks['combined_preserves_print_faces']=all(np.allclose(np.array(i['transform'])[:3,2],[0,0,1]) and abs(np.linalg.det(np.array(i['transform'])[:3,:3])-1)<1e-8 for i in combined['items'])
 # Read the embedded objects independently and compare to the delivered STL.
 embedded=[];Q='{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}'
 for plate in plates+[combined]:
  ids=[]
  with zipfile.ZipFile(OUT/plate['file']) as z:
   for name in z.namelist():
    if not name.startswith('3D/Objects/'):continue
    root=ET.fromstring(z.read(name));ob=root.find('.//'+Q+'object');id=ob.attrib['name'];ids.append(id);m=meshes[id]
    vv=np.array([[float(e.attrib[k]) for k in ['x','y','z']] for e in ob.findall('.//'+Q+'vertex')]);ff=np.array([[int(e.attrib[k]) for k in ['v1','v2','v3']] for e in ob.findall('.//'+Q+'triangle')])
    embedded.append(vv.shape==m.vertices.shape and ff.shape==m.faces.shape and np.max(abs(vv-m.vertices))<1e-7 and np.array_equal(ff,m.faces))
  embedded.append(set(ids)=={i['id'] for i in plate['items']})
 checks['embedded_3MF_matches_delivered_STLs']=all(embedded)
 tutorial_browser=json.loads((OUT/'verification/tutorial_browser.json').read_text('utf8'))
 checks['tutorial_final_assets_tested']=all(sha(OUT/'tutorial'/name)==digest for name,digest in tutorial_browser['checked_assets'].items())
 links=[];missing=[]
 for p in list(OUT.glob('*.html'))+list((OUT/'viewer').glob('*.html'))+list((OUT/'tutorial').glob('*.html')):
  for rel in re.findall(r'(?:href|src)="([^"]+)"',p.read_text('utf8')):
   if rel.startswith(('http','data:','#')):continue
   target=p.parent/rel.split('#')[0].split('?')[0];links.append(str(target))
   if target.name=='O24C-T6_print_and_assembly.zip' or target==OUT/'verification/delivery.json':continue
   if not target.exists():missing.append(str(target))
 checks['local_links']=not missing
 source=OUT/'source';source.mkdir(exist_ok=True)
 for p in HERE.iterdir():
  if p.suffix in ['.py','.js','.html','.css']:shutil.copyfile(p,source/p.name)
 rebuild='''T6 source snapshots belong at Hardware/PoseDoll44/cad/revO24C_T6 in the original repository.
Dependencies: revO24C_T4 / T3 / T1 / revO24 helpers, repository .venv, scripts/verify_revo22_a1mini.py,
O22 A1mini 3MF template, Blender and local OrcaSlicer. This is not a standalone source installer.
Print STL/3MF and offline HTML/tutorial need none of those development dependencies.
Order: arm_kit.py; audit.py; assembly_checks.py; bench_checks.py; tutorial.py;
tutorial_checks.py; print_projects.py; combined_print.py; Blender --python render.py;
publish.py; docs.py. Serve bench/revO24C_T6 on localhost:8782 for browser review.
Use Playwright CLI with tutorial_browser_review.js and browser_review.js; save raw results to
output/playwright/o24ct6-tutorial-browser-raw.txt and o24ct6-browser-raw.txt.
Then verify_tutorial_browser.py and verify_delivery.py; lastly call publish.package().
No file has been sent to a printer. Physical T6 test remains pending.
'''
 (source/'REBUILD.txt').write_text(rebuild,encoding='utf8');(OUT/'REBUILD.txt').write_text(rebuild,encoding='utf8')
 result=dict(passed=all(checks.values()),geometry_sha256=geo,checks=checks,printed_parts=14,actual_joint_prints=9,reprinted_parts=['H6-01','R6-01','W6-01'],detachable_tools=4,optional_coupon=1,link_count=len(links),missing_links=missing,GLB_bounds_mm=(model.bounds*1000).tolist(),user_feedback=data['user_feedback'],physical_tests_passed=False)
 put(OUT/'verification/delivery.json',result);print(json.dumps(dict(passed=result['passed'],checks=checks,missing_links=missing),ensure_ascii=False),flush=True)
 if not result['passed']:raise SystemExit(1)

if __name__=='__main__':main()
