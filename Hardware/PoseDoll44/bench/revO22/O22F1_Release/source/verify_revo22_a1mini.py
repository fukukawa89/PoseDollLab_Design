"""Validate O22 A1 mini layouts with the locally installed Bambu Studio CLI.

No printer connection is used. Test G-code remains in .local and is not shipped.
The reference PLA / 0.4 mm settings check layout and slicing, not O11 material fit.
"""
from pathlib import Path
import argparse, hashlib, json, math, re, subprocess, zipfile
import xml.etree.ElementTree as ET
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'Hardware/PoseDoll44/bench/revO22/a1mini'
WORK=ROOT/'.local/a1mini-slicer'


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def profiles(install):
    folder=install/'resources/profiles/BBL';index={}
    for path in folder.rglob('*.json'):
        try:
            d=json.loads(path.read_text(encoding='utf-8-sig'))
            index[d.get('name',path.stem)]=(d,path)
        except (ValueError,UnicodeError): pass
    used={}
    def resolve(name):
        d,p=index[name];used[str(p.relative_to(folder))]=sha(p)
        base=resolve(d['inherits']) if d.get('inherits') else {}
        for inc in d.get('include',[]):base.update(resolve(inc))
        base.update(d);base.pop('inherits',None);base.pop('include',None)
        return base
    files=[]
    for typ,name in [('machine','Bambu Lab A1 mini 0.4 nozzle'),('process','0.20mm Standard @BBL A1M'),('filament','Generic PLA @BBL A1M')]:
        d=resolve(name)
        if typ=='process':
            d.update({'name':'O22 A1 mini layout check 0.20mm','print_settings_id':'O22 A1 mini layout check 0.20mm','enable_support':'1','support_type':'normal(auto)','support_style':'grid','support_on_build_plate_only':'0','support_threshold_angle':'30','support_object_xy_distance':'0.35','support_expansion':'0','brim_type':'outer_only','brim_width':'2','brim_object_gap':'0.1','skirt_loops':'0','print_sequence':'by layer','enable_prime_tower':'0','wall_loops':'3','sparse_infill_density':'20%'})
        d['version']='02.08.02.61';p=WORK/(typ+'.json');p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');files.append(p)
    return files,used


