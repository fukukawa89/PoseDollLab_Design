"""A1 mini / PLA print projects and offline OrcaSlicer path validation.
Never sends files to a printer. Diagnostic G-code stays under output/.
"""
from kit import *
import xml.etree.ElementTree as ET
import zipfile,subprocess,time,re,concurrent.futures
Q='{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}';P='{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}'
ET.register_namespace('',Q[1:-1]);ET.register_namespace('p',P[1:-1])
ORCA=Path('D:/ProgramFiles/OrcaSlicer/orca-slicer.exe');WORK=ROOT/'output/o24ct1-slicing'
def xb(e):return ET.tostring(e,encoding='utf-8',xml_declaration=True)
def meta(e,k,v):ET.SubElement(e,'metadata',{'key':k,'value':str(v)})
def load(p):return json.loads(p.read_text('utf8'))

def project(plate):
    template=H/'bench/revO22/O22F7_PLA_AssemblyRevision/projects/D01_O22F7_PLA_final.3mf'
    with zipfile.ZipFile(template) as z:settings=json.loads(z.read('Metadata/project_settings.config'));ct=z.read('[Content_Types].xml')
    settings.update(print_settings_id=REVISION+' / A1 mini / PLA / 0.12 / solid',layer_height='0.12',initial_layer_print_height='0.2',wall_loops='5',sparse_infill_density='100%',sparse_infill_pattern='rectilinear',top_shell_layers='6',bottom_shell_layers='6',enable_support='1',support_type='normal(auto)',support_style='grid',support_on_build_plate_only='0',support_threshold_angle='45',support_top_z_distance='0.2',support_object_xy_distance='0.3',brim_type='outer_only',brim_width='3',brim_object_gap='0.1',skirt_loops='0',print_sequence='by layer',enable_prime_tower='0',elefant_foot_compensation='0.15',xy_hole_compensation='0',xy_contour_compensation='0')
    root=ET.Element(Q+'model',{'unit':'millimeter','requiredextensions':'p'});res=ET.SubElement(root,Q+'resources');build=ET.SubElement(root,Q+'build')
    ET.SubElement(root,Q+'metadata',{'name':'Application'}).text='BambuStudio-02.08.02.61';ET.SubElement(root,Q+'metadata',{'name':'BambuStudio:3mfVersion'}).text='1'
    cfg=ET.Element('config');pl=ET.SubElement(cfg,'plate')
    for key,val in [('plater_id',1),('plater_name',plate['id']),('locked','false')]:meta(pl,key,val)
    resources={};relns='http://schemas.openxmlformats.org/package/2006/relationships';modelrel='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel'
    subrel=ET.Element('Relationships',{'xmlns':relns})
    for i,item in enumerate(plate['items']):
        m=trimesh.load(OUT/item['stl'],process=True);assert m.is_watertight
        oid=2*i+2;sid=2*i+1;subpath=f'3D/Objects/object_{sid}.model';M=np.eye(4);M[:3,3]=item['offset_mm']
        ob=ET.SubElement(res,Q+'object',{'id':str(oid),'type':'model','name':item['id']});co=ET.SubElement(ob,Q+'components');ET.SubElement(co,Q+'component',{'objectid':str(sid),P+'path':'/'+subpath,'transform':'1 0 0 0 1 0 0 0 1 0 0 0'})
        ET.SubElement(build,Q+'item',{'objectid':str(oid),'transform':' '.join(f'{x:.12g}' for x in M[:3,:].T.flat),'printable':'1'})
        doc=ET.Element(Q+'model',{'unit':'millimeter'});rr=ET.SubElement(doc,Q+'resources');ob=ET.SubElement(rr,Q+'object',{'id':str(sid),'type':'model','name':item['id']});me=ET.SubElement(ob,Q+'mesh');verts=ET.SubElement(me,Q+'vertices');faces=ET.SubElement(me,Q+'triangles')
        for x,y,z in m.vertices:ET.SubElement(verts,Q+'vertex',dict(x=f'{x:.12g}',y=f'{y:.12g}',z=f'{z:.12g}'))
        for a,b,c in m.faces:ET.SubElement(faces,Q+'triangle',dict(v1=str(a),v2=str(b),v3=str(c)))
        resources[subpath]=xb(doc);ET.SubElement(subrel,'Relationship',{'Target':'/'+subpath,'Id':f'rel-{sid}','Type':modelrel})
        ob=ET.SubElement(cfg,'object',{'id':str(oid)});meta(ob,'name',item['id']);meta(ob,'extruder',1)
        pp=ET.SubElement(ob,'part',{'id':str(sid),'subtype':'normal_part'});meta(pp,'name',item['id']);meta(pp,'extruder',1);ET.SubElement(pp,'mesh_stat',{'face_count':str(len(m.faces)),'edges_fixed':'0','degenerate_facets':'0','facets_removed':'0','facets_reversed':'0','backwards_edges':'0'})
        inst=ET.SubElement(pl,'model_instance')
        for key,val in [('object_id',oid),('instance_id',0),('identify_id',i+1)]:meta(inst,key,val)
        item['object_name']=item['id'];item['bounds_mm']=np.r_[m.bounds[0]+M[:3,3],m.bounds[1]+M[:3,3]].tolist()
    ET.SubElement(cfg,'assemble');rel=ET.Element('Relationships',{'xmlns':relns});ET.SubElement(rel,'Relationship',{'Target':'/3D/3dmodel.model','Id':'rel-1','Type':modelrel})
    path=OUT/'printing'/(plate['id']+'.3mf');path.parent.mkdir(exist_ok=True)
    resources.update({'[Content_Types].xml':ct,'_rels/.rels':xb(rel),'3D/_rels/3dmodel.model.rels':xb(subrel),'3D/3dmodel.model':xb(root),'Metadata/model_settings.config':xb(cfg),'Metadata/project_settings.config':json.dumps(settings).encode()})
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for name,blob in resources.items():z.writestr(name,blob)
    plate['file']=path.relative_to(OUT).as_posix();plate['sha256']=sha(path);plate['count']=len(plate['items'])
    return path

