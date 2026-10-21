"""Meaningful O17 regression, analytic rotation and hostile-data cases."""
from pathlib import Path
import copy, json, sys, unittest
import numpy as np
from device import forward, compound, quaternion, capture_window, digest
HERE=Path(__file__).resolve().parent
PORTABLE=(HERE.parent/'profiles/device_profile.json').exists()
H=HERE.parents[1]
BASE=HERE.parent if PORTABLE else H/'bench/revO17'
REPORT=BASE/'local_test_result.json' if PORTABLE else H/'generated/revO17/device_tests.json'
P=json.loads((BASE/'profiles/device_profile.json').read_text(encoding='utf-8-sig'))


def fixture():
    c={'status':'SYNTHETIC','device_id':'test-device','profile_sha256':digest(P),
       'axes':{k:{'sensor_zero_deg':180.,'reference_joint_deg':v,'sign':1} for k,v in P['neutral_raw_deg'].items()},
       'physical_tests':{k:False for k in P['required_physical_measurement_tests']}}
    scans=[{'device_id':'test-device','boot_id':'test-boot','capture_id':17,'sequence':i,
        'time_ms':1000.+i*100,'integrity':'valid',
        'channels':{k:{'sensor_deg':180.,'time_ms':990.+i*100,'status':'valid'} for k in P['raw_order']}}
        for i in range(6)]
    return c,scans


def capture(c,s): return capture_window(P,c,s,expected_capture_id=17,evaluation_time_ms=1510.)


