from pathlib import Path
import sys,json
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import revo2_evidence as evidence
from report_revo2 import exact_set,checked_report,assess,ROLES
from capture_metrics_revo2 import metrics
from pd41_protocol import encode_diagnostic,FIXED,FAULT

@pytest.mark.parametrize('roles',[[],['G0'],['G0','N1','N2','N3','N4','N5','N5'],['G0','N1','N2','N3','N4','N5','N6','N7']])
def test_expected_set_cannot_pass_empty_partial_duplicate_extra(roles):
 with pytest.raises(ValueError):exact_set([{'role':n} for n in roles],'role',ROLES)

def test_current_run_and_replaced_report(tmp_path):
 p=tmp_path/'proof.json';p.write_text(json.dumps({'run_id':'old','status':'PASS'}))
 with pytest.raises(ValueError):checked_report(p,'new')
 p.write_text(json.dumps({'run_id':'new','status':'PASS'}));h=evidence.sha(p);assert checked_report(p,'new',h)['status']=='PASS'
 p.write_text(json.dumps({'run_id':'new','status':'PASS','changed':True}))
 with pytest.raises(ValueError):checked_report(p,'new',h)
 p.unlink()
 with pytest.raises(ValueError):checked_report(p,'new',h)

def test_all_missing_reports_cannot_pass(tmp_path):
 assert assess(tmp_path,'new',{})['gates']['V0']['status']=='FAIL'

def test_producer_failure_blocks_golden_consumer(tmp_path,monkeypatch):
 monkeypatch.setattr(evidence,'REPO',tmp_path);monkeypatch.setattr(evidence,'git_head',lambda:'unit-test');monkeypatch.setattr(evidence,'VERIFY',tmp_path/'verify');monkeypatch.setattr(evidence,'GENERATED',tmp_path/'generated');monkeypatch.setattr(evidence,'sources',lambda:{'test':'abc'})
 run=evidence.Run('test');assert not run.step('producer',[sys.executable,'-c','raise SystemExit(7)'])
 marker=tmp_path/'should_not_exist';consumer=[sys.executable,'-c',f'from pathlib import Path;Path({str(marker)!r}).write_text("bad")']
 assert not run.step('golden',consumer,dependencies=['producer']);assert not marker.exists();assert run.steps['golden']['status']=='BLOCKED_DEPENDENCY'
 assert run.finish()['status']=='INCOMPLETE_OR_FAILED'
 with pytest.raises(FileExistsError):evidence.Run('test')

def test_zero_exit_missing_output_blocks_dependency(tmp_path,monkeypatch):
 monkeypatch.setattr(evidence,'REPO',tmp_path);monkeypatch.setattr(evidence,'git_head',lambda:'unit-test');monkeypatch.setattr(evidence,'VERIFY',tmp_path/'v');monkeypatch.setattr(evidence,'GENERATED',tmp_path/'g');monkeypatch.setattr(evidence,'sources',lambda:{'test':'abc'})
 run=evidence.Run('missing');assert not run.step('producer',[sys.executable,'-c','pass'],expected_paths=[tmp_path/'absent.bin'])
 assert not run.step('downstream',[sys.executable,'-c','pass'],dependencies=['producer']);assert run.steps['downstream']['status']=='BLOCKED_DEPENDENCY'

def test_input_change_invalidates_successful_run(tmp_path,monkeypatch):
 monkeypatch.setattr(evidence,'REPO',tmp_path);monkeypatch.setattr(evidence,'git_head',lambda:'unit-test');monkeypatch.setattr(evidence,'VERIFY',tmp_path/'v');monkeypatch.setattr(evidence,'GENERATED',tmp_path/'g');fingerprint={'test':'abc'};monkeypatch.setattr(evidence,'sources',lambda:dict(fingerprint))
 run=evidence.Run('changed');assert run.step('ok',[sys.executable,'-c','pass']);fingerprint['test']='changed'
 assert run.finish()['status']=='FAIL_INPUT_CHANGED_DURING_RUN'

def test_presence_is_not_all_angles_normal_and_stale_is_rejected():
 good=[FIXED]*3+[123]*41;fault=good.copy();fault[3]=FAULT|1
 a=encode_diagnostic(good,[[0,7000]]*6,1,2,1,1000,7000,63)
 b=encode_diagnostic(fault,[[0,7000]]*6,1,2,2,18000,7000,63)
 r=metrics(a+b+a);assert r['presence_complete_frames']==2;assert r['all_41_angles_normal_frames']==1;assert r['fresh_complete_normal_rate']==.5;assert r['malformed_stale_or_changed_session_frames']==1
 assert not r['physical_CAN_END_14ms_deadline_verified'];assert not r['hardware_30min_soak_pass']

def test_no_capture_never_passes():
 r=metrics(b'');assert r['status']=='NO_VALID_CAPTURE';assert r['fresh_complete_normal_rate'] is None

@pytest.mark.parametrize('damage',['replace','delete'])
def test_changed_producer_output_blocks_consumer(tmp_path,monkeypatch,damage):
 monkeypatch.setattr(evidence,'REPO',tmp_path);monkeypatch.setattr(evidence,'git_head',lambda:'unit-test');monkeypatch.setattr(evidence,'VERIFY',tmp_path/'v');monkeypatch.setattr(evidence,'GENERATED',tmp_path/'g');monkeypatch.setattr(evidence,'sources',lambda:{'test':'abc'})
 run=evidence.Run('tampered');out=tmp_path/'golden.bin'
 assert run.step('producer',[sys.executable,'-c',f'from pathlib import Path;Path({str(out)!r}).write_bytes(b"fresh")'],expected_paths=[out])
 if damage=='replace':out.write_bytes(b'old')
 else:out.unlink()
 assert not run.step('consumer',[sys.executable,'-c','pass'],dependencies=['producer'])
 assert run.steps['consumer']['status']=='BLOCKED_DEPENDENCY'
