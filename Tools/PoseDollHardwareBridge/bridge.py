"""A request-bound raw acquisition to PDS1. Hardware mode requires an actual serial port.
Diagnostic partial rigs never publish a FullBody PDS1 hello. Test transports explicitly
label simulated provenance. Stability and capture remain in UE.
"""
from pathlib import Path
import argparse,collections,json,math,socket,sys,time,uuid
import pdg5

class BridgeCore:
    def __init__(self,profile,info,source_kind='simulated'):
        if info['type']!=pdg5.HELLO or not info['device'] or not info['boot'] or len(info['source_boot'])!=6 or any(not b for b in info['source_boot']) or info['physical_mask']!=pdg5.FULL_MASK:
            raise ValueError('Partial bench: diagnostic only; 41 physical channels required')
        layout=json.loads(Path(__file__).with_name('layout.json').read_text(encoding='utf-8'))
        if profile.order!=layout['axis_order'] or any(abs(profile.cal[a]['raw_period_rad']-math.tau)>1e-9 for a in profile.order[3:]):
            raise ValueError('PDG5/1 AS5048 layout/period mismatch')
        if source_kind not in ('simulated','hardware'):raise ValueError('Invalid provenance')
        self.info=info;self.profile=profile;self.active=None;self.seen=set();self.retired=collections.OrderedDict();self.dropped=0
        self.h=dict(protocol='PDS1/1',type='hello',device_id='G0-'+str(info['device']),gateway_boot=str(info['boot']),source_boots=[str(b) for b in info['source_boot']],profile_sha256=profile.profile_hash,calibration_sha256=profile.calibration_hash,axis_order=profile.order,source_kind=source_kind)
        self.req=None;self.last=0;self.last_end=0;self.wall=0
    def _retire(self,now):
        if self.active is not None:
            self.retired[self.active]=now+30
            while len(self.retired)>32:self.retired.popitem(last=False)
        self.active=None
    def command(self,p,now):
        from posedoll_sim.static_protocol import validate_command
        validate_command(p,self.h);cid=uuid.UUID(p['capture_id']).bytes
        kind=p['type']
        if kind=='request':
            if cid==self.active:return None # Never restart measurement clock on duplicate UI command.
            if cid in self.seen or len(self.seen)>=4096:raise ValueError('PDS1 reused/exhausted capture')
            self._retire(now);self.seen.add(cid);self.active=cid;self.wall=now;self.req=None;self.last=0;self.last_end=0
        else:
            if cid!=self.active:return None
            self._retire(now)
        return pdg5.encode(dict(type={'request':pdg5.REQUEST,'cancel':pdg5.CANCEL,'ack':pdg5.STOP}[kind],device=self.info['device'],boot=self.info['boot'],capture=cid))
    def reply(self,m,now):
        if m['device']!=self.info['device'] or m['boot']!=self.info['boot'] or m['source_boot']!=self.info['source_boot'] or m['physical_mask']!=pdg5.FULL_MASK:
            raise ValueError('PDG5 changed boot/missing physical region')
        if m['type'] not in (pdg5.ACCEPTED,pdg5.SCAN):raise ValueError('PDG5 error/unexpected reply')
        if m['type']==pdg5.ACCEPTED and m['scan']:
            raise ValueError('PDG5 malformed ACK')
        if m['type']==pdg5.SCAN:
            if not m['scan'] or not m['request_us']<=m['start_us']<m['end_us'] or m['end_us']-m['start_us']>100000 or m['words'][:3]!=[0x4000]*3 or any(w>=0x4000 for w in m['words'][3:]):
                raise ValueError('PDG5 incomplete/faulty scan')
        self.retired=collections.OrderedDict((k,v) for k,v in self.retired.items() if now<v)
        if m['capture']!=self.active:
            if m['capture'] in self.retired:self.dropped+=1;return None
            raise ValueError('PDG5 unknown capture')
        if not 0<=now-self.wall<=3:raise ValueError('PDG5 request deadline')
        base={k:self.h[k] for k in ('protocol','device_id','gateway_boot','profile_sha256','calibration_sha256','source_boots')}
        base.update(capture_id=str(uuid.UUID(bytes=m['capture'])),request_start_us=str(m['request_us']))
        if m['type']==pdg5.ACCEPTED:
            if m['scan'] or (self.req is not None and self.req!=m['request_us']):raise ValueError('PDG5 conflicting ACK')
            self.req=m['request_us'];return dict(base,type='accepted')
        if self.req is None or m['request_us']!=self.req or m['scan']!=self.last+1 or m['start_us']<self.last_end or m['end_us']-self.req>(now-self.wall)*1e6+5000:raise ValueError('PDG5 unbound/old/future scan')
        self.last=m['scan'];self.last_end=m['end_us']
        return dict(base,type='scan',scan_id=str(m['scan']),start_us=str(m['start_us']),end_us=str(m['end_us']),duration_us=m['end_us']-m['start_us'],raw_angles_rad=[None]*3+[w*math.tau/16384 for w in m['words'][3:]],axis_status=['fixed']*3+['valid']*41)

