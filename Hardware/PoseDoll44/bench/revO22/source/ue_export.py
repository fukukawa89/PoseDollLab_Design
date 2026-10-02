"""Revalidate stored O22 measurement and export orientation deltas for UE.
Root/world translation, contacts, target lengths and finger animation are not inferred.
"""
from pathlib import Path
import argparse,json,hashlib
from device import forward,digest
from measurement import capture_window
SEMANTICS=['pelvis','waist','chest','head','clavicle_l','clavicle_r','upperarm_l','upperarm_r',
 'lowerarm_l','lowerarm_r','hand_l','hand_r','thigh_l','thigh_r','calf_l','calf_r','foot_l','foot_r','ball_l','ball_r']
def export(profile,record,allow_synthetic=False):
 m=record.get('measurement',record)
 if m.get('status')!='VALID_MEASUREMENT':raise ValueError('invalid saved measurement')
 raw=m['raw_scans'];cal=m['calibration']
 if record.get('packets_hex'):
  from usb_capture import decode,measurement_scans,SCAN
  decoded=[decode(bytes.fromhex(packet)) for packet in record['packets_hex']]
  frames=[frame for frame in decoded if frame['type']==SCAN]
  if not frames:raise ValueError('raw USB scan evidence missing')
  replay=measurement_scans(profile,frames,frames[0]['capture'])
  if digest(replay)!=digest(raw):raise ValueError('raw USB evidence disagrees with saved scans')
 elif not allow_synthetic:raise ValueError('original USB packets required for production export')
 verified=capture_window(profile,cal,raw,expected_capture_id=raw[0]['capture_id'],
                         evaluation_time_ms=m['capture_evaluation_time_ms'])
 if verified['status']!='VALID_MEASUREMENT':raise ValueError('revalidation: '+verified.get('reason',''))
 if not verified['hardware_capture_eligible'] and not allow_synthetic:raise ValueError('physical qualification incomplete; production export refused')
 if verified['joint_angles_deg']!=m['joint_angles_deg'] or digest(cal)!=m['calibration_sha256']:raise ValueError('measurement/calibration altered')
 neutral=forward(profile,profile['neutral_raw_deg']);actual=forward(profile,verified['joint_angles_deg']);rotations={}
 for semantic in SEMANTICS:
  physical=semantic.replace('lowerarm_','forearm_')
  rotations[semantic]=(actual[physical][:3,:3]@neutral[physical][:3,:3].T).ravel().tolist()
 return {'schema':'POSEDOLL-O22-UE/1','status':'VALID_MEASUREMENT','basis':'RH_X_FORWARD_Y_LEFT_Z_UP',
  'raw_count':46,'device_profile_sha256':digest(profile),'calibration_sha256':digest(cal),
  'capture_id':str(raw[0]['capture_id']),'hardware_capture_eligible':verified['hardware_capture_eligible'],
  'source_kind':'MEASURED_QUALIFIED' if verified['hardware_capture_eligible'] else 'SYNTHETIC_OR_UNQUALIFIED',
  'semantic_rotations':rotations,'joint_angles_deg':verified['joint_angles_deg'],
  'boundary_uncertainty':verified['boundary_uncertainty'],'source_measurement':m,
  'root_provenance':'FIXED_REFERENCE_NOT_MEASURED','contact_correction':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--profile',required=True);p.add_argument('--record',required=True);p.add_argument('--output',required=True);p.add_argument('--allow-synthetic-for-testing',action='store_true');a=p.parse_args()
 read=lambda x:json.loads(Path(x).read_text(encoding='utf-8-sig'))
 out=export(read(a.profile),read(a.record),a.allow_synthetic_for_testing)
 Path(a.output).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(out['source_kind'])
