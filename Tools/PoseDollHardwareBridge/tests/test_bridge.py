import copy,json,math,os,sys,uuid
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[3]
UE=Path(os.environ.get('POSEDOLL_UE_ROOT','E:/UnrealProjects/DollSimulation'))
sys.path[:0]=[str(ROOT/'Tools/PoseDollHardwareBridge'),str(UE/'Tools/PoseDollSimulator/src')]
from posedoll_sim.core import DeviceProfile
from posedoll_sim.static_protocol import StaticWindow,command
from bridge import BridgeCore
import pdg5

def scenario():
 p=DeviceProfile(UE/'Shared');info=dict(type=pdg5.HELLO,device=1,boot=2,source_boot=[11,12,13,14,15,16],physical_mask=pdg5.FULL_MASK,words=[0x4000]*3+[0xffff]*41)
 core=BridgeCore(p,info,'simulated');cid=str(uuid.uuid4());raw=core.command(command(core.h,cid),100)
 decoded=pdg5.decode(raw);assert decoded['type']==pdg5.REQUEST and str(uuid.UUID(bytes=decoded['capture']))==cid
 ack={**info,'type':pdg5.ACCEPTED,'capture':uuid.UUID(cid).bytes,'request_us':1000000,'scan':0,'start_us':0,'end_us':0}
 return p,core,cid,ack

def scan(p,ack,i=1):
 q={aid:(p.axes[aid]['limits_rad'][0]+p.axes[aid]['limits_rad'][1])*.5 for aid in p.order}
 raw,status=p.encode_angles(q);words=[0x4000]*3+[round(x*16384/math.tau)%16384 for x in raw[3:]]
 return {**ack,'type':pdg5.SCAN,'scan':i,'start_us':1001000+(i-1)*100000,'end_us':1021000+(i-1)*100000,'words':words}

def test_native_c_golden():
 b=Path(os.environ.get('PD5_GOLDEN',Path(__file__).with_name('pdg5_golden.bin'))).read_bytes();m=pdg5.decode(b)
 assert m['boot']==456 and m['device']==123 and m['physical_mask']==pdg5.FULL_MASK and m['words'][3]==100
 assert pdg5.encode(m)==b
 # Compare C aggregation with the independently maintained physical connector map.
 network=json.loads((ROOT/'Hardware/PoseDoll44/mechanical_manifest/network_revO.json').read_text(encoding='utf-8'))
 layout=json.loads((ROOT/'Tools/PoseDollHardwareBridge/layout.json').read_text(encoding='utf-8'))
 assert layout['axis_order']==network['protocol_order']
 for node in network['nodes']:
  for port in node['ports']:
   index=network['protocol_order'].index(port['axis_id'])
   assert m['words'][index]==100+port['port']-1


def test_complete_scan_to_existing_stability_window():
 p,core,cid,ack=scenario();w=StaticWindow(p,core.h,cid,100);w.push(core.reply(pdg5.decode(pdg5.encode(ack)),100.001),100.001)
 for i in range(1,8):
  m=scan(p,ack,i);now=100+(m['end_us']-1000000)/1e6;out=core.reply(pdg5.decode(pdg5.encode(m)),now);w.push(out,now)
 assert w.state=='SnapshotReady' and w.final['scan_id']=='7' and core.h['source_kind']=='simulated'
 assert core.command(command(core.h,cid,'ack'),100.7)
 assert core.reply(pdg5.decode(pdg5.encode(scan(p,ack,7))),100.8) is None

@pytest.mark.parametrize('which', ['device','boot','source_boot','mask','missing','fault','root','scan','request','start','duration','future','deadline','crc','unknown'])
def test_faults_do_not_create_pose(which):
 p,core,cid,ack=scenario();core.reply(pdg5.decode(pdg5.encode(ack)),100.001);m=scan(p,ack);now=100.021
 if which=='device':m['device']=9
 if which=='boot':m['boot']=9
 if which=='source_boot':m['source_boot']=[9]*6
 if which=='mask':m['physical_mask']&=~8
 if which=='missing':m['words'][5]=0xffff
 if which=='fault':m['words'][5]=0x8004
 if which=='root':m['words'][0]=0
 if which=='scan':m['scan']=2
 if which=='request':m['request_us']-=1
 if which=='start':m['start_us']=m['request_us']-1
 if which=='duration':m['end_us']=m['start_us']+100001
 if which=='future':now=100.001
 if which=='deadline':now=104
 if which=='unknown':m['capture']=uuid.uuid4().bytes
 b=bytearray(pdg5.encode(m))
 if which=='crc':b[130]^=1
 with pytest.raises(ValueError):core.reply(pdg5.decode(b),now)
 assert core.last==0

@pytest.mark.parametrize('ports',[1,9,40])
def test_partial_bench_never_full_hardware(ports):
 p,core,cid,ack=scenario();info=copy.deepcopy(core.info);info['physical_mask']=((1<<ports)-1)<<3
 with pytest.raises(ValueError,match='diagnostic only'):BridgeCore(p,info,'hardware')

def test_cancel_reorder_identity_checked_before_retire():
 p,core,cid,ack=scenario();core.command(command(core.h,cid,'cancel'),100.002)
 new=str(uuid.uuid4());core.command(command(core.h,new),100.003)
 assert core.reply(pdg5.decode(pdg5.encode(ack)),100.004) is None
 assert core.reply(pdg5.decode(pdg5.encode(scan(p,ack))),100.025) is None
 bad=scan(p,ack);bad['words'][7]=0xffff
 with pytest.raises(ValueError):core.reply(pdg5.decode(pdg5.encode(bad)),100.03)
 assert core.active==uuid.UUID(new).bytes and core.dropped==2

def test_stream_split_concat_and_timeout():
 p,core,cid,ack=scenario();a=pdg5.encode(ack);b=pdg5.encode(scan(p,ack));s=pdg5.Stream();out=[]
 for byte in a+b:out.extend(s.feed(bytes([byte]),100))
 assert [m['type'] for m in out]==[pdg5.ACCEPTED,pdg5.SCAN]
 s=pdg5.Stream();assert not s.feed(a[:50],100)
 with pytest.raises(ValueError):s.feed(a[50:],100.6)
 with pytest.raises(ValueError):pdg5.Stream().feed(b'x'*220,100)
 with pytest.raises(ValueError):pdg5.Stream().feed(a*33,100)

def test_duplicate_request_cannot_retime_or_reexecute():
 p,core,cid,ack=scenario();assert core.command(command(core.h,cid),101) is None;assert core.wall==100
 core.command(command(core.h,cid,'cancel'),101)
 with pytest.raises(ValueError):core.command(command(core.h,cid),102)


def test_wrong_measured_axis_order_is_rejected():
 p,core,cid,ack=scenario();p.order=p.order.copy();p.order[3],p.order[4]=p.order[4],p.order[3]
 with pytest.raises(ValueError,match="layout/period mismatch"):BridgeCore(p,core.info)