def arrange():
    rows=load(OUT/'assembly.json')['parts'];options=load(OUT/'fit_options.json')['parts'];plates=[]
    groups=[('P0_fit',[r for r in rows if r['id'] in ['C01','W01','W02','W03','W04','W05']]),
        ('P1_hinge',[r for r in rows if r['station']=='H' and r['printable']]),
        ('P2_roll',[r for r in rows if r['station']=='R' and r['printable']]),
        ('P3_wrist',[r for r in rows if r['id'] in ['W06','W07','W08','W09']]),
        ('OPTION_bearing',[r for r in options if 'bearing' in r['id']]),('OPTION_liner',[r for r in options if 'inner' in r['id']]),
        ('REPRINT_S2',[r for r in rows if r['id'] in ['H04','H05','R04','R05']]),
        ('REPRINT_S3',[r for r in rows if r['id'] in ['W06','W07']])]
    for group,items in groups:
        plate=dict(id=group+'_1',items=[],optional=group.startswith('OPTION'),replacement=group.startswith('REPRINT'));x=8;y=8;rowh=0;number=1
        for item in sorted(items,key=lambda r: -(r.get('print_bounds_mm',r.get('bounds_mm'))[1][1])):
            m=trimesh.load(OUT/item['stl'],process=True);w,h,d=m.extents
            if x+w>172:x=8;y+=rowh+9;rowh=0
            if y+h>172:
                project(plate);plates.append(plate);number+=1;plate=dict(id=group+'_'+str(number),items=[],optional=group.startswith('OPTION'),replacement=group.startswith('REPRINT'));x=8;y=8;rowh=0
            assert w<164 and h<164
            plate['items'].append(dict(id=item['id'],stl=item['stl'],offset_mm=[x,y,0],stl_sha256=sha(OUT/item['stl'])))
            x+=w+9;rowh=max(rowh,h)
        project(plate);plates.append(plate)
    put(OUT/'printing/plates.json',dict(plates=plates,profile='A1 mini, 0.4mm nozzle, Generic PLA, 0.12mm layers, 5 walls, 100% infill, auto supports, 3mm brim. Start with P0. Optional plates are substitutes, not extra assembly parts.'))
    return plates

def run(plate):
    sys.path.insert(0,str(ROOT/'scripts'));from verify_revo22_a1mini import inspect_paths_and_positions
    work=WORK/plate['id'];work.mkdir(parents=True,exist_ok=True);dest=work/'sliced.3mf'
    cmd=[str(ORCA),'--allow-newer-file','--arrange','0','--slice','0','--debug','2','--export-3mf',str(dest),str(OUT/plate['file'])];start=time.time()
    with (work/'console.log').open('wb') as log:r=subprocess.run(cmd,cwd=work,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW,timeout=600)
    result=dict(id=plate['id'],returncode=r.returncode,input_sha256=sha(OUT/plate['file']),elapsed_s=time.time()-start,passed=False,objects=plate['count'])
    if r.returncode==0 and dest.exists():
        with zipfile.ZipFile(dest) as z:
            cfg=ET.fromstring(z.read('Metadata/model_settings.config'));stats=[dict(e.attrib) for e in cfg.findall('.//mesh_stat')]
            repairs=sum(int(s.get(key,0)) for s in stats for key in ('edges_fixed','degenerate_facets','facets_removed','facets_reversed','backwards_edges'))
            names=[e.attrib['value'] for o in cfg.findall('object') for e in o.findall('metadata') if e.attrib['key']=='name']
            result.update(inspect_paths_and_positions(z,plate,cfg));result.update(mesh_repairs=repairs,names=names,passed=repairs==0 and set(names)=={i['id'] for i in plate['items']})
            settings=json.loads(z.read('Metadata/project_settings.config'));result['settings']={key:settings.get(key) for key in ['printer_model','nozzle_diameter','filament_type','layer_height','wall_loops','sparse_infill_density','enable_support','print_sequence']}
            gcode=z.read('Metadata/plate_1.gcode').decode('utf8','replace');result['layers']=len(re.findall(r'^; Z_HEIGHT:',gcode,re.M));result['gcode_sha256']=hashlib.sha256(gcode.encode()).hexdigest()
            if 'Metadata/plate_1.png' in z.namelist():(OUT/'printing'/(plate['id']+'.png')).write_bytes(z.read('Metadata/plate_1.png'))
        if (work/'result.json').exists():
            d=load(work/'result.json');result['slicer_result']=d
    put(work/'audit.json',result);print('SLICE',plate['id'],result['passed'],round(time.time()-start,1),flush=True);return result

if __name__=='__main__':
    plates=arrange()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,plates))
    put(OUT/'verification/slicing.json',dict(passed=all(r['passed'] for r in results),plates=results,gcode_delivered=False,scope='Offline toolpaths and import, full-layer extrusion bounds, unchanged placements, all object names, zero mesh repairs. Physical print quality is not measured.'))
