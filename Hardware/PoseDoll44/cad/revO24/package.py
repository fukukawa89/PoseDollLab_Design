"""Collect review artifacts and check that every report refers to this geometry."""
from arm import *
import zipfile,shutil,importlib.metadata

def main():
    checks={}
    names=['kinematics','exported_axes','motion_dense','ue_transform_mapping','functional_reach','browser_review','browser_fk_agreement','blender_saved_file','tutorial_browser','tutorial_fk_agreement','tutorial_portability']
    for name in names:
        d=json.loads((OUT/'verification'/f'{name}.json').read_text('utf-8-sig'))
        assert d['status']=='PASS',(name,d['status']);checks[name]='PASS'
    geometry_sha=sha(OUT/'assembly_meshes.npz')
    for name in ['exported_axes','motion_dense']:
        d=json.loads((OUT/'verification'/f'{name}.json').read_text('utf8'))
        assert d['geometry_sha256']==geometry_sha,name+' stale geometry'
    tutorial=json.loads((OUT/'verification/tutorial_fk_agreement.json').read_text('utf8'))
    assert tutorial['geometry_sha256']==geometry_sha,'Tutorial geometry changed'
    assert tutorial['browser_report_sha256']==sha(OUT/'verification/tutorial_browser.json'),'Tutorial report changed'
    for name,digest in tutorial['source_sha256'].items():
        assert sha(HERE/name)==digest and sha(OUT/'preview'/name)==digest,'Stale tutorial '+name
    ref=json.loads((OUT/'reference/target_quinn.json').read_text('utf8'))
    for name,digest in ref['source_files'].items():assert sha(REPO/name)==digest,'UE target changed'
    integrity=json.loads((OUT/'verification/mesh_integrity.json').read_text('utf8'));assert integrity['all_watertight']
    assert all(v['components']==1 and v['positive_volume'] for v in integrity['parts'])
    # Replace the provisional named-case report with a subset of the final audited cases.
    dense=json.loads((OUT/'verification/motion_dense.json').read_text('utf8'))
    named={**dense,'cases':[r for r in dense['cases'] if r['pose'] in poses()]};named['samples']=len(named['cases'])
    named['scope']='Named-pose subset of the final dense audit; see motion_dense.json for complete scope.'
    put(OUT/'verification/motion_named.json',named)
    for name in ['o24-neutral.png','o24-front.png','o24-body-scale.png','o24-drink.png']:
        shutil.copy2(REPO/'output/playwright'/name,OUT/'images'/name)
    for path in (REPO/'output/playwright').glob('o24-tutorial-*.png'):
        if path.name!='o24-tutorial-first.png':shutil.copy2(path,OUT/'images'/path.name)
    put(OUT/'STATUS.json',dict(revision='O24A',date_local='2026-10-22',stage='DIGITAL_LAYOUT_REVIEW',manufacturing_release=False,
        reference_height_mm=560,future_full_doll_envelope_budget_mm=580,strict_limit_mm=600,physical_complete_doll_height='NOT BUILT',
        geometry_sha256=geometry_sha,checks=checks,motion_samples=dense['samples'],
        unresolved=['Shoulder gimbal singularity near 90 deg abduction','Magnet carriers and anti-rotation attachments','Axial preload closure and bypass load paths','Bearing fits, retention and printable assembly splits','Hard travel stops and flexible harness','Bilateral clavicle and full torso/head clearance','Physical holding, accuracy and wear','Live UE plugin integration'],
        runtime_versions={name:importlib.metadata.version(name) for name in ['numpy','scipy','manifold3d','trimesh']}))
    exclude={'run_named.log','reach_candidates.json','preview-server.log','preview-server.err.log','preview-server.pid','render.log','MANIFEST.sha256.json','PoseDoll_O24A_Arm_Review.zip'}
    files=[f for f in OUT.rglob('*') if f.is_file() and f.name not in exclude and f.suffix!='.blend1']
    source=[f for f in HERE.iterdir() if f.is_file()]
    manifest={str(f.relative_to(OUT)).replace('\\','/'):sha(f) for f in files}
    manifest.update({'source/'+f.name:sha(f) for f in source})
    put(OUT/'MANIFEST.sha256.json',manifest)
    archive=OUT/'PoseDoll_O24A_Arm_Review.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for f in files:z.write(f,'O24A/'+str(f.relative_to(OUT)))
        z.write(OUT/'MANIFEST.sha256.json','O24A/MANIFEST.sha256.json')
        for f in source:z.write(f,'O24A/source/'+f.name)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name,digest in manifest.items():assert hashlib.sha256(z.read('O24A/'+name)).hexdigest()==digest,name
    print(json.dumps(dict(status='PASS',archive=str(archive),bytes=archive.stat().st_size,checks=checks,samples=dense['samples']),ensure_ascii=False))
if __name__=='__main__':main()
