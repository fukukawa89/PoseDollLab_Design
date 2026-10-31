import copy,hashlib,json,math,os,sys,uuid
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[3]
UE=Path(os.environ.get('POSEDOLL_UE_ROOT','E:/UnrealProjects/DollSimulation'))
sys.path[:0]=[str(ROOT/'Tools/PoseDollHardwareBridge'),str(UE/'Tools/PoseDollSimulator/src')]
from posedoll_sim.core import DeviceProfile
from posedoll_sim.static_protocol import StaticWindow,command
from o15_bridge import BridgeCore,read_calibration,REQUIRED_PHYSICAL_TESTS
import pdg15
G=ROOT/'Hardware/PoseDoll44/generated/revO15/runs/o15_20260929_r1'

def fixture_data():
 mapping=json.loads((G/'raw46_mapping_candidate.json').read_text());wiring=json.loads((G/'raw46_wiring_candidate.json').read_text())
 # Synthetic fixture: exact neutral geometry falls at integer zero sensor code.
 q={rid:angle for g in mapping['groups'] for rid,angle in zip(g['raw_ids'],g['angles_deg'])}
 cal=dict(schema='O15-RAW-CALIBRATION/1',source_kind='simulated',body_device='123',raw={rid:dict(sign=1,zero_deg=-a) for rid,a in q.items()})
 info=pdg15.decode(pdg15.encode(dict(type=pdg15.HELLO,device=123,gateway_boot=456,body_boot=789)))
 return mapping,wiring,cal,info

def scenario():
 p=DeviceProfile(UE/'Shared');m,w,c,info=fixture_data();core=BridgeCore(p,info,m,w,c)
 cid=str(uuid.uuid4());raw=core.command(command(core.h,cid),100)
 assert pdg15.decode(raw)['type']==pdg15.REQUEST
 ack=dict(info,type=pdg15.ACCEPTED,capture=uuid.UUID(cid).bytes,request_us=1000000,scan=0,start_us=0,end_us=0)
 return p,core,cid,ack

def scan(ack,i=1):
 return dict(ack,type=pdg15.SCAN,scan=i,token=i,start_us=1001000+(i-1)*100000,end_us=1061000+(i-1)*100000,words=[0]*46,valid_mask=pdg15.MASK)

