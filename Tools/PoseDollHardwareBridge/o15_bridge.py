"""Request-bound raw46 -> semantic41 -> existing PDS1 calibrated raw interface.
Hardware mode requires a completed physical binding/calibration record. Synthetic
records stay source_kind=simulated and cannot attest a real doll's qualification.
"""
from pathlib import Path
import argparse,collections,hashlib,json,math,socket,sys,time,uuid
import pdg15
from o15_kinematics import RawAngle,compose_frame,wrap

REQUIRED_PHYSICAL_TESTS=('individual_chain_binding','magnet_and_raw_calibration','disconnect_and_brownout','far_end_voltage_and_spi','complete_wired_motion')


def read_calibration(path,mapping_bytes,wiring_bytes,body_device,source_kind):
 raw=Path(path).read_bytes();c=json.loads(raw);mapping=json.loads(mapping_bytes);wiring=json.loads(wiring_bytes)
 if c.get('schema')!='O15-RAW-CALIBRATION/1' or c.get('body_device')!=str(body_device):raise ValueError('calibration identity')
 if c.get('mapping_sha256')!=hashlib.sha256(mapping_bytes).hexdigest() or c.get('wiring_sha256')!=hashlib.sha256(wiring_bytes).hexdigest():raise ValueError('calibration design changed')
 if c.get('source_kind')!=source_kind:raise ValueError('calibration provenance mismatch')
 if source_kind=='hardware' and not all(c.get('physical_tests',{}).get(k) is True for k in REQUIRED_PHYSICAL_TESTS):raise ValueError('physical qualification incomplete; use diagnostic acquisition')
 entries=c.get('raw',{})
 if set(entries)!=set(wiring['raw_order']) or len(entries)!=46:raise ValueError('calibration channel coverage')
 for r in entries.values():
  if type(r.get('sign')) is not int or r['sign'] not in (-1,1) or type(r.get('zero_deg')) not in (float,int) or not math.isfinite(r['zero_deg']):raise ValueError('calibration value')
 return c,hashlib.sha256(raw).hexdigest(),mapping,wiring


