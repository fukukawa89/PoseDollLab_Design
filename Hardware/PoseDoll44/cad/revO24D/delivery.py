"""Audit saved deliverables and assemble a review-only archive; never a print release."""
from fullbody import *
import ast
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit
from datetime import datetime, timezone
from zipfile import ZipFile, ZIP_DEFLATED


class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]
    def handle_starttag(self, tag, attrs):
        for key, val in attrs:
            if key in ['src','href'] and val:self.links.append(val)


def audit():
    assembly=load(OUT/'assembly.json'); z=np.load(OUT/'assembly_meshes.npz'); digest=sha(OUT/'assembly_meshes.npz')
    scene=trimesh.load(OUT/'O24D_full_body.glb',force='scene',process=False)
    missing=[]; vertex_error=matrix_error=0.; topology=True
    for p in assembly['parts']:
        if p['name'] not in scene.graph.nodes_geometry:missing.append(p['name']);continue
        matrix, geometry=scene.graph[p['name']];mesh=scene.geometry[geometry]
        v=z[str(p['i'])+'v']; f=z[str(p['i'])+'f']; expected=FA[p['frame']].copy();expected[:3,3]/=1000
        if mesh.vertices.shape!=v.shape:missing.append(p['name']+': vertex count');continue
        vertex_error=max(vertex_error,float(np.max(abs(mesh.vertices*1000-v))))
        matrix_error=max(matrix_error,float(np.max(abs(matrix-expected))))
        topology=topology and bool(np.array_equal(mesh.faces,f))
    bounds_error=float(np.max(abs(scene.bounds*1000-np.array(load(OUT/'verification/envelope.json')['bounds_mm']))))
    glb_pass=not missing and topology and vertex_error<.0001 and bounds_error<.0001 and matrix_error<1e-10
    put(OUT/'verification/glb_saved_file.json',dict(status='PASS' if glb_pass else 'FAIL',geometry_sha256=digest,
        glb_sha256=sha(OUT/'O24D_full_body.glb'),units='m',nodes=len(scene.graph.nodes_geometry),missing=missing,
        face_indices_unchanged=topology,max_local_vertex_error_mm=vertex_error,max_transform_element_error=matrix_error,
        max_bounds_error_mm=bounds_error,scope='Reload actual GLB and compare every saved mesh, topology and neutral transform with NPZ; unit conversion m to mm explicitly checked.'))
    json_count=0
    for f in OUT.rglob('*.json'):
        if f.name not in ['delivery_manifest.json','package_receipt.json']:json.loads(f.read_text(encoding='utf-8-sig'));json_count+=1
    for f in HERE.glob('*.py'):ast.parse(f.read_text(encoding='utf8'),filename=str(f))
    broken=[]
    for f in [OUT/'REVIEW.html',OUT/'preview/index.html',OUT/'electronics/SYSTEM.html']:
        links=Links();links.feed(f.read_text(encoding='utf8'))
        for url in links.links:
            parsed=urlsplit(url)
            if parsed.scheme or not parsed.path:continue
            path=(f.parent/unquote(parsed.path)).resolve()
            if not path.exists() and path.name!='artifact_delivery.json':broken.append([f.name,url])
    groups=load(OUT/'verification/printed_body_connections.json')
    expected_stl={Path(r['stl']).name for r in groups['rows']}
    actual_stl={p.name for p in (OUT/'stl_review_bodies').glob('*.stl')}
    stale=[]
    for f in (OUT/'verification').glob('*.json'):
        r=load(f)
        if isinstance(r,dict) and r.get('geometry_sha256') and r['geometry_sha256']!=digest:stale.append(f.name)
    copied={f:(HERE/f).read_bytes()==(OUT/'preview'/f).read_bytes() for f in ['index.html','viewer.js','style.css']}
    good=glb_pass and not broken and not stale and expected_stl==actual_stl and all(copied.values())
    result=dict(status='PASS_DELIVERY' if good else 'FAIL',geometry_sha256=digest,json_files_parsed=json_count,
        python_sources_parsed=len(list(HERE.glob('*.py'))),broken_local_links=broken,stale_geometry_reports=stale,
        review_stl_manifest_matches=expected_stl==actual_stl,review_stl_count=len(actual_stl),preview_source_copies=copied,
        scope='Saved artifact integrity only. Does not change failed ROM checks, manufacturing status or physical qualification.')
    put(OUT/'verification/artifact_delivery.json',result)
    print('DELIVERY',result['status'],'GLB',glb_pass,'vertex error mm',vertex_error,flush=True)
    if not good:raise RuntimeError('Delivery audit failed')


def package():
    root='PoseDoll_O24D_Review'; archive=OUT/'O24D_Digital_Review.zip'
    excluded={'delivery_manifest.json','package_receipt.json','O24D_Digital_Review.zip'}
    files=[]
    for folder,prefix in [(HERE,'cad/revO24D'),(OUT,'bench/revO24D')]:
        for f in sorted(folder.rglob('*')):
            if not f.is_file() or f.name in excluded or '__pycache__' in f.parts or f.suffix in ['.blend1','.log','.pyc']:continue
            files.append((f,prefix+'/'+f.relative_to(folder).as_posix()))
    manifest=dict(created_utc=datetime.now(timezone.utc).isoformat(),purpose='DIGITAL_REVIEW_ONLY',manufacturing_release=False,
        geometry_sha256=sha(OUT/'assembly_meshes.npz'),files=[dict(path=rel,bytes=f.stat().st_size,sha256=sha(f)) for f,rel in files],
        source_dependencies='CAD source uses the original repository virtual environment, revO24/revE helpers and frozen UE inputs. Preview/Blender/GLB/report can be reviewed without regenerating CAD.')
    put(OUT/'delivery_manifest.json',manifest)
    with ZipFile(archive,'w',ZIP_DEFLATED,compresslevel=6) as pack:
        for f,rel in files:pack.write(f,root+'/'+rel)
        pack.write(OUT/'delivery_manifest.json',root+'/delivery_manifest.json')
        pack.writestr(root+'/START_HERE.html','<!doctype html><meta charset="utf-8"><title>O24D 数字审查包</title><h1>O24D 数字审查包</h1><p>先解压全部文件，再打开以下入口。此包不是制造或打印放行。</p><p><a href="bench/revO24D/REVIEW.html">设计与验证报告</a></p><p><a href="bench/revO24D/preview/index.html">本地交互三维预览</a></p><p>预览无需外网。如浏览器限制直接打开，在 bench/revO24D 目录运行 <code>python serve_review.py</code>，使用仅限本机的预览服务。</p><p>本版含简化掌体、缩小骨盆、四肢镜像、背部原生电路板和全身线束路径。<a href="bench/revO24D/electronics/SYSTEM.html">电子与走线报告</a>。默认中立为双肩外展 45° 的 A 字姿态。相邻活动件为验收对象，非相邻接触为姿态提示；旧版 15° 强制联动已取消。S1 通过仍为设计假设；H04 弱连接已排除。完整限制见报告。源码重建需原仓库依赖。</p>')
    with ZipFile(archive) as pack:bad=pack.testzip();count=len(pack.namelist())
    put(OUT/'package_receipt.json',dict(status='PASS' if bad is None else 'FAIL',archive=archive.name,sha256=sha(archive),bytes=archive.stat().st_size,entries=count,crc_error=bad,manufacturing_release=False))
    print('PACKAGE',count,'entries',round(archive.stat().st_size/1024**2,2),'MiB',flush=True)
    if bad:raise RuntimeError(bad)


if __name__=='__main__':
    import sys
    audit()
    if '--package' in sys.argv:package()
