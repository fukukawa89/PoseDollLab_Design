from build_guide import *
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import zipfile

def main():
    digest=sha(SOURCE/'production_meshes.npz');d=load(DEST/'steps.json');r=load(DEST/'verification/assembly_paths.json');b=load(DEST/'verification/browser_review.json');checks=[]
    def ck(n,ok):checks.append(dict(check=n,passed=bool(ok)))
    ck('production digest and immutable input fingerprints',d['geometry_sha256']==digest and all(sha(H/n)==v for n,v in load(DEST/'source_fingerprints.json').items()))
    ck('201 supported steps geometrically checked',len(d['steps'])==201 and r['status']=='PASS_GUIDE_GEOMETRY' and r['geometry_sha256']==digest)
    ck('603 browser render states, 153 directions, 147 final installed parts',b['steps']==201 and b['render_states']==603 and b['part_orientations']==153 and b['final_visible']==147 and b['final_shoulder_abduction_deg']==45 and not b['errors'])
    ck('all playback controls tested',all(b['playback'][k] for k in ['play_moves','pause_stable','replay_moves','continuous_advanced']) and not b['playback']['errors'] and b['console_errors']==0)
    ck('viewer assets identical to browser-reviewed files',all(sha(DEST/n)==v for n,v in b['asset_sha256'].items()))
    spring=[]
    for group,ps in d['spring_groups'].items():
        if group=='RP':
            one=[p for p in ps if '_A8_1_' in p['feature']];two=[p for p in ps if '_A8_2_' in p['feature']];ok=len(one)==len(two)==2 and np.dot(one[0]['direction'],one[1]['direction'])>.99 and np.dot(two[0]['direction'],two[1]['direction'])>.99 and np.dot(one[0]['direction'],two[0]['direction'])<-.99
        else:ok=len(ps)==2 and np.dot(ps[0]['direction'],ps[1]['direction'])<-.99
        spring.append(dict(group=group,passed=bool(ok),members=ps))
    ck('all 24 spring orientation arrows checked from actual rims',sum(len(s['members']) for s in spring)==24 and all(s['passed'] for s in spring));put(DEST/'verification/spring_orientation.json',dict(geometry_sha256=digest,groups=spring))
    single=(DEST/'index.html').read_text('utf8').replace('<link rel="stylesheet" href="style.css">','<style>'+(DEST/'style.css').read_text('utf8')+'</style>')
    for n in ['data.js','guide.js','enhance.js']:single=single.replace(f'<script src="{n}"></script>','<script>'+(DEST/n).read_text('utf8')+'</script>')
    (DEST/'R4_Assembly_Offline.html').write_text(single,encoding='utf8');ck('single-file viewer embeds all scripts and geometry',not re.search(r'<script\b[^>]*\bsrc=',single) and 'window.ARM_GUIDE=' in single and 'window.GUIDE_API=' in single)
    class Links(HTMLParser):
        def __init__(self):super().__init__();self.links=[]
        def handle_starttag(self,t,attrs):self.links.extend(v for k,v in attrs if k in ['href','src'] and v)
    missing=[]
    for p in DEST.glob('*.html'):
        h=Links();h.feed(p.read_text('utf8'))
        for link in h.links:
            u=urlsplit(link)
            if not u.scheme and u.path and not (p.parent/unquote(u.path)).exists():missing.append(p.name+': '+link)
    ck('all local links resolve',not missing)
    result=dict(status='PASS_TUTORIAL_DELIVERY' if all(c['passed'] for c in checks) else 'FAIL',geometry_sha256=digest,checks=checks,missing_links=missing,scope='HTTP browser runtime checked. Offline single-file asset completeness checked; native file: launch has not been tested. No actual human assembly or retention-force claim.')
    put(DEST/'verification/delivery_audit.json',result);print(result['status'],[c for c in checks if not c['passed']],flush=True);assert result['status']=='PASS_TUTORIAL_DELIVERY'
    for n in ['build_guide.py','verify_r4.py','docs_guide.py','package_r4.py','index.html','style.css','guide.js','enhance.js']:shutil.copyfile(HERE/n,DEST/'source'/n)
    (DEST/'README.txt').write_text('O24E R4 · 201步单臂安装动画\n打开 index.html，或内嵌单文件 R4_Assembly_Offline.html。后者已核对资源完整性，尚未实测系统file:方式启动。\n11个整臂打印件＋136件五金；另打印J001托叉、J002导向针各1件重复使用。动画里的RP/RU/RF工具实例不代表三份物料。\n新增留片检查8处；运动关节仍用NL3，六支压盖螺钉采用12颗普通M3对顶。\n准备软口台钳／桌夹、有效直杆≥120 mm的3 mm内六角、2.5 mm内六角，以及两把5.5 mm薄开口扳手（厚≤2 mm）。\n右侧放大图核对各片方向；主视图前三章的蓝色箭头为实际朝上方向。托叉只承托，不用于压簧。\n验证报告区分实体路径、预期定位筋压配、浏览器检查和待做的实物试装。\n完整打印件、3MF、清单在上一层主交付包。旧R3不变。\n',encoding='utf8')
if __name__=='__main__':main()
