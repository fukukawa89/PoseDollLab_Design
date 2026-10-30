"""Finalize browser evidence, links, source snapshot and a cache-free delivery ZIP."""
from common import *
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import zipfile
from release_docs import run as docs

def run():
    browser_output=(H.parents[1]/'output/playwright/r5-review-output.txt').read_text('utf-8-sig')
    result=json.loads(browser_output.split('### Result',1)[1].strip().splitlines()[0])
    current=sha(OUT/'production_meshes.npz')
    assert result['passed'] and result['guide']['geometry_sha256']==current and result['viewer']['geometry_sha256']==current
    result['geometry_sha256']=current;result['screenshots']=[]
    for name in ['r5-guide.png','r5-viewer-wiring.png','r5-wrist.png','r5-start.png']:
        shutil.copyfile(H.parents[1]/'output/playwright'/name,OUT/'images'/name);result['screenshots'].append('images/'+name)
    put(OUT/'verification/browser_review.json',result)
    for name in ['motion_prototype','assembly_paths','baseline_audit']:
        r=load(OUT/f'verification/{name}.json');assert r['passed'] and r['geometry_sha256']==current,(name,r)
    assert load(OUT/'verification/stl_export.json')['geometry_sha256']==current
    plates=load(OUT/'printing/plates.json')['plates'];slicing=load(OUT/'verification/slicing.json')
    assert slicing['passed']
    for p in plates:
        assert p['sha256']==sha(OUT/p['file'])
        assert next(r['input_sha256'] for r in slicing['plates'] if r['id']==p['id'])==p['sha256']
        assert all(x['stl_sha256']==sha(OUT/x['stl']) for x in p['items'])
    for name in ['electronics_tests','calibration_software_tests']:assert load(OUT/f'verification/{name}.json')['passed']
    assert sha(BASE/'production_meshes.npz')=='de73b1fb747faa73d77f735215eed157c6503b94efe380b91477f848450ccdfa'
    docs()
    excludes={'probe.py','layout_search.py','search_clocks.py','search_wd_sides.py','clock_ru.py'}
    for f in HERE.iterdir():
        if f.is_file() and f.name not in excludes and f.suffix in ['.py','.inc','.js']:shutil.copyfile(f,OUT/'source'/f.name)
    shutil.copyfile(H/'docs/R4_MECHANICAL_FEEDBACK_20261030.json',OUT/'verification/R4_MECHANICAL_FEEDBACK_20261030.json')
    class Links(HTMLParser):
        def __init__(self):super().__init__();self.links=[]
        def handle_starttag(self,tag,attrs):
            for k,v in attrs:
                if k in ['href','src'] and v:self.links.append(v)
    missing=[];total=0
    htmls=list(OUT.glob('*.html'))+[OUT/'preview/index.html',OUT/'assembly_guide/index.html',OUT/'assembly_guide/STEP_CARDS.html']
    for f in htmls:
        parser=Links();parser.feed(f.read_text('utf8'))
        for u in parser.links:
            p=urlsplit(u)
            if p.scheme or p.netloc or not p.path:continue
            total+=1
            if not (f.parent/unquote(p.path)).resolve().exists():missing.append([str(f.relative_to(OUT)),u])
    put(OUT/'verification/release_links.json',dict(passed=not missing,local_links_checked=total,missing=missing))
    assert not missing,missing
    skipped_reports={'zero_prototype.json','tmag5170.pdf','tmag_spi.png'}
    package='O24E_R5_Arm_Sensing_20261030.zip'
    files=[]
    for p in OUT.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(OUT)
        if rel.parts[0]=='verification' and (len(rel.parts)>2 or p.name in skipped_reports):continue
        if p.name in [package,'release_checksums.json'] or p.suffix in ['.blend1','.pyc','.log']:continue
        if '__pycache__' in rel.parts:continue
        files.append(p)
    put(OUT/'release_checksums.json',dict(geometry_sha256=current,files={p.relative_to(OUT).as_posix():sha(p) for p in files},physical_R5_validation=False))
    with zipfile.ZipFile(OUT/package,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files+[OUT/'release_checksums.json']:z.write(p,'O24E_R5_Arm_Sensing/'+p.relative_to(OUT).as_posix())
    with zipfile.ZipFile(OUT/package) as z:assert z.testzip() is None
    print('FINAL',current,'files',len(files)+1,'ZIP MB',round((OUT/package).stat().st_size/1e6,2),'local links',total,flush=True)

if __name__=='__main__':run()

