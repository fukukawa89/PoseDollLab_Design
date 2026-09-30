"""Focused execution of the byte-verified O4 Python oracle.
Uses a declared synthetic profile and helper shim, not the whole simulator or UE.
"""
from pathlib import Path
import hashlib, importlib.util, json, math, sys, types, unittest
ROOT=Path(__file__).resolve().parent

def strict_json(data):
    def pairs(items):
        d={}
        for k,v in items:
            if k in d: raise ValueError('duplicate JSON field')
            d[k]=v
        return d
    return json.loads(data, object_pairs_hook=pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
def uint64(text):
    if not isinstance(text,str) or not text.isascii() or not text.isdecimal() or len(text)>20 or (len(text)>1 and text[0]=='0'):
        raise ValueError('uint64')
    n=int(text)
    if n>2**64-1: raise ValueError('uint64 overflow')
    return n
pkg=types.ModuleType('o4_oracle');pkg.__path__=[str(ROOT/'source')];sys.modules[pkg.__name__]=pkg
core=types.ModuleType('o4_oracle.core');core.strict_json=strict_json;core.uint64=uint64;sys.modules[core.__name__]=core
source=ROOT/'source/static_protocol.py';data=source.read_bytes()
assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()=='9da33939b4fca5ab4e2c69bd334f4394f3ea3fdb'
spec=importlib.util.spec_from_file_location('o4_oracle.static_protocol',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Profile:
    profile_hash='profile-test';calibration_hash='cal-test'
    order=['pelvis.yaw','pelvis.pitch','pelvis.roll']+[f'test.axis.{i}' for i in range(41)]
    cal={aid:dict(sign=1,joint_rad_per_sensor_rad=1,raw_period_rad=2*math.pi,zero_raw_rad=math.pi) for aid in order[3:]}
    axes={aid:dict(limits_rad=[-math.radians(170),math.radians(170)]) for aid in order[3:]}
p=Profile();hello=m.hello(p,'device-test','gateway-1',[f'node-{i}-boot1' for i in range(6)])
REQ=1_000_000;WALL=100.0

def ack(cid='new'):
    return dict(m.command(hello,cid,'accepted'),request_start_us=str(REQ),source_boots=hello['source_boots'][:])
def scan(sid,cid='new',q=0.0):
    start=REQ+(sid-1)*100000;end=start+40000
    return dict(m.command(hello,cid,'scan'),request_start_us=str(REQ),source_boots=hello['source_boots'][:],scan_id=str(sid),start_us=str(start),end_us=str(end),duration_us=40000,raw_angles_rad=[None]*3+[math.pi+q]*41,axis_status=['fixed']*3+['valid']*41)
def received(msg): return WALL+(int(msg['end_us'])-REQ)/1e6+.005

def window():
    w=m.StaticWindow(p,hello,'new',WALL);w.push(ack(),WALL+.001);return w

class Audit(unittest.TestCase):
    def test_healthy_seven_scans(self):
        w=window()
        for sid in range(1,8):
            msg=scan(sid);w.push(msg,received(msg))
        self.assertEqual(w.state,'SnapshotReady');self.assertEqual(w.final['scan_id'],'7');self.assertGreaterEqual(w.stable_us,500000)
    def test_late_cancelled_reply_faults_new_request_current_behavior(self):
        w=window();old=scan(1,'cancelled-old')
        with self.assertRaises(ValueError): w.push(old,received(old))
        self.assertEqual(w.state,'Fault');self.assertIsNone(w.final)
    def test_valid_new_reply_cannot_revive_faulted_transaction(self):
        w=window()
        try: w.push(scan(1,'cancelled-old'),WALL+.05)
        except ValueError: pass
        with self.assertRaisesRegex(ValueError,'No pending'): w.push(scan(1),WALL+.06)
    def test_fault_word_is_not_a_pose(self):
        w=window();msg=scan(1);msg['axis_status'][10]='invalid';msg['raw_angles_rad'][10]=None
        with self.assertRaises(ValueError): w.push(msg,received(msg))
        self.assertIsNone(w.final)
    def test_boot_change_rejected(self):
        w=window();msg=scan(1);msg['source_boots'][2]='rebooted'
        with self.assertRaises(ValueError): w.push(msg,received(msg))
    def test_overlong_scan_rejected(self):
        w=window();msg=scan(1);msg['duration_us']=100001;msg['end_us']=str(int(msg['start_us'])+100001)
        with self.assertRaises(ValueError): w.push(msg,received(msg))
    def test_slow_drift_does_not_become_ready(self):
        w=window()
        for sid in range(1,20):
            msg=scan(sid,q=math.radians(.3*(sid-1)*.1));w.push(msg,received(msg))
        self.assertEqual(w.state,'WaitStable');self.assertIsNone(w.final)
    def test_stale_final_rejected(self):
        w=window()
        for sid in range(1,7):
            msg=scan(sid);w.push(msg,received(msg))
        msg=scan(7)
        with self.assertRaisesRegex(ValueError,'STALE_FINAL'): w.push(msg,received(msg)+.3)
    def test_deadline_rejected(self):
        w=window()
        with self.assertRaises(ValueError): w.push(scan(1),WALL+3.01)
        self.assertEqual(w.state,'TimedOut')
    def test_crc_corruption_rejected(self):
        wrapped=m.envelope(scan(1));wrapped['crc32']='00000000'
        with self.assertRaises(ValueError): m.unwrap(wrapped)

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Audit)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report=dict(scope='O4 Python oracle, synthetic profile; no UE run or physical test',tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),late_cancelled_packet_current_state='Fault',old_pose_accepted=False,source_git_blob='9da33939b4fca5ab4e2c69bd334f4394f3ea3fdb')
    (ROOT/'results/static_window.json').write_text(json.dumps(report,indent=2))
    sys.exit(0 if result.wasSuccessful() else 1)
