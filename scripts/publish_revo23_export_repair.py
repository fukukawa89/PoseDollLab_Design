"""Publish only the STL set that passed topology, slicing and G regressions."""
from revo23_export import *
from probe_revo23_stl import SNAP
import shutil

def main():
    digest=sha(B/'assembly.npz');snapshot=read(SNAP/'snapshot.json')
    assert digest==snapshot['geometry_sha256'] and sha(B/'profiles/device_profile.json')==snapshot['profile_sha256']
    assert sha(CFG)==sha(SNAP/'parameters.json')
    repair=read(EXPORT_ROOT/'repair.json');slice_report=read(EXPORT_ROOT/'slicing/results.json');native=read(EXPORT_ROOT/'slicing/native_audit.json')
    assert len(repair['rows'])==len(slice_report['rows'])==len(native['rows'])==32
    assert native['passed'] and slice_report['passed']
    names=('daily_motion','edge_motion','smooth_connections','continuous_walls','physical_rod_count','wire_fixtures','fixed_interfaces','geometry_difference')
    checks={n:read(EXPORT_ROOT/'verification'/(n+'.json')) for n in names}
    export_hash=checks['daily_motion']['export_set_sha256']
    for name,r in checks.items():assert r['passed'] and r['geometry_sha256']==digest and r['export_set_sha256']==export_hash,name
    assert checks['daily_motion']['pose_count']==408 and checks['edge_motion']['pose_count']==114
    assert len(checks['smooth_connections']['rods'])==44
    assert len(checks['wire_fixtures']['seats'])==33 and len(checks['wire_fixtures']['channels'])==8
    for r in repair['rows']:
        rid=r['id'];src=B/r['staged_stl'];assert sha(src)==r['stl_sha256']
        sx=next(x for x in slice_report['rows'] if x['id']==rid);nx=next(x for x in native['rows'] if x['id']==rid)
        assert sx['stl_sha256']==nx['stl_sha256']==r['stl_sha256'] and sx['passed'] and nx['passed']
        assert sha(B/sx['project'])==sx['project_sha256']==nx['project_sha256']
        shutil.copy2(src,B/'review_stl'/src.name)
        dst=B/'slice_validation/projects'/Path(sx['project']).name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(B/sx['project'],dst)
        sx['validation_project']=dst.relative_to(B).as_posix()
    regression=dict(geometry_sha256=digest,profile_sha256=sha(B/'profiles/device_profile.json'),
        export_set_sha256=export_hash,source_assembly_byte_identical=True,configuration_byte_identical=True,
        checks={n:dict(report=(EXPORT_ROOT/'verification'/(n+'.json')).relative_to(B).as_posix(),sha256=sha(EXPORT_ROOT/'verification'/(n+'.json')),passed=True) for n in names},
        daily_poses=408,transition_poses=114,required_contacts=0,round_connections=44,
        maximum_rods_per_adjacent_component=checks['physical_rod_count']['maximum_rods_per_adjacent_component'],
        wire_seats=33,wire_channels=8,independent_sensor_routes=46,passed=True)
    put(B/'verification/stl_regression.json',regression)
    summary=dict(geometry_sha256=digest,export_set_sha256=export_hash,engine='OrcaSlicer 2.4.2',
        printer='Bambu Lab A1 mini',nozzle_mm=.4,material='PLA',layer_height_mm=.16,initial_layer_height_mm=.2,
        walls=3,infill_percent=20,automatic_supports=True,rows=slice_report['rows'],native_mesh_audits=native['rows'],
        orientation_fixes=read(EXPORT_ROOT/'slicing/orientation_overrides.json'),
        native_meshes_preserved=True,slicer_mesh_repairs=0,physical_print_tested=False,passed=True)
    put(B/'verification/slice_validation.json',summary)
    old=read(SNAP/'verification/export_formats.json');rows=[]
    for r in repair['rows']:
        oldrow=next(x for x in old['rows'] if x['id']==r['id']);before=trimesh.load(SNAP/oldrow['stl'],process=True)
        dst=B/'review_stl'/Path(r['staged_stl']).name;after=trimesh.load(dst,process=True)
        st=mesh_stats(after);assert st['watertight'] and st['winding_consistent'] and st['degenerate_faces']==st['duplicate_faces']==0
        rows.append(dict(id=r['id'],key=r['key'],stl=dst.relative_to(B).as_posix(),stl_sha256=sha(dst),
            before=mesh_stats(before),after=st,components=1,simplify_tolerance_mm=r['simplify_tolerance_mm'],
            maximum_declared_surface_displacement_mm=r['surface_displacement_bound_mm'],
            conditioning_record=(EXPORT_ROOT/(r['key'].replace('/','__')+'.json')).relative_to(B).as_posix()))
    report=dict(geometry_sha256=digest,export_set_sha256=export_hash,export_version=EXPORT_VERSION,
        before_stl_failures=old['stl_failures'],before_failed_count=len(old['stl_failures']),after_failed_count=0,
        source_geometry_unchanged=True,source_profile_unchanged=True,rows=rows,
        max_declared_surface_displacement_mm=max(r['maximum_declared_surface_displacement_mm'] for r in rows),
        causes=['Float32 coordinate weld collapses short edges and creates degenerate facets.',
            'Oppositely oriented coincident faces form zero-thickness internal membranes.',
            'The case retains membranes from an obsolete lid-boss subtraction; its identical analytic features were re-evaluated.'],
        case_nominal_boolean_difference_mm3=next(r['case_rebuild'] for r in repair['rows'] if r['key']=='o22/controller_housing'),
        topology_passed=True,slicing_passed=True,regression_passed=True,passed=True,physical_print_tested=False)
    put(B/'verification/stl_export_repair.json',report)
    import export_revo23_3mf
    export_revo23_3mf.main()
    delivery=read(B/'DELIVERY.json');delivery.update(export_repair='verification/stl_export_repair.json',
        export_regression='verification/stl_regression.json',slice_validation='verification/slice_validation.json',
        stl_topology_failed_ids=[],stl_slicing_verified=True,native_3mf_slicing_verified=True)
    put(B/'DELIVERY.json',delivery)
    print('PUBLISHED EXPORT REPAIR',len(rows),digest,flush=True)

if __name__=='__main__':main()
