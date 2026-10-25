"""Package the study, while preserving the explicit non-manufacturing status."""
from spherical_wrist import *
import zipfile,shutil,importlib.metadata,re
def main():
    geometry=sha(OUT/'assembly_meshes.npz');checks={}
    for name in ['mesh_integrity','motion_grid','kinematics','antiroll_negative_control','capture_feasibility','magnetic_feasibility','blender_saved_file','browser_review','browser_fk_agreement']:
        d=load(OUT/'verification'/f'{name}.json');assert d['status']=='PASS',(name,d['status'])
        if 'geometry_sha256' in d:assert d['geometry_sha256']==geometry,'Stale geometry: '+name
        checks[name]='PASS'
    web=load(OUT/'verification/browser_fk_agreement.json')
    assert web['browser_report_sha256']==sha(OUT/'verification/browser_review.json')
    for name,digest in web['source_sha256'].items():
        assert sha(HERE/name)==digest,name
        if name!='browser_review.js':assert sha(OUT/'preview'/name)==digest,'Stale preview '+name
    data=(OUT/'preview/data.js').read_text('utf8');assert geometry in data
    unchanged={name:sha(OLD/name)==digest for name,digest in load(OUT/'reference/O24A_frozen_hashes.json').items()}
    assert all(unchanged.values()),'A changed'
    oldz=np.load(OLD/'assembly_meshes.npz');newz=np.load(OUT/'assembly_meshes.npz')
    # Re-exporting via Manifold may reorder vertices; sorted coordinates verify the point sets.
    def sorted_points(v):return v[np.lexsort((v[:,2],v[:,1],v[:,0]))]
    delta=max(float(np.max(abs(sorted_points(oldz[str(i)+'v'])-sorted_points(newz[str(i)+'v'])))) for i in range(94))
    assert delta<1e-8
    put(OUT/'verification/retained_baseline.json',dict(status='PASS',frozen_files=unchanged,proximal_parts=94,max_vertex_set_error_mm=delta))
    checks['retained_baseline']='PASS'
    source=[f for f in HERE.iterdir() if f.is_file()]
    (OUT/'source').mkdir(exist_ok=True)
    for f in source:shutil.copy2(f,OUT/'source'/f.name)
    # Validate relative Markdown links, ignoring the external sources and anchor-only references.
    checked=0
    for f in OUT.glob('*.md'):
        for target in re.findall(r'\]\(([^\s)]+)\)',f.read_text('utf8')):
            if '://' in target or target.startswith('#'):continue
            assert (f.parent/target.split('#')[0]).exists(),f'{f.name}: broken {target}';checked+=1
    for path in (H.parents[1]/'output/playwright').glob('o24b-*.png'):
        if path.name!='o24b-wrist-initial.png':shutil.copy2(path,OUT/'images'/path.name)
    put(OUT/'STATUS.json',dict(revision='O24B',date_local='2026-10-22',stage=CONFIG['stage'],manufacturing_release=False,
        decision='Keep O24A; B is a spherical-wrist feasibility candidate pending physical sensing, holding and tolerance validation.',
        geometry_sha256=geometry,reference_height_mm=560,full_doll_height_measured=False,strict_full_doll_limit_mm=600,
        future_full_doll_envelope_budget_mm=580,parts=113,new_parts_including_palm=19,proximal_A_parts_retained=94,
        mechanical_checks=checks,markdown_links_checked=checked,magnetic_interference_status='ANALYTIC_BUDGET_ONLY',
        physical_testing='NOT RUN',PCB_routing='NOT DONE',firmware_UE_integration='NOT DONE',
        unresolved=['Whole-arm magnetic interference and calibration','Guide backlash and redundant-guide binding','Socket preload, friction creep and wear','Magnet/pin/cap/hand/forearm interface retention','PCB and flexible harness','Unchanged O24A shoulder singularity','Full doll exterior under 600 mm not yet modeled'],
        runtime_versions={name:importlib.metadata.version(name) for name in ['numpy','scipy','manifold3d','trimesh']}))
    exclude={'MANIFEST.sha256.json','PoseDoll_O24B_Spherical_Wrist_Study.zip','browser_cli_result.txt'}
    files=[f for f in OUT.rglob('*') if f.is_file() and f.name not in exclude and f.suffix not in ['.log','.pid','.blend1']]
    manifest={f.relative_to(OUT).as_posix():sha(f) for f in files}
    put(OUT/'MANIFEST.sha256.json',manifest)
    archive=OUT/'PoseDoll_O24B_Spherical_Wrist_Study.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for f in files:z.write(f,'O24B/'+f.relative_to(OUT).as_posix())
        z.write(OUT/'MANIFEST.sha256.json','O24B/MANIFEST.sha256.json')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name,digest in manifest.items():assert hashlib.sha256(z.read('O24B/'+name)).hexdigest()==digest,name
    print(json.dumps(dict(status='PASS',files=len(manifest),bytes=archive.stat().st_size,markdown_links_checked=checked,unchanged_A=unchanged),ensure_ascii=False))
if __name__=='__main__':main()