class BridgeCore:
 def __init__(self,profile,info,mapping,wiring,calibration,source_kind='simulated'):
  if info['type']!=pdg15.HELLO or not info['device'] or not info['gateway_boot'] or not info['body_boot'] or tuple(info['counts'])!=pdg15.COUNTS:raise ValueError('O15 discovery')
  if source_kind not in ('simulated','hardware') or calibration.get('source_kind')!=source_kind:raise ValueError('source provenance')
  if calibration.get('body_device')!=str(info['device']) or set(calibration.get('raw',{}))!=set(wiring['raw_order']) or len(wiring['raw_order'])!=46 or len(set(wiring['raw_order']))!=46:raise ValueError('physical binding')
  if source_kind=='hardware' and not all(calibration.get('physical_tests',{}).get(k) is True for k in REQUIRED_PHYSICAL_TESTS):raise ValueError('physical qualification incomplete')
  for r in calibration['raw'].values():
   if type(r.get('sign')) is not int or r['sign'] not in (-1,1) or type(r.get('zero_deg')) not in (int,float) or not math.isfinite(r['zero_deg']):raise ValueError('calibration value')
  if profile.order!=json.loads(Path(__file__).with_name('layout.json').read_text(encoding='utf-8'))['axis_order']:raise ValueError('semantic layout mismatch')
  expected={rid for g in mapping['groups'] for rid in g['raw_ids']}
  if set(wiring['raw_order'])!=expected or wiring['counts']!=list(pdg15.COUNTS):raise ValueError('wiring/mapping mismatch')
  # Validate full semantic layout before any connection; missing samples are expected here.
  compose_frame(mapping,{},profile.order,capture_id=0,boot_id='layout-validation')
  self.info=info;self.profile=profile;self.mapping=mapping;self.wiring=wiring;self.cal=calibration;self.active=None;self.seen=set();self.retired=collections.OrderedDict();self.dropped=0;self.previous={}
  self.h=dict(protocol='PDS1/1',type='hello',device_id='O15-'+str(info['device']),gateway_boot=str(info['gateway_boot']),source_boots=[str(info['body_boot'])]*6,profile_sha256=profile.profile_hash,calibration_sha256=profile.calibration_hash,axis_order=profile.order,source_kind=source_kind)
  # Six logical chains share a single measured body's boot/failure domain.
  self.req=None;self.last=0;self.last_end=0;self.wall=0;self.last_token=0
 def _retire(self,now):
  if self.active is not None:
   self.retired[self.active]=now+30
   while len(self.retired)>32:self.retired.popitem(last=False)
  self.active=None;self.previous={}
 def command(self,p,now):
  from posedoll_sim.static_protocol import validate_command
  validate_command(p,self.h);cid=uuid.UUID(p['capture_id']).bytes;kind=p['type']
  if kind=='request':
   if cid==self.active:return None
   if cid in self.seen or len(self.seen)>=4096:raise ValueError('reused/exhausted capture')
   self._retire(now);self.seen.add(cid);self.active=cid;self.wall=now;self.req=None;self.last=0;self.last_end=0;self.last_token=0
  else:
   if cid!=self.active:return None
   self._retire(now)
  return pdg15.encode(dict(type={'request':pdg15.REQUEST,'cancel':pdg15.CANCEL,'ack':pdg15.STOP}[kind],device=self.info['device'],gateway_boot=self.info['gateway_boot'],body_boot=self.info['body_boot'],capture=cid))
 def reply(self,m,now):
  # Validate before retired-transaction routing; corruption is never silently dropped.
  m=pdg15.decode(pdg15.encode(m))
  if any(m[k]!=self.info[k] for k in ('device','gateway_boot','body_boot')):raise ValueError('changed body/gateway identity')
  if m['type'] not in (pdg15.ACCEPTED,pdg15.SCAN):raise ValueError('unexpected acquisition reply')
  if m['type']==pdg15.ACCEPTED and m['scan']:raise ValueError('malformed accepted reply')
  if m['type']==pdg15.SCAN and (m['valid_mask']!=pdg15.MASK or m['end_us']-m['start_us']>100000):raise ValueError('missing/faulty or over-age raw46 scan')
  self.retired=collections.OrderedDict((k,v) for k,v in self.retired.items() if now<v)
  if m['capture']!=self.active:
   if m['capture'] in self.retired:self.dropped+=1;return None
   raise ValueError('unknown capture')
  if not 0<=now-self.wall<=3:raise ValueError('request deadline')
  base={k:self.h[k] for k in ('protocol','device_id','gateway_boot','profile_sha256','calibration_sha256','source_boots')};base.update(capture_id=str(uuid.UUID(bytes=m['capture'])),request_start_us=str(m['request_us']))
  if m['type']==pdg15.ACCEPTED:
   if self.req is not None and self.req!=m['request_us']:raise ValueError('conflicting accepted clock')
   self.req=m['request_us'];return dict(base,type='accepted')
  if self.req is None or m['request_us']!=self.req or m['scan']!=self.last+1 or m['token']<=self.last_token or m['start_us']<self.last_end or m['end_us']-self.req>(now-self.wall)*1e6+5000:raise ValueError('old, future, overlapping or unbound scan')
  samples={}
  for rid,word in zip(self.wiring['raw_order'],m['words']):
   c=self.cal['raw'][rid];angle=c['sign']*wrap(word*360/16384-c['zero_deg']);samples[rid]=RawAngle(angle,'valid',m['scan'],str(m['body_boot']),(m['end_us']-m['start_us'])/1000)
  semantic=compose_frame(self.mapping,samples,self.profile.order,capture_id=m['scan'],boot_id=str(m['body_boot']),max_age_ms=100,previous=self.previous)
  if semantic['status']!='valid':raise ValueError('raw composition/range failure')
  angles={a:math.radians(v['angle_deg']) for a,v in zip(self.profile.order,semantic['channels'])}
  # PDS1 expects the existing DeviceProfile calibrated-period raw values. This
  # inverse is essential; sending semantic angles directly would calibrate twice.
  raw,status=self.profile.encode_angles(angles)
  raw[:3]=[None]*3;status[:3]=['fixed']*3 # static FullBody fixes pelvis only, not body35 limb axes
  self.previous={g['group']:g['angles_deg'] for g in semantic['groups']};self.last=m['scan'];self.last_end=m['end_us'];self.last_token=m['token']
  return dict(base,type='scan',scan_id=str(m['scan']),start_us=str(m['start_us']),end_us=str(m['end_us']),duration_us=m['end_us']-m['start_us'],raw_angles_rad=raw,axis_status=status)


