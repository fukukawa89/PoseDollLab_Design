from build_stock import *
from collections import Counter
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import shutil,zipfile

def main():
 checks=[]
 def ck(n,ok):checks.append(dict(check=n,passed=bool(ok)))
 digest=sha(OUT/'production_meshes.npz');kit=load(OUT/'kit.json');a=load(OUT/'production_assembly.json')['parts'];ids={p['part_number'] for p in a};report=load(OUT/'verification/merge_review.json')
 ck('11 continuous prints and 130 standard hardware',len(kit['structural_parts'])==11 and len(kit['hardware'])==130 and len(ids)==141)
 ck('one new unified part and exactly ten byte-identical R2 prints',report['required_reprint']==['S4-P010'] and len(report['reused_prints'])==10 and all(r['byte_identical'] for r in report['reused_prints']))
 ck('all four same-frame groups reviewed',len(report['all_same_frame_print_groups_in_R2'])==4 and len(report['reviewed_fixed_pairs'])==4)
 ck('three indispensable covers remain removable',all(r['fused_cover_washer_entry_max_overlap_mm3']>1 and r['cover_removed_washer_entry_max_overlap_mm3']<.02 for r in report['reviewed_fixed_pairs'][:3]))
 ck('obsolete palm and four interface metal parts removed',not any(p['name'] in ['KEEP_E-P017','KEEP_E-H1171','KEEP_E-H1172','KEEP_E-H1173','KEEP_E-H1174'] for p in a))
 ck('no new standard hardware sizes or custom machining',kit['custom_metal_count']==kit['cut_hardware_count']==0 and set(p['sku'] for p in kit['hardware'])<=set(p['sku'] for p in load(R2/'kit.json')['hardware']))
 ck('all seven axes, offsets, limits and clocking unchanged',load(OUT/'profiles/arm_profile.json')==load(R2/'profiles/arm_profile.json'))
 for name,expected in [('stl_export','PASS_EXPORT'),('capture_assembly','PASS_GEOMETRY'),('hinge_wrist_paths','PASS_PATHS'),('module_joining','PASS_GEOMETRY'),('connected_core','PASS_SCREEN'),('motion','PASS_SAMPLED'),('motion_dense','PASS_SAMPLED'),('merge_review','PASS_MERGE_REVIEW')]:
  d=load(OUT/f'verification/{name}.json');ck(name+' final exported geometry',d['geometry_sha256']==digest and d['status']==expected)
 ck('30 named/endpoints and 850 dense finite pose checks',len(load(OUT/'verification/motion.json')['cases'])==30 and len(load(OUT/'verification/motion_dense.json')['cases'])==850)
 ep=load(OUT/'electronics/interface_reservations.json');ck('electronics envelopes checked against new geometry without release claim',ep['geometry_sha256']==digest and ep['sampled_poses']==850 and len(ep['bindings'])==6 and not ep['carrier_fabrication_released'] and not ep['electrical_accuracy_verified'])
 ck('retained magnet entry is clear',report['magnet_entry_max_overlap_mm3']<.02)
 ck('all print hashes match actual STL files',all(sha(OUT/r['stl'])==r['sha256'] for r in kit['structural_parts']))
 plates=load(OUT/'printing/plates.json')['plates'];full=[p for p in plates if not p['replacement']];upgrade=[p for p in plates if p['replacement']]
 ck('full plate has exactly eleven prints, upgrade plate only P010',len(full)==len(upgrade)==1 and Counter(i['id'] for p in full for i in p['items'])==Counter(r['part_number'] for r in kit['structural_parts']) and [i['id'] for i in upgrade[0]['items']]==['S4-P010'])
 for p in plates:
  s=load(OUT/f'verification/slice_{p["id"]}.json');ck('offline slice '+p['id'],s['passed'] and s['input_sha256']==sha(OUT/p['file']) and s['mesh_repairs']==0 and s['objects']==p['count'])
 tutorial=load(OUT/'tutorial/steps.json');ck('146 base steps cover all physical items',tutorial['steps']==146 and set(tutorial['covered_part_numbers'])==ids)
 guide=load(OUT/'assembly_guide/verification/delivery_audit.json');ck('updated 156-step standalone animation verified',guide['status']=='PASS_TUTORIAL_DELIVERY' and guide['geometry_sha256']==digest)
 gb=load(OUT/'assembly_guide/verification/browser_review.json');ck('guide assets unchanged since browser test',all(sha(OUT/'assembly_guide'/n)==d for n,d in gb['asset_sha256'].items()))
 b=load(OUT/'verification/browser_review.json');ck('whole-arm viewer matches production and tutorial',b['production_mesh_sha256']==digest and b['ready'] and b['sliders']==7 and b['steps_checked']==146 and b['restored_visible']==141 and not b['missing_current_parts'] and b['console_errors']==0 and b['reservation_visible']==153)
 ck('source inputs unchanged',all(sha(H/n)==d for n,d in load(OUT/'source_fingerprints.json').items()))
 ck('R2 frozen production hash retained',sha(R2/'production_meshes.npz')=='9bf25e08e41c3faf6107d6e558f7b25f61aa82ec839a56e2c8c25f8fdcbc965e')
 ck('original R2 guide data unchanged',sha(H/'bench/revO24E_LArm_Stock_R2_AssemblyGuide/data.js')=='927319124d2d97552bb996a321d98c5bffea1697e05e01700d516dee2e105b05')
 ck('physical performance remains unmeasured',not kit['physical_tested'] and not kit['manufacturing_release'] and all(not x['spring_force_measured'] for x in load(OUT/'verification/holding_targets.json')['rows']))
 class Links(HTMLParser):
  def __init__(self):super().__init__();self.links=[]
  def handle_starttag(self,t,attrs):self.links.extend(v for k,v in attrs if k in ['href','src'] and v)
 missing=[]
 for p in [*OUT.glob('*.html'),OUT/'preview/index.html',*list((OUT/'assembly_guide').glob('*.html'))]:
  h=Links();h.feed(p.read_text('utf8'))
  for link in h.links:
   u=urlsplit(link)
   if not u.scheme and u.path and not (p.parent/unquote(u.path)).exists():missing.append(p.name+': '+link)
 ck('all delivery links resolve',not missing)
 ck('editable and exchange 3D models present',all((OUT/p).is_file() for p in ['O24E_left_arm_stock_R4.blend','O24E_left_arm_stock_R4.glb']))
 result=dict(status='PASS_DELIVERY' if all(c['passed'] for c in checks) else 'FAIL',geometry_sha256=digest,checks=checks,missing_links=missing,physical_tested=False,manufacturing_release=False)
 put(OUT/'verification/delivery_audit.json',result);print(result['status'],[c for c in checks if not c['passed']],flush=True);assert result['status']=='PASS_DELIVERY'
 for p in HERE.glob('*.py'):shutil.copyfile(p,OUT/'source'/p.name)
 (OUT/'README.txt').write_text('O24E R3 — 固定分件合并版\n从 START_HERE.html 开始；MERGE_REVIEW.html 解释4组固定连接的去留。\n相对R2，只需新打印S4-P010一体腕输出叉与手掌，替代S2-P010和S2-P011。其余10个R2打印件逐字节相同，可直接复用。编号P011撤销，P012不改号。\n整臂11个打印件＋130件标准五金，减少M2×20一颗、W2两片、NL2一颗。旧R2分件若继续使用，仍需原4件掌部五金。\nprinting/R3_REPRINT_P010.3mf是单件升级盘；printing/STOCK_ARM_01.3mf是整臂11件盘，二选一。\nassembly_guide/index.html是156步安装动画，R3_Assembly_Offline.html为内嵌单文件动画。preview/index.html提供七轴整臂检查及电子空间预留开关。\n原R2、原R2教程和更早设计保留。H/W用户接受状态不变。几何、装配与切片已检查；实际保持力、配合、打印强度、蠕变与耐久未实测。电子附件仍未发布生产版本。\nsource可追溯，重建需原仓库冻结输入、Python、Blender、Orca。顺序：build_stock → export_stock → check_stock（默认、--dense）→ validate_stock（默认、--joins、--cores）→ check_modules → merge_review → load_stock → print_stock → render_stock（Blender）→ electronics_review → deliver_r3 → guide源码build/verify/docs → 浏览器实测 → package_guide → audit_r3。\n',encoding='utf8')
 def include(p):return p.is_file() and p.suffix not in ['.zip','.blend1','.pyc'] and 'slicer_work' not in p.parts and '__pycache__' not in p.parts and not (p.parent==OUT and p.name=='checksums.json') and p!=OUT/'verification/package_audit.json'
 files=[p for p in OUT.rglob('*') if include(p)];put(OUT/'checksums.json',{p.relative_to(OUT).as_posix():sha(p) for p in files});files.append(OUT/'checksums.json');target=OUT/'O24E_left_arm_stock_R4.zip'
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in sorted(files):z.write(p,p.relative_to(OUT).as_posix())
 with zipfile.ZipFile(target) as z:
  bad=z.testzip();m=json.loads(z.read('checksums.json'));ok=all(hashlib.sha256(z.read(n)).hexdigest()==d for n,d in m.items())
 put(OUT/'verification/package_audit.json',dict(status='PASS_PACKAGE' if bad is None and ok else 'FAIL',files=len(files),bytes=target.stat().st_size,sha256=sha(target),crc_error=bad,all_manifest_hashes_match=ok));assert bad is None and ok;print('ZIP',len(files),target.stat().st_size,flush=True)
if __name__=='__main__':main()
