from pathlib import Path
import json,sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import revo3_evidence as ev
from capture_metrics_revo3 import metrics,analyze_segments
from pd41_protocol import encode_diagnostic,FIXED,FAULT,MISSING,NODE_INDICES
from study_revo3 import activate_contacts,vertical_reaction_vertices,contact_counterexample

def wire(seq=1,time=1000,boot=2,presence=63,fault=None,end=11000):
    words=[FIXED]*3+[123]*41;timings=[[0,end] for _ in range(6)]
    for node,inds in NODE_INDICES.items():
        if not presence&(1<<(node-1)):
            timings[node-1]=[0,0]
            for i in inds:words[i]=MISSING
    if fault is not None:words[fault]=FAULT|1
    return encode_diagnostic(words,timings,1,boot,seq,time,end,presence)

def trace(seq=1,boot=2,delay=200,span=6200,end=11000):
    return [dict(device_id='000000000001',boot_id=str(boot),usb_sequence=seq,node=n,node_delay_us=delay,node_span_us=span,g0_end_elapsed_us=end,association_verified=True,shared_clock_verified=True) for n in range(1,7)]

def test_11ms_arrival_is_not_8ms_sampling():
    m=metrics(wire());assert m['fresh_complete_normal_rate']==1;assert m['node_8ms_and_G0_14ms_trace']['status']=='NOT_OBSERVABLE'
    m=metrics(wire(),trace());assert m['node_8ms_and_G0_14ms_trace']['status']=='PASS_ASSOCIATED_RAW_TRACE';assert not m['hardware_30min_soak_pass']

@pytest.mark.parametrize('change',[{'span':7801},{'end':14000}])
def test_independent_sampling_and_strict_end_limits(change):
    assert metrics(wire(),trace(**change))['node_8ms_and_G0_14ms_trace']['status']=='FAIL_OR_INCOMPLETE_TRACE'

def test_raw_trace_requires_common_clock_and_explicit_association():
    t=trace();t[0]['shared_clock_verified']=False
    assert metrics(wire(),t)['node_8ms_and_G0_14ms_trace']['status']=='FAIL_OR_INCOMPLETE_TRACE'
    assert metrics(wire(),trace()+trace())['node_8ms_and_G0_14ms_trace']['status']=='FAIL_OR_INCOMPLETE_TRACE'

def test_low_frame_rate_contiguous_sequences_cannot_pass():
    m=metrics(b''.join(wire(i+1,1000+i*1000000) for i in range(10)))
    assert m['effective_output_Hz']==1;assert m['fresh_complete_by_sequence_only']==1;assert m['fresh_complete_normal_rate']<.02;assert not m['qualification_checks']['effective_rate_near_60Hz']

def test_long_pause_is_counted_even_if_sequence_has_no_gap():
    m=metrics(wire()+wire(2,1800_001_000));assert m['qualification_checks']['duration_at_least_30min'];assert m['fresh_complete_normal_rate']<.0001;assert m['maximum_output_interval_us']==1800_000_000

def test_health_is_per_node_and_fault_presence_not_normal():
    m=metrics(wire()+wire(2,17667,presence=59)+wire(3,34334,fault=3));assert m['presence_complete_frames']==2;assert m['all_41_angles_normal_frames']==1
    assert m['per_node'][2]['normal_fresh_frames']==2;assert m['per_node'][5]['normal_fresh_frames']==3;assert m['per_node'][5]['rate_including_missing_fault_and_recovery']==1

def test_stale_and_silent_session_change_rejected_explicit_reconnect_reported(tmp_path):
    m=metrics(wire()+wire()+wire(2,17667,boot=3));assert m['malformed_stale_or_changed_session_frames']==2
    (tmp_path/'one.bin').write_bytes(wire());(tmp_path/'two.bin').write_bytes(wire(1,1000,boot=3))
    spec={'segments':[{'path':'one.bin'},{'path':'two.bin'}]}
    with pytest.raises(ValueError):analyze_segments(spec,tmp_path)
    spec['segments'][1]['explicit_reconnect_reason']='G0 reboot observed';r=analyze_segments(spec,tmp_path)
    assert r['reconnect_count']==1 and r['segments'][1]['accepted_frames']==1 and not r['continuous_30min_session_verified']

