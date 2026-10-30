from build_stock import *
from collections import Counter
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import shutil,zipfile

def audit():
 checks=[]
 def ck(n,ok):checks.append(dict(check=n,passed=bool(ok)))
 kit=load(OUT/'kit.json');a=load(OUT/'production_assembly.json');digest=sha(OUT/'production_meshes.npz');ids={r['part_number'] for r in kit['structural_parts']+kit['hardware']}
 ck('12 unique continuous prints and 134 standard hardware',len(kit['structural_parts'])==12 and len(kit['hardware'])==134 and len(ids)==146)
 ck('zero custom or cut hardware',kit['custom_metal_count']==0 and kit['cut_hardware_count']==0 and all(not r['custom_or_secondary_operation'] for r in kit['hardware']))
 ck('mechanical parts only',all(p['role'] not in ['pcb','connector','magnet'] for p in a['parts']))
 ck('source design outputs unchanged',all(sha(H/n)==d for n,d in load(OUT/'source_fingerprints.json').items()))
 ck('original O24D frozen geometry unchanged',sha(H/'bench/revO24D/assembly_meshes.npz')=='fd64f061821a42f803e2131b0f0642147ab9cc8e65dc32cdb5e3476a0b7c9e8e')
 ck('all seven UE nodes, limits and zero clocking retained',load(OUT/'profiles/arm_profile.json')==load(SRC/'profiles/arm_profile.json'))
 for name,expected in [('stl_export','PASS_EXPORT'),('connected_core','PASS_SCREEN'),('capture_assembly','PASS_GEOMETRY'),('hinge_wrist_paths','PASS_PATHS'),('module_joining','PASS_GEOMETRY'),('motion','PASS_SAMPLED'),('motion_dense','PASS_SAMPLED')]:
  r=load(OUT/f'verification/{name}.json');ck(name+' final geometry',r['geometry_sha256']==digest and r['status']==expected)
 ck('finite motion coverage',len(load(OUT/'verification/motion.json')['cases'])==30 and len(load(OUT/'verification/motion_dense.json')['cases'])==850)
 placed=[]
 plates=load(OUT/'printing/plates.json')['plates']
 for p in plates:
  r=load(OUT/f'verification/slice_{p["id"]}.json');ck('offline slice '+p['id'],r['passed'] and r['input_sha256']==sha(OUT/p['file']) and r['mesh_repairs']==0 and r['objects']==p['count']);placed.extend(i['id'] for i in p['items'])
 ck('one plate, one copy per print',len(plates)==1 and Counter(placed)==Counter(r['part_number'] for r in kit['structural_parts']))
 ck('print STL hashes consistent',all(sha(OUT/r['stl'])==r['sha256'] for r in kit['structural_parts']))
 t=load(OUT/'tutorial/steps.json');ck('151 tutorial steps cover all physical items',t['steps']==151 and set(t['covered_part_numbers'])==ids)
 wm=t['modules'][-1];loc={n:i for i,s in enumerate(wm['steps']) for n in s['new_part_numbers']};oldkit=load(SRC/'kit.json');oldby={r['feature']:r['part_number'] for r in oldkit['hardware']};newby={r['feature']:r['part_number'] for r in kit['hardware']}
 joinindex=next(i for i,s in enumerate(wm['steps']) if '已备好内层五金' in s['title']);ck('all wrist inner metal is installed before fork closure',all(loc[newby['KEEP_'+oldby['l_E_'+pre+suf]]]<joinindex for pre in ['WYM_','WYP_','WXM_','WXP_'] for suf in ['N','RW','K1','K2','F1']))
 class Links(HTMLParser):
  def __init__(self):super().__init__();self.links=[]
  def handle_starttag(self,tag,attrs):self.links.extend(v for k,v in attrs if k in ['src','href'] and v)
 missing=[]
 for p in [*OUT.glob('*.html'),OUT/'preview/index.html']:
  h=Links();h.feed(p.read_text('utf8'))
  for link in h.links:
   url=urlsplit(link)
   if not url.scheme and url.path and not (p.parent/unquote(url.path)).exists():missing.append(str(p)+': '+link)
 ck('all HTML links resolve',not missing)
 browser=load(OUT/'verification/browser_review.json');ck('browser displays actual final meshes and all steps',browser['production_mesh_sha256']==digest and browser['ready'] and browser['sliders']==7 and browser['restored_visible']==146 and browser['steps_checked']==151 and not browser['missing_current_parts'] and browser['console_errors']==0)
 ck('editable and exchange assembly present',all((OUT/n).is_file() for n in ['O24E_left_arm_stock.blend','O24E_left_arm_stock.glb']))
 ck('physical performance remains explicitly unmeasured',not kit['physical_tested'] and all(not r['spring_force_measured'] for r in load(OUT/'verification/holding_targets.json')['rows']))
 result=dict(status='PASS_DELIVERY' if all(c['passed'] for c in checks) else 'FAIL',geometry_sha256=digest,checks=checks,missing_links=missing,physical_tested=False,manufacturing_release=False);put(OUT/'verification/delivery_audit.json',result);print(result['status'],[c for c in checks if not c['passed']],flush=True);assert result['status']=='PASS_DELIVERY'
 return result

def package():
 for p in HERE.glob('*.py'):shutil.copyfile(p,OUT/'source'/p.name)
 (OUT/'README.txt').write_text('O24E_LArm_Stock — O22 / T6 常见五金左臂试装\n从 START_HERE.html 开始。新目录不覆盖原 O24E 或旧单臂。\n12个打印件，134件标准五金，1个A1 mini 3MF盘。无电路。\n先看 HARDWARE.html 核实规格及库存；旧55件加工项见 CHANGES.html。\nSTL / Blender / GLB / 逐件教程 / 计算验证 / 空白试装表均包含。\n防脱与装配为几何验证，保持力、真实A8曲线、PLA蠕变和100次循环待实装。\nsource为可追溯脚本，需原仓库中的冻结 O24E/T6/O22 输入及 Python、Blender、Orca。\n重建顺序：build_stock → export_stock → validate_stock（默认、--joins、--cores）→ check_modules → check_stock（默认、--dense）→ load_stock → print_stock → render_stock（Blender）→ section_stock → deliver_stock → 浏览器核对 → audit_stock。\n',encoding='utf8')
 def include(p):return p.is_file() and p.suffix not in ['.zip','.blend1','.pyc'] and 'slicer_work' not in p.parts and p.name not in ['package_audit.json','checksums.json']
 files=[p for p in OUT.rglob('*') if include(p)];manifest={p.relative_to(OUT).as_posix():sha(p) for p in files};put(OUT/'checksums.json',manifest);files.append(OUT/'checksums.json')
 target=OUT/'O24E_left_arm_stock.zip'
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in sorted(files):z.write(p,p.relative_to(OUT).as_posix())
 with zipfile.ZipFile(target) as z:
  bad=z.testzip();m=json.loads(z.read('checksums.json'));ok=all(hashlib.sha256(z.read(n)).hexdigest()==d for n,d in m.items())
 put(OUT/'verification/package_audit.json',dict(status='PASS_PACKAGE' if bad is None and ok else 'FAIL',files=len(files),bytes=target.stat().st_size,sha256=sha(target),crc_error=bad,all_manifest_hashes_match=ok));assert bad is None and ok;print('ZIP',len(files),target.stat().st_size,flush=True)
if __name__=='__main__':audit();package()
