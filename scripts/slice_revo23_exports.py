"""Slice the repaired STL round trips on the existing A1 mini PLA profile.

Offline verification only: never contacts a printer. Projects retain each exact
STL mesh, its rigid placement, profile, slicer logs and generated toolpaths.
"""
from revo23_export import *
from package_revo23 import export_selection
from present_revo23 import load_current
import xml.etree.ElementTree as ET
import subprocess,time,concurrent.futures,re

ROOT=EXPORT_ROOT/'slicing'
ORCA=Path('D:/ProgramFiles/OrcaSlicer/orca-slicer.exe')
Q='{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}'
P='{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}'
ET.register_namespace('',Q[1:-1]);ET.register_namespace('p',P[1:-1])

def xb(r):return ET.tostring(r,encoding='utf-8',xml_declaration=True)
def meta(parent,key,value):ET.SubElement(parent,'metadata',{'key':key,'value':str(value)})

def build(row):
    rid=row['id'];work=ROOT/rid;work.mkdir(parents=True,exist_ok=True)
    path=B/row['staged_stl'];assert sha(path)==row['stl_sha256']
    m=trimesh.load(path,process=True);assert m.is_watertight
    g=next(r for r in read(B/'verification/geometry.json')['geometry']['rows'] if r['key']==row['key'])
    M=np.array(g['print_matrix'])
    overrides=ROOT/'orientation_overrides.json'
    if overrides.exists():
        alternative=next((r for r in read(overrides) if r['id']==rid),None)
        if alternative:M=np.array(alternative['matrix'])
    placed=m.vertices@M[:3,:3].T+M[:3,3]
    M[:2,3]+=90-(placed.min(0)[:2]+placed.max(0)[:2])/2
    placed=m.vertices@M[:3,:3].T+M[:3,3]
    template=H/'bench/revO22/O22F7_PLA_AssemblyRevision/projects/D01_O22F7_PLA_final.3mf'
    with zipfile.ZipFile(template) as z:settings=json.loads(z.read('Metadata/project_settings.config'));ct=z.read('[Content_Types].xml')
    settings.update(print_settings_id='O23G STL validation / A1 mini PLA 0.4',
        layer_height='0.16',initial_layer_print_height='0.2',wall_loops='3',sparse_infill_density='20%',
        enable_support='1',support_type='normal(auto)',support_style='grid',support_on_build_plate_only='0',
        support_threshold_angle='45',support_top_z_distance='0.2',support_object_xy_distance='0.35',
        brim_type='outer_only',brim_width='3',skirt_loops='0',print_sequence='by layer',enable_prime_tower='0')
    root=ET.Element(Q+'model',{'unit':'millimeter','requiredextensions':'p'})
    ET.SubElement(root,Q+'metadata',{'name':'Application'}).text='BambuStudio-02.08.02.61'
    ET.SubElement(root,Q+'metadata',{'name':'BambuStudio:3mfVersion'}).text='1'
    ET.SubElement(root,Q+'metadata',{'name':'Title'}).text=rid+' repaired STL validation'
    res=ET.SubElement(root,Q+'resources');obj=ET.SubElement(res,Q+'object',{'id':'2','type':'model','name':rid})
    comps=ET.SubElement(obj,Q+'components');ET.SubElement(comps,Q+'component',{'objectid':'1',P+'path':'/3D/Objects/object_1.model','transform':'1 0 0 0 1 0 0 0 1 0 0 0'})
    build=ET.SubElement(root,Q+'build');ET.SubElement(build,Q+'item',{'objectid':'2','transform':' '.join(f'{x:.17g}' for x in M[:3,:].T.flat),'printable':'1'})
    sub=ET.Element(Q+'model',{'unit':'millimeter'});rr=ET.SubElement(sub,Q+'resources');ob=ET.SubElement(rr,Q+'object',{'id':'1','type':'model','name':rid})
    mesh=ET.SubElement(ob,Q+'mesh');verts=ET.SubElement(mesh,Q+'vertices');tris=ET.SubElement(mesh,Q+'triangles')
    for x,y,z in m.vertices:ET.SubElement(verts,Q+'vertex',dict(x=f'{x:.17g}',y=f'{y:.17g}',z=f'{z:.17g}'))
    for a,b,c in m.faces:ET.SubElement(tris,Q+'triangle',dict(v1=str(a),v2=str(b),v3=str(c)))
    cfg=ET.Element('config');o=ET.SubElement(cfg,'object',{'id':'2'});meta(o,'name',rid);meta(o,'extruder',1)
    part=ET.SubElement(o,'part',{'id':'1','subtype':'normal_part'});meta(part,'name',rid);meta(part,'extruder',1)
    ET.SubElement(part,'mesh_stat',{'face_count':str(len(m.faces)),'edges_fixed':'0','degenerate_facets':'0','facets_removed':'0','facets_reversed':'0','backwards_edges':'0'})
    plate=ET.SubElement(cfg,'plate')
    for k,v in [('plater_id',1),('plater_name',rid),('locked','false')]:meta(plate,k,v)
    inst=ET.SubElement(plate,'model_instance')
    for k,v in [('object_id',2),('instance_id',0),('identify_id',1)]:meta(inst,k,v)
    ET.SubElement(cfg,'assemble')
    relns='http://schemas.openxmlformats.org/package/2006/relationships';modelrel='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel'
    rel=ET.Element('Relationships',{'xmlns':relns});ET.SubElement(rel,'Relationship',{'Target':'/3D/3dmodel.model','Id':'rel-1','Type':modelrel})
    subrel=ET.Element('Relationships',{'xmlns':relns});ET.SubElement(subrel,'Relationship',{'Target':'/3D/Objects/object_1.model','Id':'rel-1','Type':modelrel})
    source=work/'input.3mf'
    with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED) as z:
        for name,data in {'[Content_Types].xml':ct,'_rels/.rels':xb(rel),'3D/_rels/3dmodel.model.rels':xb(subrel),'3D/3dmodel.model':xb(root),'3D/Objects/object_1.model':xb(sub),'Metadata/model_settings.config':xb(cfg),'Metadata/project_settings.config':json.dumps(settings).encode()}.items():z.writestr(name,data)
    put(work/'input.json',dict(id=rid,key=row['key'],stl_sha256=sha(path),source_project_sha256=sha(source),
        matrix=M,bounds_mm=[placed.min(0),placed.max(0)],profile_template=str(template),profile_template_sha256=sha(template)))
    return work,source