def test_empty_capture_does_not_pass():
    assert metrics(b'')['status']=='NO_VALID_CAPTURE'

def test_airborne_force_counterexample_closed():
    q=contact_counterexample();assert q['unconstrained_airborne_max_N']==pytest.approx(10);assert q['geometry_activated_airborne_max_N']==0

@pytest.mark.parametrize('point,normal,state',[([0,0,20],[0,0,1],'INACTIVE_NO_NORMAL_REACTION'),([0,0,0],[1,0,0],'INACTIVE_NO_NORMAL_REACTION'),([0,0,-1],[0,0,1],'PENETRATION_REQUIRES_RESOLUTION')])
def test_gap_normal_penetration_gate(point,normal,state):
    q=activate_contacts([{'point_mm':point,'normal':normal}]);assert q[0]['state']==state;assert q[0]['normal_force_forced_zero'];assert not vertical_reaction_vertices(q,10,[0,0,0])

def sandbox(monkeypatch,tmp_path):
    monkeypatch.setattr(ev,'REPO',tmp_path);monkeypatch.setattr(ev,'VERIFY',tmp_path/'v');monkeypatch.setattr(ev,'GENERATED',tmp_path/'g');monkeypatch.setattr(ev,'git_head',lambda:'test');monkeypatch.setattr(ev,'sources',lambda:{'source':'original'})

def produce(run,folder):
    folder.mkdir();
    for name in ('housing.step','hollow_pin_spanner.step','J50_mate.step','board.kicad_pcb','layout.json'):(folder/name).write_text('original')
    assert run.step('producer',[sys.executable,'-c','pass'],artifact_roots=[folder])

@pytest.mark.parametrize('filename,damage',[('housing.step','replace'),('hollow_pin_spanner.step','delete'),('J50_mate.step','replace'),('board.kicad_pcb','replace'),('extra.step','add')])
def test_every_consumed_artifact_sealed(monkeypatch,tmp_path,filename,damage):
    sandbox(monkeypatch,tmp_path);r=ev.Run('mutation');folder=r.out/'parts';produce(r,folder);p=folder/filename
    if damage=='delete':p.unlink()
    else:p.write_text('mutated')
    assert not r.step('consumer',[sys.executable,'-c','raise RuntimeError("consumer must not run")'],dependencies=['producer']);assert r.steps['consumer']['status']=='BLOCKED_DEPENDENCY';assert r.finish()['status']=='INCOMPLETE_OR_FAILED'

def test_consumer_reader_rejects_undeclared_or_changed_step(monkeypatch,tmp_path):
    sandbox(monkeypatch,tmp_path);r=ev.Run('reader');folder=r.out/'parts';produce(r,folder);monkeypatch.setenv('REVO3_RUN_ID','reader');monkeypatch.setenv('REVO3_DEPENDENCIES',json.dumps({'producer':r.steps['producer']['artifacts']}));a=ev.ArtifactReader('producer');assert a.path(folder/'housing.step').exists();(folder/'housing.step').write_text('changed')
    with pytest.raises(ev.BlockedInput):a.path(folder/'housing.step')
    with pytest.raises(ev.BlockedInput):a.receipt()

def test_failed_producer_does_not_use_old_golden(monkeypatch,tmp_path):
    sandbox(monkeypatch,tmp_path);r=ev.Run('stale');golden=r.out/'golden.bin';golden.write_bytes(b'old')
    assert not r.step('host',[sys.executable,'-c','raise SystemExit(7)'],expected_paths=[golden]);assert not r.step('bridge',[sys.executable,'-c','pass'],dependencies=['host'])

def test_manifest_and_report_source_tampering(monkeypatch,tmp_path):
    sandbox(monkeypatch,tmp_path);r=ev.Run('meta');folder=r.out/'parts';produce(r,folder);record=r.steps['producer']['artifacts'];(tmp_path/record['path']).write_text('{}')
    assert not r.step('consumer',[sys.executable,'-c','pass'],dependencies=['producer'])
    monkeypatch.setattr(ev,'sources',lambda:{'source':'tampered'});assert r.finish()['source_changed_during_run']==['source']

