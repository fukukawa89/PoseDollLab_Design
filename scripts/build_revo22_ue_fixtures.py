"""Exercise actual P21R encoding/decoding before synthetic UE fixtures."""
from pathlib import Path
import sys,json,struct,zlib,copy
R=Path(__file__).resolve().parents[1];B=R/'Hardware/PoseDoll44/bench/revO22'
sys.path.insert(0,str(B/'source'))
from usb_capture import command,decode,measurement_scans,SCAN,MASK
from mt6701 import crc6
from measurement import capture_window
from device import digest
from ue_export import export
def main():
 p=json.loads((B/'profiles/device_profile.json').read_text(encoding='utf-8-sig'))
 default=json.loads((B/'profiles/default_pose.json').read_text(encoding='utf-8-sig'))['raw_deg']
 poses={'a_stand':default,'left_elbow':dict(default,**{'elbow_l.flex/r0':60}),
        'asymmetric':dict(default,**{'waist/r0':12,'chest/r1':8,'head/r0':20,'hand_r.flex/r0':25,'calf_l.flex/r0':35,'foot_l/r0':10,'ball_r.flex/r0':20}),
        'right_forearm':dict(default,**{'forearm_r.twist/r0':40})}
 for name,q in poses.items():
  identity={'device':2201,'transport_boot':22,'body_boot':22};cap='00000000000000000000000000000022';frames=[];packets=[]
  cal={'status':'SYNTHETIC','device_id':'2201','profile_sha256':digest(p),'axes':{k:{'sensor_zero_deg':180.,'reference_joint_deg':p['neutral_raw_deg'][k],'sign':1} for k in p['raw_order']},
       'physical_tests':{k:False for k in p['required_physical_measurement_tests']}}
  for scan in range(1,7):
   data=bytearray(command(SCAN,identity,cap));start=990000+(scan-1)*100000;end=start+10000
   struct.pack_into('<IIQQQ',data,48,scan,scan,900000,start,end);struct.pack_into('<Q',data,88,MASK);struct.pack_into('<Q',data,236,MASK)
   for i,k in enumerate(p['raw_order']):
    counts=round(((180+q[k]-p['neutral_raw_deg'][k])%360)*16384/360)%16384
    word=(counts<<10)|crc6(counts<<4);data[96+3*i:99+3*i]=word.to_bytes(3,'little')
   struct.pack_into('<I',data,244,zlib.crc32(data[:244]));raw=bytes(data);packets.append(raw.hex());frames.append(decode(raw))
  scans=measurement_scans(p,frames,cap);m=capture_window(p,cal,scans,expected_capture_id=int(cap,16),evaluation_time_ms=1510)
  assert m['status']=='VALID_MEASUREMENT',m
  record={'schema':'POSEDOLL-O22-USB-RECORD/1','status':m['status'],'measurement':m,'packets_hex':packets,'source_kind':'SYNTHETIC_WIRE_FIXTURE_NOT_HARDWARE'}
  (B/'ue'/f'{name}.record.json').write_text(json.dumps(record,indent=2)+'\n')
  (B/'ue'/f'{name}.payload.json').write_text(json.dumps(export(p,record,True),indent=2)+'\n')
 print('4 synthetic USB -> calibrated FK -> UE payload fixtures')
if __name__=='__main__':main()