def run():
    ap=argparse.ArgumentParser();ap.add_argument('--ue-root',type=Path,required=True);ap.add_argument('--serial',required=True);ap.add_argument('--diagnostic',action='store_true');ap.add_argument('--mapping',type=Path,required=True);ap.add_argument('--wiring',type=Path,required=True);ap.add_argument('--raw-calibration',type=Path);ap.add_argument('--log',type=Path,required=True);ap.add_argument('--port',type=int,default=39178);a=ap.parse_args()
    sys.path.insert(0,str(a.ue_root/'Tools/PoseDollSimulator/src'))
    from posedoll_sim.core import DeviceProfile,FrameDecoder,encode
    from posedoll_sim.static_protocol import envelope,unwrap
    import serial
    profile=DeviceProfile(a.ue_root/'Shared');a.log.parent.mkdir(parents=True,exist_ok=True)
    with serial.Serial(a.serial,115200,timeout=.01,write_timeout=.2) as transport,a.log.open('x',encoding='utf-8') as log:
        def record(direction,raw):log.write(json.dumps(dict(wall_ns=time.monotonic_ns(),direction=direction,hex=raw.hex(),source_kind='hardware' if direction!='meta' else 'diagnostic'))+'\n');log.flush()
        def send(raw):record('command',raw);n=transport.write(raw);assert n==len(raw),'serial short write'
        stream=pdg15.Stream();send(pdg15.encode(dict(type=pdg15.PROBE)));deadline=time.monotonic()+2;info=None
        while info is None:
            now=time.monotonic()
            if now>deadline:raise TimeoutError('No PDG15 gateway hello')
            raw=transport.read(min(4096,max(1,transport.in_waiting)))
            if raw:record('reply',raw)
            for m in stream.feed(raw):
                if m['type']!=pdg15.HELLO:raise ValueError('Unexpected discovery frame')
                info=m
        if a.diagnostic:
            send(pdg15.encode(dict(type=pdg15.REQUEST,device=info['device'],gateway_boot=info['gateway_boot'],body_boot=info['body_boot'],capture=uuid.uuid4().bytes)))
            deadline=time.monotonic()+3
            while time.monotonic()<deadline:
                raw=transport.read(min(4096,max(1,transport.in_waiting)))
                if raw:record('diagnostic',raw)
                for m in stream.feed(raw):
                    if m['type'] in (pdg15.SCAN,pdg15.ERROR):print(json.dumps({**m,'capture':m['capture'].hex(),'scope':'diagnostic only; not a PDS1 full-body pose'}));return
            raise TimeoutError('Diagnostic scan timeout')
        if a.raw_calibration is None:raise ValueError('--raw-calibration is required for hardware capture; use --diagnostic for commissioning')
        calibration,digest,mapping,wiring=read_calibration(a.raw_calibration,a.mapping.read_bytes(),a.wiring.read_bytes(),info['device'],'hardware')
        core=BridgeCore(profile,info,mapping,wiring,calibration,'hardware')
        record('raw-calibration-sha256',digest.encode('ascii'))
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
                        for m in stream.feed(raw):
                            response=core.reply(m,time.monotonic())
                            if response:client.sendall(encode(envelope(response)))
                        if core.active is not None and time.monotonic()-core.wall>3:raise TimeoutError('Hardware acquisition deadline')
                finally:
                    if core.active is not None:send(pdg15.encode(dict(type=pdg15.CANCEL,device=info['device'],gateway_boot=info['gateway_boot'],body_boot=info['body_boot'],capture=core.active)))
if __name__=='__main__':run()