def test_zero_exit_without_output_and_immutable_run(monkeypatch,tmp_path):
    sandbox(monkeypatch,tmp_path);r=ev.Run('missing');assert not r.step('producer',[sys.executable,'-c','pass'],expected_paths=[r.out/'absent'])
    assert not r.step('consumer',[sys.executable,'-c','pass'],dependencies=['producer'])
    with pytest.raises(FileExistsError):ev.Run('missing')


@pytest.mark.parametrize('values',[[],['G0'],['G0','N1','N2','N3','N4','N5','N5'],['G0','N1','N2','N3','N4','N5','N6','N7']])
def test_O3_role_set_is_exact(values):
    from report_revo3 import exact_set,ROLES
    with pytest.raises(ValueError):exact_set([{'role':v} for v in values],'role',ROLES)

def test_O3_missing_axis_and_missing_reports_cannot_pass():
    from report_revo3 import exact_set,assess
    with pytest.raises(ValueError):exact_set([{'axis_id':'one'}],'axis_id',{'one','two'})
    assert assess({},'empty')['gates']['V0']['status']=='FAIL'

def test_mass_policy_and_itemized_allocation_transfer():
    from study_revo3 import reconcile
    req=json.loads((ev.HW/'mechanical_manifest/requirements_revO3.json').read_text(encoding='utf-8'))
    assert req['mass_policy']['hard_max_g'] is None and not req['mass_policy']['exceedance_fails_design']
    rows=[{'part_id':'axis/disc_spring_1','scope':'R2 CAD part on provisional axis transform','mass_g':2,'mass_source':'CAD'}, {'part_id':'unresolved_fasteners_springs/link','scope':'allocation','mass_g':100,'mass_source':'retained'}, {'part_id':'axis/housing','scope':'R2 CAD part on provisional axis transform','mass_g':7,'mass_source':'CAD'}]
    r=reconcile(rows);assert r['explicit_coverage_transfer_g']==2 and r['remaining_hardware_allocation_g']==98;assert rows[-1]['mass_g']==7


def test_lying_case_rotates_gravity_frame_not_just_empty_joint_angles():
    import numpy as np
    from study_revo3 import root_rotation_for_case
    assert np.allclose(root_rotation_for_case('left_side_lying')@np.array([0,0,1]),[0,1,0])
    assert np.allclose(root_rotation_for_case('right_side_lying')@np.array([0,0,1]),[0,-1,0])
    assert np.allclose(root_rotation_for_case('prone')@np.array([0,0,1]),[1,0,0])
    assert np.allclose(root_rotation_for_case('neutral'),np.eye(3))


@pytest.mark.parametrize('change',['changed_config','removed_header','new_source','changed_recipe'])
def test_firmware_reuse_refuses_different_real_build_inputs(change):
    from import_revo3_firmware import match_firmware_inputs
    old={'Firmware/PoseDollFullBody/main/pd41_core.h':'a','Firmware/PoseDollFullBody/revO3/sdkconfig.G0.defaults':'b','scripts/build_revo3_firmware.py':'c'}
    new=dict(old)
    if change=='changed_config':new['Firmware/PoseDollFullBody/revO3/sdkconfig.G0.defaults']='changed'
    elif change=='removed_header':del new['Firmware/PoseDollFullBody/main/pd41_core.h']
    elif change=='new_source':new['Firmware/PoseDollFullBody/revO3/main/new.c']='new'
    else:new['scripts/build_revo3_firmware.py']='changed'
    with pytest.raises(ev.BlockedInput):match_firmware_inputs(old,new)

def test_firmware_reuse_can_separate_unrelated_mechanical_change():
    from import_revo3_firmware import match_firmware_inputs
    old={'Firmware/PoseDollFullBody/main/pd41_core.h':'a','Hardware/PoseDoll44/cad/revO3/compact_joint.py':'x'}
    new={**old,'Hardware/PoseDoll44/cad/revO3/compact_joint.py':'y'}
    assert match_firmware_inputs(old,new)=={'Firmware/PoseDollFullBody/main/pd41_core.h':'a'}