def run(row):
    work,source=build(row);dest=work/(row['id']+'_PLA_validation.3mf')
    command=[str(ORCA),'--allow-newer-file','--arrange','0','--slice','0','--debug','3','--export-3mf',str(dest),str(source)]
    start=time.time()
    with (work/'console.log').open('wb') as log:
        proc=subprocess.Popen(command,cwd=work,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
        try:code=proc.wait(timeout=900)
        except subprocess.TimeoutExpired:proc.terminate();code=proc.wait(timeout=15)
    r=dict(id=row['id'],key=row['key'],stl_sha256=row['stl_sha256'],command=command,returncode=code,elapsed_s=time.time()-start,passed=False)
    if dest.exists():
        with zipfile.ZipFile(dest) as z:
            codes=[n for n in z.namelist() if n.endswith('.gcode')];r['gcode_members']=codes
            if codes:
                gcode=z.read(codes[0]).decode('utf8','replace')
                heights=[float(x) for x in re.findall(r'^; Z_HEIGHT:\s*([0-9.]+)',gcode,re.M)]
                if not heights:heights=[float(x) for x in re.findall(r'^;Z:([0-9.]+)',gcode,re.M)]
                extrusion=sum(bool(re.match(r'G[123] .*\b[XY]-?\d',line) and re.search(r'\bE(?:\d*\.\d+|\d+)',line)) for line in gcode.splitlines())
                config=ET.fromstring(z.read('Metadata/model_settings.config'))
                meshstats=[dict(t.attrib) for t in config.findall('.//mesh_stat')]
                repairs=sum(int(s.get(k,'0')) for s in meshstats for k in ('edges_fixed','degenerate_facets','facets_removed','facets_reversed','backwards_edges'))
                settings=json.loads(z.read('Metadata/project_settings.config'))
                r.update(gcode_bytes=len(gcode),gcode_sha256=hashlib.sha256(gcode.encode()).hexdigest(),layer_count=len(heights),
                    min_layer_z=min(heights) if heights else None,max_layer_z=max(heights) if heights else None,
                    xy_extrusion_moves=extrusion,mesh_stats=meshstats,mesh_repair_counter_sum=repairs,
                    settings={k:settings.get(k) for k in ('printer_model','filament_type','nozzle_diameter','layer_height','initial_layer_print_height','wall_loops','sparse_infill_density','enable_support')},
                    slicer_header=gcode[:300],project_sha256=sha(dest),project=dest.relative_to(B).as_posix(),
                    passed=code==0 and len(heights)>1 and extrusion>10 and repairs==0)
    put(work/'result.json',r);print('SLICE',row['id'],r['passed'],'layers',r.get('layer_count'),'repairs',r.get('mesh_repair_counter_sum'),'sec',round(r['elapsed_s']),flush=True)
    return r

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--ids',nargs='*');ap.add_argument('--workers',type=int,default=2);a=ap.parse_args()
    rows=read(EXPORT_ROOT/'repair.json')['rows'];rows=[r for r in rows if not a.ids or r['id'] in a.ids]
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:results=list(pool.map(run,rows))
    if a.ids and (ROOT/'results.json').exists():
        old=read(ROOT/'results.json')['rows'];changed={r['id']:r for r in results}
        results=[changed.get(r['id'],r) for r in old]
    put(ROOT/'results.json',dict(geometry_sha256=sha(B/'assembly.npz'),rows=results,passed=all(r['passed'] for r in results)))