def test_native_golden_cross_language():
 wire=(ROOT/'.local/revO15-core/golden.bin').read_bytes();m=pdg15.decode(wire)
 assert m['device']==0x010203040506 and m['words']==[37*i for i in range(46)] and m['body_boot']==9
 assert pdg15.encode(m)==wire
 for bit in range(len(wire)*8):
  bad=bytearray(wire);bad[bit//8]^=1<<(bit%8)
  with pytest.raises(ValueError):pdg15.decode(bad)
 for n in range(len(wire)):
  with pytest.raises(ValueError):pdg15.decode(wire[:n])

def test_static_snapshot_and_inverse_profile_calibration():
 p,c,cid,ack=scenario();w=StaticWindow(p,c.h,cid,100);w.push(c.reply(ack,100.001),100.001)
 for i in range(1,8):
  m=scan(ack,i);now=100+(m['end_us']-1000000)/1e6;out=c.reply(m,now);w.push(out,now)
  assert out['axis_status']==['fixed']*3+['valid']*41
  # Profile inversion must return zero semantic angles, not the profile's pi offset.
  for aid,raw in zip(p.order[3:],out['raw_angles_rad'][3:]):
   z=p.cal[aid];a=(raw-z['zero_raw_rad']+math.pi)%math.tau-math.pi
   assert abs(a*z['sign']*z['joint_rad_per_sensor_rad'])<1e-7
 assert w.state=='SnapshotReady' and c.h['source_boots']==['789']*6
 c.command(command(c.h,cid,'ack'),100.7)
 assert c.reply(scan(ack,7),100.8) is None

@pytest.mark.parametrize('which',['device','gateway_boot','body_boot','scan','token','request','start','duration','future','deadline','unknown'])
def test_transaction_failures(which):
 p,c,cid,ack=scenario();c.reply(ack,100.001);m=scan(ack);now=100.061
 if which in ('device','gateway_boot','body_boot'):m[which]+=1
 if which=='scan':m['scan']=2
 if which=='token':m['token']=0
 if which=='request':m['request_us']-=1
 if which=='start':m['start_us']=m['request_us']-1
 if which=='duration':m['end_us']=m['start_us']+100001
 if which=='future':now=100.001
 if which=='deadline':now=104
 if which=='unknown':m['capture']=uuid.uuid4().bytes
 with pytest.raises(ValueError):c.reply(m,now)
 assert c.last==0

@pytest.mark.parametrize('channel',range(46))
def test_each_missing_and_fault_channel_rejects_pose(channel):
 for invalid in (0x8000,0x8004,0xffff):
  p,c,cid,ack=scenario();c.reply(ack,100.001);m=scan(ack);m['words'][channel]=invalid;m['valid_mask']&=~(1<<channel)
  with pytest.raises(ValueError):c.reply(m,100.061)
  assert c.last==0

def test_cancel_duplicate_and_stale_replies():
 p,c,cid,ack=scenario();assert c.command(command(c.h,cid),101) is None;assert c.wall==100
 c.command(command(c.h,cid,'cancel'),100.01)
 with pytest.raises(ValueError):c.command(command(c.h,cid),100.02)
 new=str(uuid.uuid4());c.command(command(c.h,new),100.03)
 assert c.reply(ack,100.04) is None and c.reply(scan(ack),100.1) is None
 bad=scan(ack);bad['words'][7]=pdg15.FAULT;bad['valid_mask']&=~128
 with pytest.raises(ValueError):c.reply(bad,100.1)
 assert c.active==uuid.UUID(new).bytes

def test_reorder_overlapping_and_token_replay():
 for kind in ('sequence','time','token'):
  p,c,cid,ack=scenario();c.reply(ack,100.001);c.reply(scan(ack),100.061);m=scan(ack,2)
  if kind=='sequence':m['scan']=1
  if kind=='time':m['start_us']=1060999
  if kind=='token':m['token']=1
  with pytest.raises(ValueError):c.reply(m,100.161)

def test_unqualified_calibration_and_axis_layout():
 p,c,cid,ack=scenario();m,w,cal,info=fixture_data();cal['source_kind']='hardware'
 with pytest.raises(ValueError,match='qualification'):BridgeCore(p,info,m,w,cal,'hardware')
 cal['source_kind']='simulated';cal['raw'][w['raw_order'][0]]['zero_deg']=float('nan')
 with pytest.raises(ValueError,match='calibration'):BridgeCore(p,info,m,w,cal)
 m,w,cal,info=fixture_data();w['raw_order'][1]=w['raw_order'][0]
 with pytest.raises(ValueError):BridgeCore(p,info,m,w,cal)
 m,w,cal,info=fixture_data();p.order=p.order.copy();p.order[3],p.order[4]=p.order[4],p.order[3]
 with pytest.raises(ValueError,match='layout'):BridgeCore(p,info,m,w,cal)

def test_calibration_digest_and_source_binding(tmp_path):
 m,w,c,info=fixture_data();mb=json.dumps(m).encode();wb=json.dumps(w).encode()
 c.update(mapping_sha256=hashlib.sha256(mb).hexdigest(),wiring_sha256=hashlib.sha256(wb).hexdigest());p=tmp_path/'cal.json';p.write_text(json.dumps(c))
 read_calibration(p,mb,wb,123,'simulated')
 for altered in ((mb+b' ',wb,123,'simulated'),(mb,wb,124,'simulated'),(mb,wb,123,'hardware')):
  with pytest.raises(ValueError):read_calibration(p,*altered)

def test_stream_chunks_and_body_clock_domain():
 p,c,cid,ack=scenario();s=pdg15.Stream();out=[]
 for byte in pdg15.encode(ack)+pdg15.encode(scan(ack)):out.extend(s.feed(bytes([byte])))
 assert [m['type'] for m in out]==[pdg15.ACCEPTED,pdg15.SCAN]
 body=scan(ack);body.update(type=pdg15.BODY_SCAN,start_us=5,end_us=60005)
 assert pdg15.decode(pdg15.encode(body))['start_us']==5
 with pytest.raises(ValueError):c.reply(body,100.061)
 with pytest.raises(ValueError):pdg15.Stream().feed(b'x'*192)
 with pytest.raises(ValueError):pdg15.Stream().feed(b'x'*(192*64+1))