class DeviceTests(unittest.TestCase):
    def test_single_hardware_and_no_missing_axis(self):
        self.assertEqual(P['hardware_models'],['universal'])
        self.assertEqual(len(P['joints']),25)
        self.assertEqual(len(set(P['raw_order'])),46)
        self.assertCountEqual([k for j in P['joints'] for k in j['raw_ids']],P['raw_order'])
    def test_analytic_noncommuting_rotations(self):
        # +90 around Z followed by -90 around Y, independently written basis.
        expected=np.array([[0,-1,0],[0,0,-1],[1,0,0]],float)
        np.testing.assert_allclose(compound('wide_tut',[90,0,-90,0])[:3,:3],expected,atol=1e-15)
        # Rx(-90): X->X, Y->-Z, Z->Y; then Ry(-90): X->Z, -Z->X, Y->Y.
        expected2=np.array([[0,1,0],[0,0,1],[1,0,0]],float)
        np.testing.assert_allclose(compound('ankle_core',[-90,90])[:3,:3],expected2,atol=1e-15)
    def test_cad_pose_regression(self):
        fixtures=json.loads((BASE/'profiles/pose_fixtures.json').read_text(encoding='utf-8-sig'))
        for pose in fixtures['poses']:
            for k,M in forward(P,pose['raw_deg']).items():
                np.testing.assert_allclose(M,pose['expected_frames_mm'][k],atol=1e-4,rtol=0)
    def test_random_raw_combinations_proper_rotations(self):
        rng=np.random.default_rng(16)
        for _ in range(100):
            q={k:float(rng.uniform(*P['raw_limits_deg'][k])) for k in P['raw_order']}
            for M in forward(P,q).values():
                self.assertAlmostEqual(np.linalg.det(M[:3,:3]),1.,places=7)
                np.testing.assert_allclose(M[:3,:3].T@M[:3,:3],np.eye(3),atol=1e-7)
                self.assertAlmostEqual(np.linalg.norm(quaternion(M)),1.,places=12)
        # These combinations prove mathematical coverage only, never collision safety.
    def test_180_degree_quaternion(self):
        q=quaternion(np.diag([1,-1,-1,1]));np.testing.assert_allclose(q,[1,0,0,0],atol=1e-15)
    def test_missing_raw_never_defaults_to_zero(self):
        q=copy.deepcopy(P['neutral_raw_deg']);q.pop(P['raw_order'][0])
        with self.assertRaises(ValueError): forward(P,q)
    def test_stable_capture_keeps_raw_and_calibration(self):
        c,s=fixture();out=capture(c,s)
        self.assertEqual(out['status'],'VALID_MEASUREMENT');self.assertFalse(out['hardware_capture_eligible'])
        self.assertEqual(out['raw_scans'],s);self.assertEqual(out['calibration'],c)
        self.assertEqual(out['target_adapter_status'],'NOT_APPLIED');self.assertFalse(out['contact_correction'])
        self.assertEqual(out['joint_angles_deg'],P['neutral_raw_deg'])
    def test_all46_channel_faults_rejected(self):
        for k in P['raw_order']:
            for fault in ('missing','nan','status','stale','future','outside','boolean'):
                with self.subTest(channel=k,fault=fault):
                    c,s=fixture();v=s[2]['channels'][k]
                    if fault=='missing': del s[2]['channels'][k]
                    elif fault=='nan':v['sensor_deg']=float('nan')
                    elif fault=='status':v['status']='fault'
                    elif fault=='stale':v['time_ms']=0
                    elif fault=='future':v['time_ms']=2000
                    elif fault=='outside':v['sensor_deg']=360
                    else:v['sensor_deg']=True
                    self.assertEqual(capture(c,s)['status'],'REJECTED')
    def test_identity_and_replay(self):
        for field,value in [('device_id','other'),('boot_id','reboot'),('capture_id',18),('sequence',0),('integrity','crc_error'),('time_ms',1001)]:
            c,s=fixture();s[3][field]=value
            self.assertEqual(capture(c,s)['status'],'REJECTED',field)
        c,s=fixture();s[-1]['channels']['unknown']={}
        self.assertEqual(capture(c,s)['status'],'REJECTED')
    def test_calibration_rejected(self):
        for change in ('incomplete','hash','sign','zero','count'):
            c,s=fixture();k=P['raw_order'][0]
            if change=='incomplete':c['status']='INCOMPLETE'
            elif change=='hash':c['profile_sha256']='wrong'
            elif change=='sign':c['axes'][k]['sign']=None
            elif change=='zero':c['axes'][k]['sensor_zero_deg']=None
            else:del c['axes'][k]
            self.assertEqual(capture(c,s)['status'],'REJECTED',change)
    def test_motion_window_and_scan_skew(self):
        c,s=fixture();s[3]['channels']['elbow_l.flex/r0']['sensor_deg']+=1
        self.assertEqual(capture(c,s)['status'],'REJECTED')
        c,s=fixture();s[2]['channels'][P['raw_order'][0]]['time_ms']-=70
        self.assertEqual(capture(c,s)['status'],'REJECTED')
    def test_wrap_and_calibrated_sign(self):
        c,s=fixture();k='elbow_l.flex/r0';c['axes'][k].update(sensor_zero_deg=359.,sign=-1)
        for scan in s:scan['channels'][k]['sensor_deg']=1.
        self.assertAlmostEqual(capture(c,s)['joint_angles_deg'][k],-2.)
    def test_stale_window_and_wrong_request(self):
        c,s=fixture()
        self.assertEqual(capture_window(P,c,s,expected_capture_id=17,evaluation_time_ms=3000)['status'],'REJECTED')
        self.assertEqual(capture_window(P,c,s,expected_capture_id=18,evaluation_time_ms=1510)['status'],'REJECTED')
    def test_short_window_and_gap(self):
        c,s=fixture();self.assertEqual(capture(c,s[:5])['status'],'REJECTED')
        for i,scan in enumerate(s):
            scan['time_ms']=1000+i*80
            for v in scan['channels'].values():v['time_ms']=scan['time_ms']-10
        self.assertEqual(capture(c,s)['status'],'REJECTED')
    def test_synthetic_never_qualifies_as_hardware(self):
        c,s=fixture();c['physical_tests']={k:True for k in c['physical_tests']}
        self.assertFalse(capture(c,s)['hardware_capture_eligible'])

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(DeviceTests))
    out={'status':'PASS' if result.wasSuccessful() else 'FAIL','tests_run':result.testsRun,
         'failures':len(result.failures),'errors':len(result.errors),'per_axis_fault_injections':46*7,
         'profile_sha256':digest(P),'runtime_sha256':__import__('hashlib').sha256((HERE/'device.py').read_bytes()).hexdigest(),
         'random_full_body_raw_combinations':100,'physical_tests':False,'UE_tests':False}
    REPORT.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    sys.exit(0 if result.wasSuccessful() else 1)
