"""Regressions for failure modes introduced by miniaturization and G0 separation."""
import sys
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from revo_common import HW, OUT, VERIFY, read
from study_revo import anatomy, fk

@pytest.mark.parametrize('character',['manny','quinn'])
@pytest.mark.parametrize('height',[420,450,480])
def test_anatomy_scaling_keeps_ratio_and_axes(character,height):
    p=anatomy(character,height);old=read(HW/f'mechanical_manifest/physical_{character}_44_revG_humanform_trial.json')
    newT,A=fk(p,{});oldT,_=fk(old,{})
    k=height/old['design_reference']['mesh_N_pose_surface_height_mm']
    for node in newT:np.testing.assert_allclose(newT[node][:3,3],oldT[node][:3,3]*k,atol=1e-9)
    assert p['axis_order']==old['axis_order'] and p['axes']==old['axes'] and len(A)==44
    assert p['status']=='ANATOMY_ONLY_NOT_ASSEMBLABLE_NOT_DEVICE_CALIBRATION'

def test_two_characters_keep_distinct_proportions():
    m,_=fk(anatomy('manny',480),{});q,_=fk(anatomy('quinn',480),{})
    ml=np.linalg.norm(m['upperarm_l'][:3,3]-m['elbow_l'][:3,3]);ql=np.linalg.norm(q['upperarm_l'][:3,3]-q['elbow_l'][:3,3])
    assert abs(ml-ql)>1

def test_external_gateway_does_not_renumber_measurement_slots():
    old=read(HW/'mechanical_manifest/network_revM.json');new=read(HW/'mechanical_manifest/network_revO.json')
    assert new['protocol_order']==old['protocol_order'] and new['fixed_indices']==[0,1,2]
    assert [n['ports'] for n in new['nodes']]==[n['ports'] for n in old['nodes']]
    assert sorted(p['protocol_index'] for n in new['nodes'] for p in n['ports'])==list(range(3,44))
    assert new['gateway']['measurement_channels']==0 and len(new['nodes'])==6 and new['can']['node_count']==7
    assert new['can']['termination_nodes']==['G0','N4']

def test_unplug_direction_is_not_counted_as_board_length():
    data=read(VERIFY/'size_tradeoff.json')
    for candidate in data['candidates']:
        c=candidate['constraints'][0]
        assert c['required_mm']==66
        assert abs(c['deficit_mm']-max(0,66-c['available_mm']))<1e-9

def test_candidate_is_not_false_complete_assembly():
    data=read(VERIFY/'size_tradeoff.json')
    assert data['selected_manufacturable_height_mm'] is None
    for candidate in data['candidates']:
        assert candidate['complete_body_height_mm'] is None and candidate['complete_body_mass_g'] is None
        assert not candidate['physical_tested'] and not candidate['manufacturing_released']
        assert candidate['status']=='LAYOUT_BLOCKED_CURRENT_COMPONENT_ARRANGEMENT'
        assert candidate['motion_path_check']=='NOT_RUN'

def test_fixed_hardware_and_service_zone_are_present():
    config=read(HW/'mechanical_manifest/desktop_revO.json')
    assert config['hardware_fixed']['magnet_diameter_mm']==6
    joints=read(VERIFY/'joint_study.json')
    for family in joints.values():
        assert not family['fixed_hardware_scaled']
        assert family['nominal_gap_mm']==1.5
        assert 'reservation_intersections' in family
        assert any(p['role']=='reservation' and 'tool' in p['name'] for p in family['parts'])
        assert any('sensor_pcba_existing_' in p['name'] for p in family['parts'])

def test_nine_ports_still_have_independent_buffers_and_connectors():
    layout=read(HW/'electronics/revO/node_9port/layout.json')
    refs={c['ref']:c for c in layout['components']}
    for i in range(1,10):
        assert refs[f'U{10+i}']['value']=='SN74LVC125APWR'
        assert refs[f'J{10+i}']['value'].startswith(f'P{i} sensor')
    assert 'J4' not in refs  # G0 alone carries everyday USB.

def test_bandwidth_is_not_mistaken_for_timing_qualification():
    report=read(VERIFY/'can_budget.json')
    assert report['frames_per_cohort']==30
    assert abs(report['utilization_data_end_sync']-.486)<1e-12
    assert report['timing_verified'] is False and report['excluded']
