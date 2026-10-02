"""Synthetic PDG5 bytes -> production BridgeCore -> real UE socket; never hardware."""
from pathlib import Path
import argparse,math,select,socket,sys,time
ap=argparse.ArgumentParser();ap.add_argument('--ue-root',type=Path,required=True);ap.add_argument('--case',required=True);ap.add_argument('--ready',type=Path,required=True);a=ap.parse_args()
sys.path.insert(0,str(a.ue_root/'Tools/PoseDollSimulator/src'))
from posedoll_sim.core import DeviceProfile,FrameDecoder,encode
from posedoll_sim.static_protocol import envelope,unwrap
from bridge import BridgeCore
import pdg5
p=DeviceProfile(a.ue_root/'Shared');info=dict(type=pdg5.HELLO,device=123,boot=456,source_boot=[1001,1002,1003,1004,1005,1006],physical_mask=pdg5.FULL_MASK)
core=BridgeCore(p,pdg5.decode(pdg5.encode(info)),'simulated');raw,status=p.encode_angles({aid:sum(p.axes[aid]['limits_rad'])/2 for aid in p.order})
words=[0x4000]*3+[round(x*16384/math.tau)%16384 for x in raw[3:]]
listener=socket.socket();listener.bind(('127.0.0.1',39178));listener.listen(1);listener.settimeout(10);a.ready.write_text(a.case)
wire_parser=pdg5.Stream()
def forward(c,m):
 wire=bytearray(pdg5.encode(m))
 if a.case=='crc' and m['type']==pdg5.SCAN:wire[123]^=1
 for i in range(0,len(wire),17):
  for decoded in wire_parser.feed(wire[i:i+17],time.monotonic()):
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
     usb=pdg5.decode(command)
     if usb['type']!=pdg5.REQUEST:active=None;continue
     active=usb['capture'];req=time.monotonic_ns()//1000;sid=0;due=time.monotonic()
     forward(c,{**info,'type':pdg5.ACCEPTED,'capture':active,'request_us':req})
   if active and time.monotonic()>=due:
    sid+=1;start=time.monotonic_ns()//1000;time.sleep(.002);end=time.monotonic_ns()//1000
    m={**info,'type':pdg5.SCAN,'capture':active,'scan':sid,'request_us':req,'start_us':start,'end_us':end,'words':words.copy()}
    if a.case=='missing':m['words'][17]=0xffff
    if a.case=='boot':m['source_boot']=[9999]+info['source_boot'][1:]
    forward(c,m);due+=.1
except ValueError as e:print('Expected strict bridge rejection:',e,flush=True)
except (ConnectionError,OSError):pass
finally:listener.close()
