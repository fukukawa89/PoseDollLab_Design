"""Bind the delivered review geometry, checks, exports, and renders together."""
from build_revo23_continuous import *

digest=sha(B/'assembly.npz');p=read(B/'profiles/device_profile.json')
files=['geometry.json','daily_motion.json','edge_paths.json','backpack_tool_access.json',
       'export_formats.json','gravity_demand.json','continuous_walls.json','fixed_interfaces.json',
       'fixed_all_interfaces.json','magnet_seat_restoration.json']
if read(CFG)['revision'].startswith(('O23E-','O23F-','O23G-')):
    files.append('load_paths.json')
if read(CFG)['revision'].startswith(('O23F-','O23G-')):
    files.extend(['clean_design.json','physical_rod_count.json'])
if read(CFG)['revision'].startswith('O23G-'):
    files.extend(['smooth_connections.json','positive_sweeps.json'])
if read(B/'verification/export_formats.json').get('export_version'):
    files.extend(['stl_export_repair.json','stl_regression.json','slice_validation.json'])
reports={name:read(B/'verification'/name) for name in files}
for name,r in reports.items():assert r['geometry_sha256']==digest,('stale report',name)
g=reports['geometry.json'];daily=reports['daily_motion.json'];edge=reports['edge_paths.json']
assert g['kinematics']['passed'] and not g['geometry']['invalid_parts']
assert g['geometry']['height_under_800mm']
assert daily['passed'] and daily['complete_policy'] and not daily['trial']
assert edge['passed'] and not edge['trial']
assert reports['backpack_tool_access.json']['slim_tool_plan_passed']
assert reports['backpack_tool_access.json']['pcb_removal']['passed']
assert reports['fixed_interfaces.json']['passed']
assert reports['fixed_all_interfaces.json']['passed']
assert reports['magnet_seat_restoration.json']['passed']
if 'smooth_connections.json' in reports:
    assert reports['smooth_connections.json']['passed'] and reports['positive_sweeps.json']['passed']
    assert min(r['conservative_cut_area_mm2'] for r in reports['load_paths.json']['rows'])>=20
if 'clean_design.json' in reports:
    assert reports['clean_design.json']['passed']
    assert reports['physical_rod_count.json']['passed']
    assert reports['physical_rod_count.json']['maximum_rods_per_adjacent_component']<=3
wire_summary=None
if 'load_paths.json' in reports:
    assert reports['load_paths.json']['passed'] and reports['load_paths.json']['structure_count']==24
    wires=read(B/'harness/routing_plan.json')
    fixtures=read(B/'harness/wire_fixture_verification.json')
    channels=read(B/'harness/wire_channels.json')
    assert wires['geometry_sha256']==fixtures['geometry_sha256']==channels['geometry_sha256']==digest
    assert wires['capacity_passed'] and not wires['body_sections_missing_seats']
    assert fixtures['passed'] and all(r['passed'] for r in fixtures['channels'])
    assert len(wires['rows'])==46
    wire_summary=dict(seats=len(wires['seats']),internal_channels=len(channels['rows']),
        independent_five_core_routes=len(wires['rows']),fixture_geometry_passed=True,
        flexible_wire_fatigue_verified=False)
hip=read(B/'verification/hip_centers.json');collar=read(B/'verification/collar_static_packing.json')
assert hip['passed'] and hip['profile_sha256']==profile_signature(p)
assert collar['passed'] and collar['profile_sha256']==profile_signature(p)
wrist=read(B/'verification/right_wrist_boards.json')
assert wrist['passed'] and wrist['source_hardware_overrides_sha256']==sha(DROOT/'source/part_overrides.npz')
delivery=read(B/'DELIVERY.json');preview=read(B/'preview/provenance.json');renders=read(B/'images/provenance.json')
assert delivery['source_geometry_sha256']==preview['geometry_sha256']==renders['geometry_sha256']==digest
assert delivery['profile_sha256']==preview['profile_sha256']==sha(B/'profiles/device_profile.json')
for name,h in preview['asset_hashes'].items():assert sha(B/'preview'/name)==h
for r in reports['export_formats.json']['rows']:
    assert sha(B/r['review_3mf'])==r['review_3mf_sha256']
    assert sha(B/r['stl'])==r['stl_sha256']
    assert r['indexed_source_watertight'] and r['native_serialization']['indices_identical']
if 'stl_export_repair.json' in reports:
    ex=reports['export_formats.json'];repair=reports['stl_export_repair.json'];reg=reports['stl_regression.json'];slices=reports['slice_validation.json']
    assert repair['passed'] and reg['passed'] and slices['passed'] and not ex['stl_failures']
    assert reg['source_assembly_byte_identical'] and reg['configuration_byte_identical']
    assert reg['daily_poses']==408 and reg['transition_poses']==114 and reg['required_contacts']==0
    assert len(ex['rows'])==len(repair['rows'])==len(slices['rows'])==32
    assert repair['export_set_sha256']==reg['export_set_sha256']==slices['export_set_sha256']
    for r in ex['rows']:
        sr=next(x for x in slices['rows'] if x['id']==r['id'])
        nr=next(x for x in slices['native_mesh_audits'] if x['id']==r['id'])
        rr=next(x for x in repair['rows'] if x['id']==r['id'])
        assert r['stl_sha256']==sr['stl_sha256']==nr['stl_sha256']==rr['stl_sha256']
        assert sha(B/sr['validation_project'])==sr['project_sha256']==nr['project_sha256']
        assert sr['passed'] and nr['passed'] and nr['slicer_repair_count']==0
    for name,c in reg['checks'].items():
        assert sha(B/c['report'])==c['sha256'] and read(B/c['report'])['passed'],name
for name,h in renders['images'].items():assert sha(B/'images'/name)==h
result=dict(geometry_sha256=digest,profile_sha256=sha(B/'profiles/device_profile.json'),
    geometry_valid=True,body_kinematics_passed=True,daily_poses=daily['pose_count'],
    additional_transition_poses=edge['pose_count'],required_contacts=0,
    actual_hip_spacing_mm=hip['physical_center_spacing_mm'],
    maximum_hip_target_error_mm=max(x['error_mm'] for x in hip['hip_centers']),
    height_mm=g['geometry']['height_mm'],review_3mf_count=len(reports['export_formats.json']['rows']),
    stl_failures=reports['export_formats.json']['stl_failures'],
    stl_slicing_verified=reports['export_formats.json'].get('native_print_slicing_verified',False),
    checks_bound_to_current_geometry=files,manufacturing_release=False,
    harness=wire_summary,
    note='Artifact consistency audit; physical manufacture and arbitrary continuous paths remain unverified.')
put(B/'verification/delivery_audit.json',result)
print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
