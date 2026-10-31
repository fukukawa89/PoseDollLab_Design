"""Final evidence and file-coherence audit, not physical qualification."""
from build import *
from collections import Counter
from html.parser import HTMLParser
from urllib.parse import unquote,urlsplit
import zipfile

def main():
    digest=sha(OUT/'assembly_meshes.npz');checks=[]
    def check(name,ok,detail=None):checks.append(dict(check=name,passed=bool(ok),detail=detail))
    reports=['mesh_integrity','envelope','motion_named_endpoints','capture_and_paths','retention_chain','sensor_assembly','kinematics','wrist_observability','production_parts','production_capture','production_retention','rom_examination_dense','joint_local_grids','motion_task_paths','harness','bone_link_alignment','standing_ground_loads','preload_retention_loads','elastic_preload','ue_mapping','protocol_guard']
    for name in reports:
        p=OUT/'verification'/f'{name}.json';r=load(p) if p.exists() else {}
        check(name,r.get('geometry_sha256')==digest and r.get('status','').startswith('PASS'),dict(status=r.get('status'),geometry_sha256=r.get('geometry_sha256')))
    r=load(OUT/'verification/production_sensor_assembly.json');check('production sensor entry',r['geometry_sha256']==digest and r['production_mesh_sha256']==sha(OUT/'production_meshes.npz') and r['status']=='PASS_GEOMETRY')
    r=load(OUT/'verification/viewer_browser.json');check('final browser evidence',r['geometry_sha256']==digest and r['production_mesh_sha256']==sha(OUT/'production_meshes.npz') and r['status']=='PASS_BROWSER_REVIEW' and r['ready'] and r['console_errors']==0 and r['max_matrix_error']<1e-8)
    check('D immutable',sha(BASE/'assembly_meshes.npz')=='fd64f061821a42f803e2131b0f0642147ab9cc8e65dc32cdb5e3476a0b7c9e8e')
    check('T6 immutable',sha(H/'bench/revO24C_T6/assembly_meshes.npz')=='645544a8af0ef769ffa8130e56f2587599ec042861d99358609bf31587e0a5e9')
    inv=load(OUT/'production_parts.json');struct=inv['structural_parts'];pr=[r for r in struct if r['printable']]
    check('47 structural bodies / 46 FDM',len(struct)==47 and len(pr)==46)
    check('production geometry identity',inv['geometry_sha256']==digest and load(OUT/'production_assembly.json')['geometry_sha256']==digest)
    for name in ['production_capture','production_retention']:check(name+' actual mesh identity',load(OUT/'verification'/f'{name}.json')['production_mesh_sha256']==sha(OUT/'production_meshes.npz'))
    check('print STL hashes',all(sha(OUT/r['stl'])==r['sha256'] and r['stl_roundtrip_watertight'] for r in pr))
    check('positive and single production solids',all(r['watertight'] and r['components']==1 and r['core_count_0_5']==1 for r in load(OUT/'verification/production_parts.json')['rows']))
    plates=load(OUT/'printing/plates.json')['plates'];placed=[]
    for p in plates:
        path=OUT/'printing'/f'{p["id"]}.3mf';r=load(OUT/'verification'/f'slice_{p["id"]}.json')
        with zipfile.ZipFile(path) as z:crc=z.testzip() is None
        check(p['id'],r.get('passed') and r['input_sha256']==sha(path) and crc,dict(extrusion_segments=r.get('extrusion_segments_checked'),mesh_repairs=r.get('mesh_repairs')))
        placed.extend(i['id'] for i in p['items'])
        check(p['id']+' STL identity',all(i['stl_sha256']==sha(OUT/i['stl']) for i in p['items']))
    check('exactly one copy of every print part',Counter(placed)==Counter(r['part_number'] for r in pr))
    t=load(OUT/'tutorial/steps.json');covered=set(t['covered_part_numbers']);required={r['part_number'] for r in struct}|{r['part_number'] for r in inv['hardware'] if r.get('procurement_item',True)}
    check('tutorial covers every independent physical part',not (required-covered),sorted(required-covered))
    check('tutorial version',t['geometry_sha256']==digest)
    check('all 38 PCB entries explicit',len(load(OUT/'profiles/sensor_entries.json')['rows'])==38 and all(r['status']=='DESIGNED_ENTRY' for r in load(OUT/'profiles/sensor_entries.json')['rows']))
    check('preserved 40 axes and 80 endpoints',len(PROFILE['axes'])==40 and load(OUT/'verification/kinematics.json')['endpoint_count']==80)
    check('under 600 mm',load(OUT/'verification/envelope.json')['height_mm']<600)
    check('no unearned qualification',load(OUT/'assembly.json')['manufacturing_release'] is False and load(OUT/'electronics/calibration_template.json')['measured_and_accepted'] is False and load(OUT/'verification/protocol_guard.json')['firmware_flashed'] is False)
    class Links(HTMLParser):
        def __init__(self):super().__init__();self.links=[]
        def handle_starttag(self,tag,attrs):
            for k,v in attrs:
                if k in ['href','src'] and v:self.links.append(v)
    missing=[]
    for p in [*OUT.glob('*.html'),OUT/'preview/index.html']:
        if not p.exists():missing.append(str(p));continue
        parser=Links();parser.feed(p.read_text('utf8'))
        for u in parser.links:
            a=urlsplit(u)
            if a.scheme or not a.path:continue
            if not (p.parent/unquote(a.path)).resolve().exists():missing.append(f'{p.name}: {u}')
    check('local HTML links and assets',not missing,missing)
    for name in ['O24E_production_assembly.blend','O24E_production_assembly.glb','preview/data.js','preview/assembly.js']:
        check(name,(OUT/name).is_file() and (OUT/name).stat().st_size>100)
    r=dict(status='PASS_DELIVERY_COHERENCE' if all(c['passed'] for c in checks) else 'FAIL',geometry_sha256=digest,checks=checks,physical_acceptance=False,scope='File identity, preserved baselines, report freshness, exact plate/part coverage and tutorial links. No physical test claimed.')
    put(OUT/'verification/delivery_audit.json',r);print(r['status'],[c for c in checks if not c['passed']],flush=True)
    if r['status']=='FAIL':raise SystemExit(1)
if __name__=='__main__':main()
