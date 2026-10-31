"""Package an audited digital candidate. Never marks hardware qualified."""
from compact_arm import *
import shutil,zipfile,re,importlib.metadata

def main():
    freeze_baselines();geometry=sha(OUT/'assembly_meshes.npz');checks={}
    for name in ['mesh_integrity','motion_dense','kinematics','exported_axes','ue_transform_mapping','functional_reach','selected_clearances','reliability_screen','antiroll_negative_control','capture_feasibility','magnetic_feasibility','blender_saved_file','browser_review','browser_fk_agreement']:
        r=load(OUT/'verification'/f'{name}.json');assert r['status']=='PASS',(name,r['status'])
        if 'geometry_sha256' in r:assert r['geometry_sha256']==geometry,'Stale '+name
        checks[name]='PASS'
    web=load(OUT/'verification/browser_fk_agreement.json');assert web['browser_report_sha256']==sha(OUT/'verification/browser_review.json')
    for n,digest in web['source_sha256'].items():
        assert sha(HERE/n)==digest,n
        if n!='browser_review.js':assert sha(OUT/'preview'/n)==digest,'Stale preview '+n
    assert geometry in (OUT/'preview/data.js').read_text('utf8')
    for relative,digest in load(OUT/'reference/target_quinn.json')['source_files'].items():assert sha(H.parents[1]/relative)==digest,'UE source changed'
    put(OUT/'verification/retained_baselines.json',dict(status='PASS',frozen_files=len(load(OUT/'reference/baselines_sha256.json')),A_and_B_unchanged=True))
    (OUT/'source').mkdir(exist_ok=True)
    for p in HERE.iterdir():
        if p.is_file():shutil.copy2(p,OUT/'source'/p.name)
    for p in (H.parents[1]/'output/playwright').glob('o24c-*.png'):shutil.copy2(p,OUT/'images'/p.name)
    links=0
    for file in OUT.glob('*.md'):
        for target in re.findall(r'\]\(([^\s)]+)\)',file.read_text('utf8')):
            if '://' in target or target.startswith('#'):continue
            assert (file.parent/target.split('#')[0]).exists(),f'Broken {file.name}: {target}';links+=1
    put(OUT/'STATUS.json',dict(revision='O24C',date_local='2026-10-22',stage=CONFIG['stage'],manufacturing_release=False,
        geometry_sha256=geometry,parts=len(load(OUT/'assembly.json')['parts']),reference_height_mm=560,future_full_doll_envelope_budget_mm=580,strict_height_limit_mm=600,full_doll_height_verified=False,
        checks=checks,retained_baselines='PASS',markdown_links_checked=links,
        qualification=dict(physical_reliability='NOT TESTED',strength_and_wear='NOT TESTED',PCB_routing='NOT DONE',UE_runtime='NOT TESTED'),
        unresolved=['Shoulder gimbal singularity at about 90 degree abduction','Friction preload bypass and shaft retention','Magnet/pin/cap/liner/hand interfaces','Manufacturing tolerances, redundant guide binding and wear','Custom magnetic PCB, harness, full-arm calibration','Full torso and second arm collision','Complete physical doll height under 600 mm'],
        runtime_versions={n:importlib.metadata.version(n) for n in ['numpy','scipy','trimesh','manifold3d']}))
    archive=OUT/'PoseDoll_O24C_Compact_Arm_Review.zip';exclude={archive.name,'MANIFEST.sha256.json','browser_cli_result.txt'}
    files=[f for f in OUT.rglob('*') if f.is_file() and f.name not in exclude and f.suffix not in ['.log','.pid','.blend1']]
    manifest={f.relative_to(OUT).as_posix():sha(f) for f in files};put(OUT/'MANIFEST.sha256.json',manifest)
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for f in files:z.write(f,'O24C/'+f.relative_to(OUT).as_posix())
        z.write(OUT/'MANIFEST.sha256.json','O24C/MANIFEST.sha256.json')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name,digest in manifest.items():assert hashlib.sha256(z.read('O24C/'+name)).hexdigest()==digest,name
    print(json.dumps(dict(status='PASS',files=len(files),zip_bytes=archive.stat().st_size,source_and_A_B_preserved=True,geometry_sha256=geometry)))

if __name__=='__main__':main()
