"""Publish verified STL geometry as indexed 3MF, with explicit export provenance."""
from package_revo23 import *
from revo23_export import prepare_export,mesh_stats,EXPORT_ROOT,EXPORT_VERSION
import xml.etree.ElementTree as ET

def write_3mf(path,v,f,title):
    from xml.sax.saxutils import escape
    content_types='<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>'
    relationships='<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
        z.writestr('[Content_Types].xml',content_types);z.writestr('_rels/.rels',relationships)
        with z.open('3D/3dmodel.model','w')as w:
            w.write(('<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><metadata name="Title">'+escape(title)+'</metadata><metadata name="Description">Verified STL-derived indexed geometry. See export_formats.json and slice_validation for actual offline slicing. Physical manufacture remains unverified. This bare geometry file has no supports or slicing profile.</metadata><resources><object id="1" type="model"><mesh><vertices>').encode())
            for x,y,z0 in v:w.write(f'<vertex x="{x:.17g}" y="{y:.17g}" z="{z0:.17g}"/>'.encode())
            w.write(b'</vertices><triangles>')
            for a,b,c in f:w.write(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>'.encode())
            w.write(b'</triangles></mesh></object></resources><build><item objectid="1"/></build></model>')
    # Check every serialized vertex and index without loading the whole XML tree.
    vi=fi=0;max_error=0.
    with zipfile.ZipFile(path)as z:
        with z.open('3D/3dmodel.model')as stream:
            for _,element in ET.iterparse(stream,events=('end',)):
                tag=element.tag.rsplit('}',1)[-1]
                if tag=='vertex':
                    actual=np.array([float(element.attrib[k])for k in ('x','y','z')]);max_error=max(max_error,float(np.max(abs(actual-v[vi]))));vi+=1
                elif tag=='triangle':
                    actual=np.array([int(element.attrib[k])for k in ('v1','v2','v3')]);assert np.array_equal(actual,f[fi]);fi+=1
                element.clear()
    assert vi==len(v) and fi==len(f) and max_error==0
    return dict(vertices=vi,triangles=fi,serialization_error_mm=max_error,indices_identical=True)

def main():
    parts=load_current();g=read(B/'verification/geometry.json');digest=sha(B/'assembly.npz')
    assert g['geometry_sha256']==digest
    native=read(EXPORT_ROOT/'slicing/native_audit.json')
    assert native['passed'] and len(native['rows'])==32 and native['geometry_sha256']==digest
    rows=[];(B/'review_3mf').mkdir(exist_ok=True)
    selected=export_selection(parts)
    for key,part,rid in selected:
        stem=key.split('/',1)[1].replace('.','_');path=B/'review_3mf'/f'{rid}_{stem}.3mf'
        r=next(r for r in g['geometry']['rows']if r['key']==key)
        sliced_input=read(EXPORT_ROOT/'slicing'/rid/'input.json');M=np.array(sliced_input['matrix'])
        stlpath=B/'review_stl'/f'{rid}_{stem}.stl';mesh=trimesh.load(stlpath,process=True)
        repair=read(EXPORT_ROOT/(key.replace('/','__')+'.json'));assert repair['source_geometry_sha256']==digest
        v,f=mesh.vertices,mesh.faces;placed=v@M[:3,:3].T+M[:3,3]
        check=write_3mf(path,placed,f,rid+' '+stem)
        check['reference']='Repaired STL vertices and indices after the recorded rigid print placement; original CAD tessellation is retained in assembly.npz.'
        assert sha(stlpath)==sliced_input['stl_sha256'],('Published STL differs from sliced STL',rid)
        quality=mesh_stats(mesh);assert quality['watertight'] and quality['winding_consistent'] and quality['degenerate_faces']==quality['duplicate_faces']==0
        row=dict(id=rid,key=key,review_3mf=path.relative_to(B).as_posix(),stl=stlpath.relative_to(B).as_posix(),
            indexed_source_watertight=r['watertight'],native_serialization=check,
            stl_welded_watertight=bool(mesh.is_watertight),stl_welded_winding_consistent=bool(mesh.is_winding_consistent),
            stl_sha256=sha(stlpath),review_3mf_sha256=sha(path),manufacturing_release=False,
            stl_quality=quality,repair_record=(EXPORT_ROOT/(key.replace('/','__')+'.json')).relative_to(B).as_posix(),
            export_version=EXPORT_VERSION,surface_displacement_bound_mm=repair['surface_displacement_bound_mm'],
            print_matrix=M.tolist(),slicing_verified=True,slice_project=f'slice_validation/projects/{rid}_PLA_validation.3mf')
        rows.append(row);print('EXPORT',rid,'STL watertight',row['stl_welded_watertight'],'3MF indices preserved',flush=True)
    put(B/'verification/export_formats.json',dict(geometry_sha256=digest,rows=rows,
        stl_failures=[r['id']for r in rows if not r['stl_welded_watertight']],
        export_version=EXPORT_VERSION,native_print_slicing_verified=True,manufacturing_release=False))
    (B/'review_3mf/先读我.txt').write_text(f'{TAG} 已修复导出几何，单位 mm。\n与本轮封闭 STL 使用相同修复网格，逐项检查坐标与三角面索引写入一致。\n此目录为纯几何文件；已验证的摆放、PLA 配置、自动支撑和实际切片见 ../slice_validation/projects。\n32 件均通过离线切片；实物打印、强度及装配仍需验证。\n',encoding='utf8')
    (B/'review_stl/先读我.txt').write_text(f'{TAG} 已修复 STL，单位 mm；保留零件局部坐标。\n包含本轮新制或修改的 32 件；其余沿用 O22F7 的关节打印件继续使用原文件。\n32 件均通过封闭性、单实体、面朝向、零退化面检查，并从这些 STL 回读生成实际切片。\n原装配模型和运动参数未修改；导出整理最大声明表面偏差小于 0.0011 mm。\n切片验证：OrcaSlicer 2.4.2 / A1 mini / PLA / 0.4 mm 喷嘴 / 0.16 mm 层高 / 3 壁 / 20% 填充 / 自动支撑。\n带摆放及切片的工程见 ../slice_validation/projects；这些是切片验证工程，尚未实物试打或确认支撑拆除顺序。\n详见 ../STL_EXPORT_REPAIR.zh-CN.md 和 ../verification/stl_export_repair.json。\n',encoding='utf8')
    update_metadata()

def update_metadata():
    report=read(B/'verification/export_formats.json');digest=sha(B/'assembly.npz')
    assert report['geometry_sha256']==digest
    delivery=read(B/'DELIVERY.json');assert delivery['source_geometry_sha256']==digest
    delivery.update(review_3mf_count=len(report['rows']),stl_topology_failed_ids=report['stl_failures'],
                    native_3mf_slicing_verified=report['native_print_slicing_verified'],export_report='verification/export_formats.json',
                    export_version=EXPORT_VERSION,stl_slicing_verified=report['native_print_slicing_verified'])
    put(B/'DELIVERY.json',delivery)
    for file in ('结构件清单.csv','附件清单.csv'):
        with (B/file).open(encoding='utf-8-sig',newline='')as stream:rows=list(csv.DictReader(stream))
        for row in rows:
            r=next(r for r in report['rows']if r['id']==row['ID'])
            row['3MF评审几何']=r['review_3mf'];row['STL焊接后封闭']=r['stl_welded_watertight']
            if '封闭网格'in row:row['源索引网格封闭']=row.pop('封闭网格')
        writecsv(B/file,list(rows[0]),rows)

if __name__=='__main__':main()
