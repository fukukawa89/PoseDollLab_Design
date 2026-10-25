"""Final artifact consistency; no new physical-performance claims."""
from kit import *
from html.parser import HTMLParser
from urllib.parse import urlparse,unquote
import shutil

def main():
    audit=json.loads((ROOT/'output/playwright/o24ct1-browser.json').read_text('utf-8-sig'))
    assert audit['geometrySha']==sha(OUT/'assembly_meshes.npz') and audit['revision']==REVISION
    assert not audit['errors'] and all(r['status']==200 for r in audit['checked'])
    assert audit['mobile']['scrollWidth']==audit['mobile']['width'] and audit['offline']['ready'] and audit['offline']['webglError']==0
    matrix_errors=[]
    for r in audit['rows']:
        assert r['ready'] and r['webglError']==0 and r['shown']>0
        if 'matrix' in r:
            expect=frames(r['station'],*r['angles'])['ball' if r['station']=='W' else 'rotor'];err=float(np.max(np.abs(expect-np.array(r['matrix']).reshape(4,4))))
            matrix_errors.append(err);assert err<1e-10
    put(OUT/'verification/browser.json',dict(passed=True,geometry_sha256=sha(OUT/'assembly_meshes.npz'),fk_matrix_max_error=max(matrix_errors),audit=audit))
    for name in ['o24ct1-overview.png','o24ct1-wrist-exploded.png','o24ct1-start.png','o24ct1-mobile.png']:shutil.copyfile(ROOT/'output/playwright'/name,OUT/'images'/name)
    class Links(HTMLParser):
        def __init__(self):super().__init__();self.urls=[]
        def handle_starttag(self,tag,attrs):
            for k,v in attrs:
                if k in ['href','src']:self.urls.append(v)
    missing=[];count=0
    for p in OUT.rglob('*.html'):
        if 'source' in p.relative_to(OUT).parts:continue  # source templates need generated data.js
        parser=Links();parser.feed(p.read_text('utf8'))
        for url in parser.urls:
            u=urlparse(url)
            if u.scheme or url.startswith('#'):continue
            count+=1
            if not (p.parent/unquote(u.path)).exists():missing.append([str(p.relative_to(OUT)),url])
    assert not missing,missing
    for p in (OUT/'test_records').glob('*.csv'):
        with p.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.reader(f))
        assert all(len(row)==len(rows[0]) for row in rows),(p,[len(row) for row in rows])
    k=build();bom=json.loads((OUT/'BOM.json').read_text('utf8'));assert sum(r['qty'] for r in bom)==sum(not p['printable'] for p in k.parts)
    refs=json.loads((OUT/'reference_baseline.json').read_text('utf8'))
    assert all(sha(ROOT/p)==v for p,v in refs.items())
    assert sha(H/'bench/revO24C/assembly_meshes.npz')=='d661e8f2f3f2e135207a528a1001faa74baad660b26b777c748dfee802e2d032'
    glb=trimesh.load(OUT/'O24C_T1_kit.glb');assert max(glb.extents)<1 and max(glb.extents)>.2
    put(OUT/'verification/delivery.json',dict(passed=True,local_html_references_checked=count,csv_column_counts_passed=True,bom_parts=sum(r['qty'] for r in bom),glb_units='metres',glb_bounds_m=glb.bounds,source_C_unchanged=True,browser_geometry_sha256=sha(OUT/'assembly_meshes.npz')))
    print('DELIVERY PASS','local links',count,'BOM',sum(r['qty'] for r in bom),'GLB extent m',glb.extents.tolist(),flush=True)

if __name__=='__main__':main()