def run():
    ap=argparse.ArgumentParser();ap.add_argument('--ue-root',type=Path,required=True);ap.add_argument('--serial',required=True);ap.add_argument('--diagnostic',action='store_true');ap.add_argument('--log',type=Path,required=True);ap.add_argument('--port',type=int,default=39178);a=ap.parse_args()
    sys.path.insert(0,str(a.ue_root/'Tools/PoseDollSimulator/src'))
    from posedoll_sim.core import DeviceProfile,FrameDecoder,encode
    from posedoll_sim.static_protocol import envelope,unwrap
    import serial
    profile=DeviceProfile(a.ue_root/'Shared');a.log.parent.mkdir(parents=True,exist_ok=True)
    with serial.Serial(a.serial,115200,timeout=.01,write_timeout=.2) as transport,a.log.open('x',encoding='utf-8') as log:
        def record(direction,raw):log.write(json.dumps(dict(wall_ns=time.monotonic_ns(),direction=direction,hex=raw.hex(),source_kind='hardware' if direction!='meta' else 'diagnostic'))+'\n');log.flush()
        def send(raw):record('command',raw);n=transport.write(raw);assert n==len(raw),'serial short write'
        stream=pdg5.Stream();send(pdg5.encode(dict(type=pdg5.PROBE)));deadline=time.monotonic()+2;info=None
        while info is None:
            now=time.monotonic()
            if now>deadline:raise TimeoutError('No PDG5 gateway hello')
            raw=transport.read(min(4096,max(1,transport.in_waiting)))
            if raw:record('reply',raw)
            for m in stream.feed(raw,now):
                if m['type']!=pdg5.HELLO:raise ValueError('Unexpected discovery frame')
                info=m
        if a.diagnostic:
            send(pdg5.encode(dict(type=pdg5.REQUEST,device=info['device'],boot=info['boot'],capture=uuid.uuid4().bytes)))
            deadline=time.monotonic()+3
            while time.monotonic()<deadline:
                raw=transport.read(min(4096,max(1,transport.in_waiting)))
                if raw:record('diagnostic',raw)
                for m in stream.feed(raw,time.monotonic()):
                    if m['type'] in (pdg5.SCAN,pdg5.ERROR):print(json.dumps({**m,'capture':m['capture'].hex(),'scope':'diagnostic only; not a PDS1 full-body pose'}));return
            raise TimeoutError('Diagnostic scan timeout')
        core=BridgeCore(profile,info,'hardware')
        with socket.socket() as listener:
            listener.bind(('127.0.0.1',a.port));listener.listen(1)
            print('HardwareBridge listening on loopback',a.port)
            with listener.accept()[0] as client:
                client.settimeout(.01);client.sendall(encode(envelope(core.h)));frames=FrameDecoder();welcomed=False;welcome_deadline=time.monotonic()+3
                try:
                    while True:
                        now=time.monotonic()
                        if not welcomed and now>welcome_deadline:raise TimeoutError('PDS1 welcome timeout')
                        try:data=client.recv(65536)
                        except socket.timeout:data=None
                        if data==b'':break
                        for p in frames.feed(data or b''):
                            if not welcomed:
                                if p.get('type')!='welcome' or p.get('protocol')!='PDS1/1' or p.get('session_id')!=core.h['gateway_boot'] or p.get('accepted') is not True:raise ValueError('Invalid PDS1 welcome')
                                welcomed=True;continue
                            raw=core.command(unwrap(p),time.monotonic())
                            if raw:send(raw)
                        raw=transport.read(min(4096,transport.in_waiting))
                        if raw:record('reply',raw)
                        for m in stream.feed(raw,time.monotonic()):
                            response=core.reply(m,time.monotonic())
                            if response:client.sendall(encode(envelope(response)))
                        if core.active is not None and time.monotonic()-core.wall>3:raise TimeoutError('Hardware acquisition deadline')
                finally:
                    if core.active is not None:send(pdg5.encode(dict(type=pdg5.CANCEL,device=info['device'],boot=info['boot'],capture=core.active)))
if __name__=='__main__':run()
