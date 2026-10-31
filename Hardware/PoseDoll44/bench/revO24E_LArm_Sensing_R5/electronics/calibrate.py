"""Fit ONLY actual saved captures; validate against independent known-angle records."""
import argparse,json,math
from pathlib import Path
import numpy as np
from arm_reader import CHANNELS,angles,wrap,vector_angle

def build(manifest):
    base=Path(manifest).resolve().parent;meta=json.loads(Path(manifest).read_text('utf8'));records=[];seen=set();devices=set()
    for r in meta['measurements']:
        if r['capture'] in seen:raise ValueError('Do not reuse a calibration capture as independent validation')
        seen.add(r['capture'])
        d=json.loads((base/r['capture']).read_text('utf8'))
        if d['status'] not in ['RAW_CAPTURE_NEEDS_CALIBRATION','VALID_CALIBRATED_CAPTURE'] or d.get('error') or len(d['frames'])<25:raise ValueError('Invalid/short measurement '+r['capture'])
        if any(not all(f['channels'][k]['valid'] for k in [*CHANNELS,'WD']) for f in d['frames']):raise ValueError('Sensor fault in capture')
        records.append((r,d['frames']))
        devices.update(f['device'] for f in d['frames'])
    if len(devices)!=1:raise ValueError('All captures must come from one controller/device')
    cal=dict(schema='R5_7_AXIS_CALIBRATION/1',status='INCOMPLETE',channels={},source_manifest=str(Path(manifest).resolve()),evidence=[])
    limits=meta['limits_deg']
    for key in [*CHANNELS,'WD']:
        fit=[(r,fs) for r,fs in records if r['axis']==key and r['run']=='calibration']
        if len(fit)<11:raise ValueError(key+': need at least 11 measured calibration stations')
        fit.sort(key=lambda x:x[0]['reference_deg']);qs=np.array([r['reference_deg'] for r,fs in fit]);lo,hi=limits[key]
        if qs[0]>lo+.25 or qs[-1]<hi-.25 or np.any(np.diff(qs)<=0):raise ValueError(key+': full monotonic range not covered')
        if key=='WD':
            if np.max(np.diff(qs))>5.01:raise ValueError('WD station spacing >5 degrees')
            vs=np.array([np.mean([f['channels'][key]['field_mT'] for f in fs],axis=0) for r,fs in fit])
            noise=max(float(np.max(np.std([f['channels'][key]['field_mT'] for f in fs],axis=0))) for r,fs in fit)
            if noise>.1:raise ValueError('WD stationary noise >0.1 mT')
            c=dict(kind='TMAG_1D_VECTOR_LUT',limits_deg=[lo,hi],lut=np.column_stack([qs,vs]).tolist(),max_residual_mT=min(.5,max(.15,6*noise)),direction_verified=True,range_verified=True,coupled_wrist_verified=True,forward_reverse_verified=True)
        else:
            vals=np.array([np.rad2deg(np.angle(np.mean(np.exp(1j*np.deg2rad([f['channels'][key]['raw_deg'] for f in fs])))))%360 for r,fs in fit])
            un=np.rad2deg(np.unwrap(np.deg2rad(vals)));slope=np.polyfit(qs,un,1)[0];sign=1 if slope>0 else -1
            if not .85<abs(slope)<1.15:raise ValueError(key+': wrong axis/direction/scale')
            pred=qs[0]+sign*(un-un[0]);lut=np.column_stack([pred,qs-pred]).tolist()
            c=dict(reference_raw_deg=float(vals[0]),reference_joint_deg=float(qs[0]),sign=sign,limits_deg=[lo,hi],direction_verified=True,range_verified=True,correction_lut=lut)
        cal['channels'][key]=c
    # Flags above are temporary to run the decoder; output is written only after all gates pass.
    for key in [*CHANNELS,'WD']:
        for run in ['validation_forward','validation_reverse']+(['coupled'] if key=='WD' else ['cross_joint']):
            tests=[(r,fs) for r,fs in records if r['axis']==key and r['run']==run]
            if len(tests)<(9 if run=='coupled' else 3 if run=='cross_joint' else 5):raise ValueError(key+': missing '+run+' validation stations')
            errs=[]
            for r,fs in tests:
                measured=[angles(f,cal)[key] for f in fs];errs.extend(float(q-r['reference_deg']) for q in measured)
                if max(measured)-min(measured)>1.0:raise ValueError(key+': stationary peak-to-peak >1 degree')
            worst=max(abs(x) for x in errs);rms=float(np.sqrt(np.mean(np.square(errs))))
            if worst>2.0 or rms>1.0:raise ValueError(key+': angle validation exceeds max2/RMS1 degree')
            cal['evidence'].append(dict(axis=key,run=run,stations=len(tests),max_abs_error_deg=worst,rms_error_deg=rms))
    wdtests=[r for r,fs in records if r['axis']=='WD' and r['run']=='coupled']
    if not all(any(abs(r.get('wrist_flex_deg',999)-f)<1 and abs(r['reference_deg']-d)<1 for r in wdtests) for f in [-65,0,70] for d in [-20,0,30]):raise ValueError('WD coupled 3 x 3 grid incomplete')
    cal['device']=next(iter(devices));cal['status']='MEASURED_ACCEPTANCE_PASSED';return cal

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    result=build(a.manifest);Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(result['status'])
