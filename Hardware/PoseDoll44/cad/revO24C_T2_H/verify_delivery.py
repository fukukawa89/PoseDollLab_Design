"""Independent viewer transformations, actual lesson assembly paths and delivery links."""
from spring_hinge import *
from publish import lessons
from verify import overlap,EPS
from html.parser import HTMLParser
from urllib.parse import unquote,urlsplit
import itertools,re,zipfile,shutil

def point(path,t):
    k=min(len(path)-2,int(t*(len(path)-1)));f=t*(len(path)-1)-k
    return np.array(path[k])*(1-f)+np.array(path[k+1])*f

def transform(id,offset):
    theta=0;center=np.zeros(3)
    if id=='AX01':theta=min(3.6,max(0,offset[1]))/.5*360
    elif id.startswith('C_S'):
        theta=max(-3.5,min(0,offset[1]))/.5*360
        center=np.array([-14 if id=='C_S1' else 14,0,0])
    return a.T(offset+center)@rot(Y,theta)@a.T(-center)

def main():
    parts={p['id']:p['s'] for p in build()};steps=lessons();placed={};bad=[];samples=0
    for st in steps:
        moving=st['ids'] if st['kind'] in ['add','move'] else []
        if not moving:continue
        path=st['path'];maximum=max(np.linalg.norm(np.subtract(q,p)) for p,q in zip(path,path[1:]));count=max(1,math.ceil(maximum/.25))*(len(path)-1)+1
        for t in np.linspace(0,1,count):
            off=point(path,t);samples+=1
            for id in moving:
                s=moved(parts[id],transform(id,off))
                for other,at in placed.items():
                    if other in moving:continue
                    v=overlap(s,parts[other].translate(at))
                    if v>EPS:bad.append(dict(step=st['number'],t=float(t),pair=[id,other],volume_mm3=v))
        for id in moving:placed[id]=np.array(path[-1])
    assert set(placed)==set(parts) and all(np.linalg.norm(p)<1e-8 for p in placed.values())
    assert not bad,bad[:10]
    raw=(ROOT/'output/playwright/o24ct2h-browser.json').read_text('utf-8-sig');browser=json.loads(raw)
    assert browser['passed'] and browser['geometry_sha256']==sha(OUT/'assembly_meshes.npz')
    matrix_error=0
    for state in browser['states']:
        if state['mode']!='steps':continue
        expected={}
        for i,s in enumerate(steps[:state['step']]):
            if s['kind'] not in ['add','move']:continue
            off=point(s['path'],state['progress']) if i==state['step']-1 else np.array(s['path'][-1])
            for id in s['ids']:expected[id]=transform(id,off) if i==state['step']-1 else a.T(off)
        assert set(state['visible'])==set(expected)
        for id,M in expected.items():matrix_error=max(matrix_error,float(np.max(np.abs(M-np.array(state['transforms'][id]).reshape(4,4)))))
    assert matrix_error<1e-5,matrix_error
    class Links(HTMLParser):
        def __init__(self):super().__init__();self.links=[]
        def handle_starttag(self,tag,attrs):
            self.links += [v for k,v in attrs if k in ['href','src'] and v]
    broken=[];checked=0
    for f in OUT.rglob('*.html'):
        if 'source' in f.parts:continue
        q=Links();q.feed(f.read_text('utf8'))
        for url in q.links:
            u=urlsplit(url)
            if u.scheme or not u.path:continue
            target=f.parent/unquote(u.path)
            if target.name=='PoseDoll_O24C_T2_H_Test_Kit.zip':continue # generated after this audit
            checked+=1
            if not target.exists():broken.append([f.relative_to(OUT).as_posix(),url])
    assert not broken,broken
    geom=json.loads((OUT/'verification/geometry.json').read_text('utf8'));assert geom['passed']
    for r in geom['parts']:
        if r['printable']:assert r['stl_sha256']==sha(OUT/r['stl'])
    slicing=json.loads((OUT/'verification/slicing.json').read_text('utf8'));assert slicing['passed']
    for p in slicing['plates']:assert p['input_sha256']==sha(OUT/'printing'/(p['id']+'.3mf'))
    assert sum(s['kind']=='add' for s in steps)==17
    body=json.loads((OUT/'BOM.json').read_text('utf8'));assert sum(b['qty'] for b in body)==14
    geometry=trimesh.load(OUT/'O24C_T2_H.glb');assert len(geometry.geometry)==17
    assert float(max(geometry.extents))<.2
    assets={str(f.relative_to(OUT)):sha(f) for f in (OUT/'viewer').iterdir() if f.is_file()}
    browser.update(assets_sha256=assets,independent_matrix_max_error=matrix_error)
    put(OUT/'verification/browser.json',browser)
    refs=[H/'cad/revO24C_T1/kit.py',H/'bench/revO24C_T1/MANIFEST.sha256.json',H/'cad/revO12/build_taobao_bench.py',H/'tutorials/assembly-o22/ASSEMBLY.zh-CN.md']
    put(OUT/'verification/reference_sources.json',{str(p.relative_to(ROOT)):sha(p) for p in refs})
    for name in ['ordinary-nut','cap-assembly','opposed-springs','shoulder-screw','rom','exploded','mobile','entry']:
        shutil.copyfile(ROOT/f'output/playwright/o24ct2h-{name}.png',OUT/f'images/tutorial-{name}.png')
    put(OUT/'verification/delivery.json',dict(passed=True,assembly_parts=17,printed_assembly_parts=3,optional_coupon=1,metal_parts=14,
        actual_tutorial_path_samples=samples,path_findings=bad,animation_matrix_max_error=matrix_error,checked_html_links=checked,
        geometry_sha256=sha(OUT/'assembly_meshes.npz'),viewer_assets_sha256=assets,old_T1_files_modified=False,physical_tested=False))
    print(json.dumps(dict(passed=True,path_samples=samples,matrix_error=matrix_error,links=checked),ensure_ascii=False))

if __name__=='__main__':main()