def inspect_paths_and_positions(z, plate, meta):
    ns='{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}'
    pns='{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}'
    docs={}
    def doc(path):
        if path not in docs: docs[path]=ET.fromstring(z.read(path))
        return docs[path]
    def transform(text):
        a=np.eye(4)
        if text:
            a[:3,:]=np.array([float(x) for x in text.split()]).reshape(4,3).T
        return a
    def vertices(path, oid, matrix):
        node=next(o for o in doc(path).findall(ns+'resources/'+ns+'object') if o.attrib['id']==oid)
        mesh=node.find(ns+'mesh')
        if mesh is not None:
            v=np.array([[float(n.attrib[k]) for k in ('x','y','z')] for n in mesh.findall(ns+'vertices/'+ns+'vertex')])
            return v@matrix[:3,:3].T+matrix[:3,3]
        return np.concatenate([vertices(c.attrib.get(pns+'path',path).lstrip('/'),c.attrib['objectid'],matrix@transform(c.attrib.get('transform'))) for c in node.findall(ns+'components/'+ns+'component')])
    object_names={o.attrib['id']:next(n.attrib['value'] for n in o.findall('metadata') if n.attrib.get('key')=='name') for o in meta.findall('object')}
    expected={i['object_name']:np.array(i['bounds_mm']) for i in plate['items']}
    errors=[]
    for item in doc('3D/3dmodel.model').findall(ns+'build/'+ns+'item'):
        v=vertices('3D/3dmodel.model',item.attrib['objectid'],transform(item.attrib.get('transform')))
        error=float(np.max(np.abs(np.r_[v.min(axis=0),v.max(axis=0)]-expected[object_names[item.attrib['objectid']]])))
        errors.append(error)
    assert max(errors)<.0001,(plate['id'],'placement changed',max(errors))
    lower=np.array([math.inf]*3);upper=-lower.copy();xyz=np.zeros(3);relative_e=True;relative_xyz=False;last_e=0.;feature='Custom';extrusions=0;arcs=0
    number=re.compile(r'([XYZEFIJK])([-+]?(?:[0-9]*\.)?[0-9]+)')
    for line in z.read('Metadata/plate_1.gcode').decode().splitlines():
        if line.startswith('; FEATURE: '):feature=line.split(': ',1)[1];continue
        code=line.split(';',1)[0].strip()
        if not code:continue
        cmd=code.split(' ',1)[0]
        if cmd=='M83':relative_e=True
        elif cmd=='M82':relative_e=False
        elif cmd=='G90':relative_xyz=False
        elif cmd=='G91':relative_xyz=True
        fields={k:float(v) for k,v in number.findall(code)}
        if cmd=='G92':
            if 'E' in fields:last_e=fields['E']
            for j,axis in enumerate('XYZ'):
                if axis in fields:xyz[j]=fields[axis]
            continue
        if cmd not in ('G0','G1','G2','G3'):continue
        prev=xyz.copy()
        for j,axis in enumerate('XYZ'):
            if axis in fields:xyz[j]=fields[axis]+(xyz[j] if relative_xyz else 0.)
        e=fields.get('E',0. if relative_e else last_e);delta=e if relative_e else e-last_e
        if 'E' in fields:last_e=e
        if delta<=0 or feature in ('Custom','Flush'):continue
        if np.linalg.norm(xyz-prev)<1e-8 and cmd not in ('G2','G3'):continue
        pts=[prev.copy(),xyz.copy()]
        if cmd in ('G2','G3'):
            arcs+=1;center=prev[:2]+[fields.get('I',0.),fields.get('J',0.)];radius=float(np.linalg.norm(prev[:2]-center))
            start=math.atan2(prev[1]-center[1],prev[0]-center[0]);end=math.atan2(xyz[1]-center[1],xyz[0]-center[0]);direction=-1 if cmd=='G2' else 1
            sweep=(direction*(end-start))%(2*math.pi)
            if np.linalg.norm(xyz[:2]-prev[:2])<1e-7 and radius>0:sweep=2*math.pi
            for angle in (0.,math.pi/2,math.pi,3*math.pi/2):
                if (direction*(angle-start))%(2*math.pi)<=sweep+1e-7:pts.append(np.array([center[0]+radius*math.cos(angle),center[1]+radius*math.sin(angle),xyz[2]]))
        pts=np.array(pts);lower=np.minimum(lower,pts.min(axis=0));upper=np.maximum(upper,pts.max(axis=0));extrusions+=1
    assert extrusions>0 and np.all(lower>=-1e-4) and np.all(upper<=180.0001),(plate['id'],lower,upper)
    return {'slicer_placement_max_bbox_error_mm':max(errors),'all_layer_model_support_brim_extrusion_path_bounds_mm':np.r_[lower,upper].tolist(),'extrusion_segments_checked':extrusions,'arc_segments_checked':arcs,'path_scope':'Extruding model/support/brim paths across every layer; machine startup, shutdown, purge and nonextruding travel excluded'}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--studio',type=Path,default=Path('D:/ProgramFiles/Bambu Studio/bambu-studio.exe'));parser.add_argument('--plate',action='append');parser.add_argument('--inspect-only',action='store_true');args=parser.parse_args()
    WORK.mkdir(parents=True,exist_ok=True);ver=BASE/'verification';ver.mkdir(exist_ok=True)
    configs,used=profiles(args.studio.parent);machine,process,filament=configs
    manifest=json.loads((BASE/'manifest.json').read_text())
    report_path=ver/'bambu_studio.json'
    old=json.loads(report_path.read_text()) if report_path.exists() else {}
    reports={r['id']:r for r in old.get('plates',[])}
    for plate in manifest['plates']:
        if args.plate and plate['id'] not in args.plate:continue
        work=WORK/plate['id'];work.mkdir(exist_ok=True);output=work/'sliced.3mf'
        command=[str(args.studio),'--arrange','0','--load-settings',str(machine)+';'+str(process),'--load-filaments',str(filament),'--curr-bed-type','Textured PEI Plate','--slice','0','--debug','2','--export-3mf',str(output),str(BASE/plate['file'])]
        if args.inspect_only:
            run=subprocess.CompletedProcess(command,0,stdout=b'')
            assert output.exists(),output
            assert reports[plate['id']]['input_sha256']==sha(BASE/plate['file']),'Input changed since slicing'
            assert old['reference_settings_sha256']=={p.name:sha(p) for p in configs},'Settings changed since slicing'
            if reports[plate['id']].get('sliced_output_sha256'):
                assert reports[plate['id']]['sliced_output_sha256']==sha(output),'Cached slice changed'
        else:
            run=subprocess.run(command,cwd=work,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),timeout=180)
            (work/'console.log').write_bytes(run.stdout)
        result_path=work/'result.json'
        result=json.loads(result_path.read_text()) if result_path.exists() else {}
        (ver/(plate['id']+'_cli_result.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(plate['id'],'exit',run.returncode,result.get('error_string'),flush=True)
        if run.returncode or result.get('return_code')!=0:
            raise RuntimeError((plate['id'],run.returncode,result,run.stdout[-2000:]))
        with zipfile.ZipFile(output) as z:
            settings=json.loads(z.read('Metadata/project_settings.config'))
            meta=ET.fromstring(z.read('Metadata/model_settings.config'))
            loaded=meta.findall('object')
            expected={i['object_name'] for i in plate['items']}
            names={n.attrib['value'] for o in loaded for n in o.findall('metadata') if n.attrib.get('key')=='name'}
            assert names==expected,(plate['id'],expected-names,names-expected)
            assert settings['printer_model']=='Bambu Lab A1 mini' and settings['print_sequence']=='by layer'
            assert settings['printable_area']==['0x0','180x0','180x180','0x180']
            paths=json.loads(z.read('Metadata/plate_1.json'));bbox=paths['bbox_all']
            assert bbox[0]>=0 and bbox[1]>=0 and bbox[2]<=180 and bbox[3]<=180,(plate['id'],bbox)
            (BASE/'previews'/(plate['id']+'.png')).write_bytes(z.read('Metadata/plate_1.png'))
            fixes={k:0 for k in ('edges_fixed','degenerate_facets','facets_removed','facets_reversed','backwards_edges')}
            for stat in meta.findall('.//mesh_stat'):
                for k in fixes:fixes[k]+=int(stat.attrib.get(k,0))
            warning=[p.get('warning_message','') for p in result['sliced_plates'] if p.get('warning_message')]
            reports[plate['id']]={'id':plate['id'],'input_file':plate['file'],'input_sha256':sha(BASE/plate['file']),'sliced_output_sha256':sha(output),'cli_return_code':run.returncode,'sliced_plate_count':len(result['sliced_plates']),'expected_objects':plate['count'],'loaded_objects':len(loaded),'all_names_preserved':True,'first_layer_with_support_brim_bbox_mm':bbox,'mesh_repairs':fixes,'warnings':warning,'print_sequence':settings['print_sequence'],'printer_model':settings['printer_model'],'gcode_exported_only_to_local_workdir':True,'reference_estimated_seconds':result['sliced_plates'][0]['total_predication'],'reference_filament_g':sum(x['total_used_g'] for x in result['sliced_plates'][0]['filaments'])}
            reports[plate['id']].update(inspect_paths_and_positions(z,plate,meta))
            assert len(result['sliced_plates'])==1,plate['id']
            print('  objects',len(loaded),'bbox',[round(x,2) for x in bbox],'repairs',fixes,'warnings',warning,flush=True)
    complete=len(reports)==len(manifest['plates']) and all(reports[p['id']]['input_sha256']==sha(BASE/p['file']) for p in manifest['plates'])
    report={'status':'PASS' if complete else 'PARTIAL','scope':'Bambu Studio import, unchanged placement (arrange=0), object names/counts, 180x180 bed, by-layer slicing with automatic normal/grid supports and 2 mm outer brim. No physical printing. No original O11 process qualification.','studio_version':'02.08.02.61','settings':{'printer':'Bambu Lab A1 mini','nozzle_mm':0.4,'filament':'Generic PLA @BBL A1M','bed':'Textured PEI Plate','layer_height_mm':0.2,'wall_loops':3,'infill':'20%','brim_width_mm':2,'supports':'normal(auto), grid, 30 degree threshold','skirt_loops':0,'print_sequence':'by layer'},'source_profiles_sha256':used,'reference_settings_sha256':{p.name:sha(p) for p in configs},'plates':list(reports.values())}
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if complete:
        manifest['slicer_validation']='PASS: 11/11 files imported and sliced as single plates by Bambu Studio 02.08.02.61; includes optional test plate'
        (BASE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
