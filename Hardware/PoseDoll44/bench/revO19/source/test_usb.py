"""Host USB decoding and measurement-chain regression with independent packets."""
import copy,json,struct,unittest,zlib
from pathlib import Path
import numpy as np
from usb_capture import decode,measurement_scans,SCAN,command,PROBE
from device import capture_window,forward,digest
HERE=Path(__file__).resolve().parent
BASE=HERE.parent if (HERE.parent/'profiles/device_profile.json').exists() else HERE.parents[1]/'bench/revO17'
P=json.loads((BASE/'profiles/device_profile.json').read_text(encoding='utf-8-sig'))
CAP='1234567890abcdef1234567890abcdef'

def packet(index=1,words=None):
 b=bytearray(192);b[:6]=b'P17R\x01\x04';struct.pack_into('<QQQ',b,8,123,456,456);b[32:48]=bytes.fromhex(CAP)
 struct.pack_into('<IIQQQ',b,48,index,index,500000,1000000+(index-1)*100000,1045000+(index-1)*100000)
 b[80:86]=bytes([6,4,10,10,8,8]);struct.pack_into('<Q',b,88,(1<<46)-1);struct.pack_into('<46H',b,96,*(words or [8192]*46));struct.pack_into('<I',b,188,zlib.crc32(b[:188]));return bytes(b)

def crc(b):
 b=bytearray(b);struct.pack_into('<I',b,188,zlib.crc32(b[:188]));return bytes(b)

class USBTests(unittest.TestCase):
 def test_c_compiler_fixture(self):
  candidate=HERE/'codec_fixture.bin'
  if not candidate.exists():candidate=HERE.parents[1]/'generated/revO17/codec_fixture.bin'
  f=decode(candidate.read_bytes());self.assertEqual(f['words'][45],1665);self.assertEqual(f['type'],SCAN)
 def test_all_packet_bit_flips_and_truncations(self):
  raw=packet()
  for bit in range(1536):
   bad=bytearray(raw);bad[bit//8]^=1<<(bit%8)
   with self.assertRaises(ValueError):decode(bytes(bad))
  for n in range(192):
   with self.assertRaises(ValueError):decode(raw[:n])
 def test_invalid_clock_and_mask_with_valid_crc(self):
  for offset,val in [(72,1060001),(72,1000000),(64,499999),(88,0),(88,1<<46)]:
   bad=bytearray(packet());struct.pack_into('<Q',bad,offset,val)
   with self.assertRaises(ValueError):decode(crc(bad))
 def test_record_to_35_body_frames_without_pose_change(self):
  frames=[decode(packet(i)) for i in range(1,7)];rows=measurement_scans(P,frames,CAP)
  cal={'status':'SYNTHETIC','device_id':'123','profile_sha256':digest(P),'axes':{k:{'sensor_zero_deg':180.,'sign':1,'reference_joint_deg':v} for k,v in P['neutral_raw_deg'].items()},'physical_tests':{}}
  result=capture_window(P,cal,rows,expected_capture_id=int(CAP,16),evaluation_time_ms=1555)
  self.assertEqual(result['status'],'VALID_MEASUREMENT');self.assertFalse(result['hardware_capture_eligible']);self.assertEqual(len(result['frames']),35)
  for k,v in forward(P,P['neutral_raw_deg']).items():np.testing.assert_allclose(v,result['frames'][k]['matrix_mm'],atol=1e-10)
  stale=capture_window(P,cal,rows,expected_capture_id=int(CAP,16),evaluation_time_ms=2000);self.assertEqual(stale['status'],'REJECTED')
 def test_boot_capture_replay_order_and_faults(self):
  frames=[decode(packet(i)) for i in range(1,7)]
  for field,value in [('device',124),('body_boot',457),('transport_boot',457),('capture','00'*16),('scan',1),('token',1),('valid_mask',0),('request_us',1),('type',7)]:
   bad=copy.deepcopy(frames);bad[3][field]=value
   with self.assertRaises(ValueError):measurement_scans(P,bad,CAP)
 def test_request_packet_has_new_magic(self):
  self.assertEqual(decode(command(PROBE))['type'],PROBE)
  b=bytearray(packet());b[:4]=b'P15R'
  with self.assertRaises(ValueError):decode(crc(b))

if __name__=='__main__':unittest.main(verbosity=2)
