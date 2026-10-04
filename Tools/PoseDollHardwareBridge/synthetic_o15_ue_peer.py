"""Synthetic PDG15 bytes -> production BridgeCore -> real UE socket; never hardware."""
from pathlib import Path
import argparse,math,select,socket,sys,time
ap=argparse.ArgumentParser();ap.add_argument('--ue-root',type=Path,required=True);ap.add_argument('--case',required=True);ap.add_argument('--ready',type=Path,required=True);a=ap.parse_args()
sys.path.insert(0,str(a.ue_root/'Tools/PoseDollSimulator/src'))
from posedoll_sim.core import DeviceProfile,FrameDecoder,encode
from posedoll_sim.static_protocol import envelope,unwrap
from o15_bridge import BridgeCore
import pdg15
import json
p=DeviceProfile(a.ue_root/'Shared');repo=Path(__file__).resolve().parents[2];g=repo/'Hardware/PoseDoll44/generated/revO15/runs/o15_20260929_r1'
mapping=json.loads((g/'raw46_mapping_candidate.json').read_text());wiring=json.loads((g/'raw46_wiring_candidate.json').read_text());q={rid:angle for group in mapping['groups'] for rid,angle in zip(group['raw_ids'],group['angles_deg'])}
cal=dict(source_kind='simulated',body_device='123',raw={rid:dict(sign=1,zero_deg=-v) for rid,v in q.items()})
info=dict(type=pdg15.HELLO,device=123,gateway_boot=456,body_boot=789)
core=BridgeCore(p,pdg15.decode(pdg15.encode(info)),mapping,wiring,cal,'simulated');words=[0]*46
listener=socket.socket();listener.bind(('127.0.0.1',39178));listener.listen(1);listener.settimeout(10);a.ready.write_text(a.case)
wire_parser=pdg15.Stream()
def forward(c,m):
 wire=bytearray(pdg15.encode(m))
 if a.case=='crc' and m['type']==pdg15.SCAN:wire[123]^=1
 for i in range(0,len(wire),17):
  for decoded in wire_parser.feed(wire[i:i+17]):
   reply=core.reply(decoded,time.monotonic())
   if reply:c.sendall(encode(envelope(reply)))
try:
 with listener.accept()[0] as c:
  c.sendall(encode(envelope(core.h)));dec=FrameDecoder();active=None;sid=0;req=0;due=0
  while True:
   ready,_,_=select.select([c],[],[],.002)
   if ready:
    data=c.recv(65536)
    if not data:break
    for packet in dec.feed(data):
     if packet.get('type')=='welcome':continue
     command=core.command(unwrap(packet),time.monotonic())
     if command is None:continue
     usb=pdg15.decode(command)
     if usb['type']!=pdg15.REQUEST:active=None;continue
     active=usb['capture'];req=time.monotonic_ns()//1000;sid=0;due=time.monotonic()
     forward(c,{**info,'type':pdg15.ACCEPTED,'capture':active,'request_us':req})
   if active and time.monotonic()>=due:
    sid+=1;start=time.monotonic_ns()//1000;time.sleep(.002);end=time.monotonic_ns()//1000
    m={**info,'type':pdg15.SCAN,'capture':active,'scan':sid,'token':sid,'valid_mask':pdg15.MASK,'request_us':req,'start_us':start,'end_us':end,'words':words.copy()}
    if a.case=='missing':m['words'][17]=0xffff;m['valid_mask']&=~(1<<17)
    if a.case=='boot':m['body_boot']=9999
    forward(c,m);due+=.1
except ValueError as e:print('Expected strict bridge rejection:',e,flush=True)
except (ConnectionError,OSError):pass
finally:listener.close()
