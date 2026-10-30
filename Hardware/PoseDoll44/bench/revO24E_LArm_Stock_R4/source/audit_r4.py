from build_stock import *
from collections import Counter
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import shutil,zipfile

def main():
    checks=[]
    def ck(n,ok):checks.append(dict(check=n,passed=bool(ok)))
    digest=sha(OUT/'production_meshes.npz');kit=load(OUT/'kit.json');a=load(OUT/'production_assembly.json')['parts'];counts=Counter(p['sku'] for p in kit['hardware']);tools=load(OUT/'tooling/kit.json')['parts'];rep=load(OUT/'verification/assembly_usability.json')
    ck('11 arm prints, 136 hardware, 2 reusable printed aids',len(kit['structural_parts'])==11 and len(kit['hardware'])==136 and len(a)==147 and len(tools)==2)
    ck('12 ordinary cover nuts and 11 retained joint locknuts',counts['N3']==12 and counts['NL3']==11 and counts['M3x16']==6)
    ck('no custom metal or cut hardware',kit['custom_metal_count']==kit['cut_hardware_count']==0)
    ck('exactly three changed arm prints and eight byte-identical reuses',rep['required_reprint']==['S4-P005','S4-P007','S4-P012'] and len(rep['reused_prints'])==8 and all(p['byte_identical'] for p in rep['reused_prints']))
    for n,expected in [('stl_export','PASS_EXPORT'),('assembly_usability','PASS_DESIGN_GEOMETRY'),('connected_core','PASS_SCREEN'),('motion','PASS_SAMPLED'),('motion_dense','PASS_SAMPLED')]:
        d=load(OUT/f'verification/{n}.json');ck(n+' uses final geometry',d['geometry_sha256']==digest and d['status']==expected)
    ck('30 named/endpoints plus 850 sampled motion cases',len(load(OUT/'verification/motion.json')['cases'])==30 and len(load(OUT/'verification/motion_dense.json')['cases'])==850)
    e=load(OUT/'electronics/interface_reservations.json');ck('electronic reservations checked without fabrication-release claim',e['geometry_sha256']==digest and e['sampled_poses']==850 and len(e['bindings'])==6 and not e['carrier_fabrication_released'])
    ck('source R3 geometry and guide remain unchanged',all(sha(H/n)==v for n,v in load(OUT/'source_fingerprints.json').items()) and sha(R2/'production_meshes.npz')=='131f5773614d53e33adcd16ac34a69802cda4ff049abefa3ada9da397af0b0d9')
    ck('all exported print and aid hashes match',all(sha(OUT/p['stl'])==p['sha256'] for p in kit['structural_parts']+tools))
    plates=load(OUT/'printing/plates.json')['plates'];full=[p for p in plates if not p['replacement']];upgrade=[p for p in plates if p['replacement']]
    ck('full plate includes arm plus reusable aids once',Counter(i['id'] for p in full for i in p['items'])==Counter(p['part_number'] for p in kit['structural_parts']+tools))
    ck('upgrade plate has exactly three replacements and two aids',len(upgrade)==1 and set(i['id'] for i in upgrade[0]['items'])=={'S4-P005','S4-P007','S4-P012','R4-J001','R4-J002'})
    for p in plates:
        d=load(OUT/f'verification/slice_{p["id"]}.json');ck('offline slice '+p['id'],d['passed'] and d['input_sha256']==sha(OUT/p['file']) and d['objects']==p['count'] and d['mesh_repairs']==0)
    g=load(OUT/'assembly_guide/verification/delivery_audit.json');ck('201-step tool-aware tutorial delivered',g['status']=='PASS_TUTORIAL_DELIVERY' and g['geometry_sha256']==digest)
    b=load(OUT/'verification/browser_review.json');ck('whole-arm browser and all seven axes verified',b['ready'] and b['geometry_sha256']==digest and b['sliders']==7 and b['pose_count']==30 and b['max_matrix_error']<1e-8 and b['default_visible']==147 and b['reservation_visible']==159 and not b['errors'] and b['console_errors']==0)
    ck('actual R4 assembly and new interference-fit forces not falsely marked tested',not kit['physical_tested'] and not kit['manufacturing_release'] and all(not x['physical_retention_tested'] for x in rep['temporary_retention']))
    class Links(HTMLParser):
        def __init__(self):super().__init__();self.links=[]
        def handle_starttag(self,t,attrs):self.links.extend(v for k,v in attrs if k in ['href','src'] and v)
    missing=[]
    for p in [*OUT.glob('*.html'),OUT/'preview/index.html',*list((OUT/'assembly_guide').glob('*.html'))]:
        h=Links();h.feed(p.read_text('utf8'))
        for link in h.links:
            u=urlsplit(link)
            if not u.scheme and u.path and not (p.parent/unquote(u.path)).exists():missing.append(p.name+': '+link)
    ck('all local delivery links resolve',not missing);ck('editable and exchange assembly models present',all((OUT/n).is_file() for n in ['O24E_left_arm_stock_R4.blend','O24E_left_arm_stock_R4.glb']))
    result=dict(status='PASS_DELIVERY' if all(c['passed'] for c in checks) else 'FAIL',geometry_sha256=digest,checks=checks,missing_links=missing,physical_tested=False,manufacturing_release=False)
    put(OUT/'verification/delivery_audit.json',result);print(result['status'],[c for c in checks if not c['passed']],flush=True);assert result['status']=='PASS_DELIVERY'
    names=['build_stock.py','export_stock.py','tooling.py','assembly_plan.py','check_stock.py','check_r4.py','validate_stock.py','load_stock.py','print_stock.py','render_stock.py','electronics_review.py','deliver_stock.py','deliver_r4.py','audit_r4.py']
    for n in names:shutil.copyfile(HERE/n,OUT/'source'/n)
    (OUT/'README.txt').write_text('O24E R4 — 根据R3实际装配反馈修改\n从 START_HERE.html 开始；新动画在 assembly_guide/index.html（201步）。\nR3升级：替换重打P005、P007、P012，另打印J001托叉和J002导向针各1；其余8件STL逐字节复用。\nprinting/R4_REPRINT_3_PLUS_2.3mf为5件升级盘；printing/STOCK_ARM_01.3mf为11个整臂零件＋2个工装的完整盘，二选一。\n压盖复用原M3×16和W3，反向安装后用12颗普通M3（AF5.5×2.4）对顶；原6颗压盖NL3留作备件。关节的11颗NL3继续保留。\n准备两把5.5薄开口扳手、3mm有效直杆至少120mm内六角、2.5mm内六角，以及软口台钳／桌夹。\n托叉只承托散件，不用于压簧；肩钉捕获后抽出托叉，再预紧。定位筋只负责临时留片；8面必须在开放台面先压入并轻翻转不掉片，再合叉。\n逐步路径、指腹与工具包络、防脱、850姿态、打印工程、浏览器已核对；新实物配合／留片力／双螺母保持／疲劳未实测。已接受T6 H/W的状态不变。电子预留保留，附件仍未发布生产版。\n完整重建：build_stock → export_stock → tooling → check_stock（默认及--dense）→ validate_stock --cores → check_r4 → load_stock → electronics_review → print_stock → render_stock（Blender）→ guide build/verify_r4 → deliver_r4 → guide build/verify_r4/docs → 浏览器核对 → guide package_r4 → audit_r4。依赖原仓库冻结输入及Python/Blender/Orca。\n旧R3与旧动画均保留。\n',encoding='utf8')
    def include(p):return p.is_file() and p.suffix not in ['.zip','.blend1','.pyc'] and 'slicer_work' not in p.parts and '__pycache__' not in p.parts and p.name not in ['checksums.json','package_audit.json']
    files=[p for p in OUT.rglob('*') if include(p)];put(OUT/'checksums.json',{p.relative_to(OUT).as_posix():sha(p) for p in files});files.append(OUT/'checksums.json');target=OUT/'O24E_left_arm_stock_R4.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(files):z.write(p,p.relative_to(OUT).as_posix())
    with zipfile.ZipFile(target) as z:
        bad=z.testzip();manifest=json.loads(z.read('checksums.json'));ok=all(hashlib.sha256(z.read(n)).hexdigest()==v for n,v in manifest.items())
    put(OUT/'verification/package_audit.json',dict(status='PASS_PACKAGE' if bad is None and ok else 'FAIL',files=len(files),bytes=target.stat().st_size,sha256=sha(target),crc_error=bad,all_manifest_hashes_match=ok));assert bad is None and ok;print('ZIP',len(files),target.stat().st_size,flush=True)
if __name__=='__main__':main()
