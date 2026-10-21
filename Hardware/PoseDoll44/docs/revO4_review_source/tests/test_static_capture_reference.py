import dataclasses, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from static_capture_reference import Scan, CaptureRejected, accept_static_window, FIXED

class StaticTests(unittest.TestCase):
    def setUp(self):
        self.scans = [Scan('request-A','G0-boot-A','profile-A','cal-A',i+1,
            1_000_000+i*100_000, 1_040_000+i*100_000,
            tuple(f'node{j}-bootA' for j in range(6)),
            (FIXED,)*3+(1000,)*41, True) for i in range(7)]
        self.kw = dict(capture_id='request-A',gateway_session='G0-boot-A',
            profile_hash='profile-A',calibration_hash='cal-A',
            request_start_us=1_000_000,now_us=1_660_000)
    def reject(self, scans=None, **kw):
        with self.assertRaises(CaptureRejected):
            accept_static_window(scans or self.scans, **(self.kw|kw))
    def test_accepts_stable_final_scan_not_averaged(self):
        out=accept_static_window(self.scans,**self.kw)
        self.assertEqual(out.words,self.scans[-1].words)
        self.assertEqual(out.source_start_us,1_600_000)
    def test_real_zero_angle_allowed(self):
        scans=[dataclasses.replace(s,words=(FIXED,)*3+(0,)*41) for s in self.scans]
        self.assertEqual(accept_static_window(scans,**self.kw).words[3],0)
    def test_fault_not_valid(self):
        self.scans[2]=dataclasses.replace(self.scans[2],words=(FIXED,)*3+(0x8001,)+(1000,)*40)
        self.reject()
    def test_missing_not_valid(self):
        self.scans[2]=dataclasses.replace(self.scans[2],words=(FIXED,)*3+(0xffff,)+(1000,)*40)
        self.reject()
    def test_bad_crc(self):
        self.scans[4]=dataclasses.replace(self.scans[4],crc_verified=False);self.reject()
    def test_duplicate_id(self):
        self.scans[3]=dataclasses.replace(self.scans[3],scan_id=3);self.reject()
    def test_missing_scan(self):
        self.scans[3]=dataclasses.replace(self.scans[3],scan_id=99);self.reject()
    def test_old_request(self):
        self.scans[1]=dataclasses.replace(self.scans[1],capture_id='previous');self.reject()
    def test_gateway_restart(self):
        self.scans[4]=dataclasses.replace(self.scans[4],gateway_session='new');self.reject()
    def test_node_restart(self):
        self.scans[4]=dataclasses.replace(self.scans[4],node_boots=('new',)+self.scans[4].node_boots[1:]);self.reject()
    def test_profile_change(self):
        self.scans[4]=dataclasses.replace(self.scans[4],profile_hash='other');self.reject()
    def test_calibration_change(self):
        self.scans[4]=dataclasses.replace(self.scans[4],calibration_hash='other');self.reject()
    def test_real_root_zero_is_not_fixed(self):
        self.scans[0]=dataclasses.replace(self.scans[0],words=(0,0,0)+(1000,)*41);self.reject()
    def test_timestamp_reversal(self):
        self.scans[0]=dataclasses.replace(self.scans[0],end_us=900_000);self.reject()
    def test_future_scan(self):
        self.scans[-1]=dataclasses.replace(self.scans[-1],end_us=2_000_000);self.reject()
    def test_final_age(self):self.reject(now_us=1_900_000)
    def test_transaction_deadline(self):self.reject(now_us=4_000_001)
    def test_scan_span(self):
        self.scans[-1]=dataclasses.replace(self.scans[-1],end_us=1_740_000);self.reject(now_us=1_740_000)
    def test_boolean_is_not_word(self):
        self.scans[0]=dataclasses.replace(self.scans[0],words=(FIXED,)*3+(True,)+(1000,)*40);self.reject()
    def test_slow_drift_adjacent_differences_small(self):
        for i,s in enumerate(self.scans):
            self.scans[i]=dataclasses.replace(s,words=(FIXED,)*3+(1000+i*2,)+(1000,)*40)
        self.reject() # ~0.44 deg/s despite tiny per-scan steps.
    def test_transient_move_then_back_is_seen(self):
        self.scans[3]=dataclasses.replace(self.scans[3],words=(FIXED,)*3+(1100,)+(1000,)*40);self.reject()
    def test_circular_wrap_not_a_360_degree_jump(self):
        for i,s in enumerate(self.scans):
            self.scans[i]=dataclasses.replace(s,words=(FIXED,)*3+((16383 if i%2 else 0),)+(1000,)*40)
        self.assertEqual(accept_static_window(self.scans,**self.kw).scan_id,7)
    def test_insufficient_duration(self): self.reject(self.scans[:6])
    def test_pretrigger_cannot_be_reused(self):self.reject(request_start_us=1_000_001)
    def test_overlapping_scans(self):
        self.scans[1]=dataclasses.replace(self.scans[1],start_us=1_030_000);self.reject()
    def test_uint16_elapsed_does_not_roundtrip_100ms(self):
        self.assertNotEqual(100_000 & 0xffff,100_000)
    def test_observation_cannot_certify_between_sample_motion(self):
        # Deliberately the same samples: an inter-sample oscillation cannot be detected.
        # This test records the limitation, not a physical safety guarantee.
        self.assertEqual(accept_static_window(self.scans,**self.kw).scan_id,7)
if __name__=='__main__':unittest.main(verbosity=2)
