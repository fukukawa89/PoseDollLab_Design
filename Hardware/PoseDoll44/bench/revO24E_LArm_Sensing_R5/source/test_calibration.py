from common import *
import tempfile
import calibrate

def run():
    template=load(OUT/'electronics/measurement_manifest_TEMPLATE.json')
    with tempfile.TemporaryDirectory(prefix='synthetic_calibration_',dir=OUT/'verification') as tmp:
        root=Path(tmp);(root/'captures').mkdir();meta=copy.deepcopy(template)
        for row in meta['measurements']:
            frames=[]
            for j in range(30):
                q={k:0 for k in ['RP','HS','RU','HE','RF','WF','WD']};q[row['axis']]=row['reference_deg']
                if 'wrist_flex_deg' in row:q['WF']=row['wrist_flex_deg']
                frames.append(dict(device=12345,channels={**{k:dict(valid=True,raw_deg=(30+1.01*v)%360) for k,v in q.items() if k!='WD'},'WD':dict(valid=True,field_mT=[20,.8*q['WD'],.15*q['WD']])}))
            put(root/row['capture'],dict(status='RAW_CAPTURE_NEEDS_CALIBRATION',error=None,frames=frames,synthetic_test_only=True))
        put(root/'manifest.json',meta);c=calibrate.build(root/'manifest.json');assert c['status']=='MEASURED_ACCEPTANCE_PASSED' and c['device']==12345
        checks=['Synthetic full-range captures exercise >180-degree MT branch and seven-axis calibration gates']
        bad=copy.deepcopy(meta);bad['measurements']=[r for r in bad['measurements'] if r['run']!='coupled'];put(root/'bad.json',bad)
        try:calibrate.build(root/'bad.json')
        except ValueError:checks.append('Missing coupled-wrist evidence is rejected')
        else:raise AssertionError('Missing wrist accepted')
        bad=copy.deepcopy(meta);bad['measurements'][0]['capture']=bad['measurements'][1]['capture'];put(root/'bad.json',bad)
        try:calibrate.build(root/'bad.json')
        except ValueError:checks.append('Reused capture cannot be claimed as independent validation')
        else:raise AssertionError('Duplicate accepted')
        row=next(r for r in meta['measurements'] if r['axis']=='WD' and r['run']=='validation_reverse');data=load(root/row['capture'])
        for f in data['frames']:f['channels']['WD']['field_mT'][0]+=10
        put(root/row['capture'],data)
        try:calibrate.build(root/'manifest.json')
        except ValueError:checks.append('Independent off-curve WD validation rejects a seemingly good fit')
        else:raise AssertionError('Bad independent validation accepted')
    put(OUT/'verification/calibration_software_tests.json',dict(passed=True,checks=checks,synthetic_only=True,usable_calibration_file_generated=False,hardware_connected=False))
    print('CALIBRATION SOFTWARE',len(checks),'checks PASS; synthetic fixtures removed',flush=True)

if __name__=='__main__':run()

