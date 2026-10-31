"""R5 seven-axis USB reader for the reused O22 SSI carrier.
Only --port opens a serial device. Faults remain faults; no stale-angle fallback.
"""
from pathlib import Path
import argparse, json, struct, time, uuid, zlib, math

CHANNELS={'RP':12,'HS':13,'RU':14,'HE':16,'RF':17,'WF':18}
REQUIRED=sum(1<<i for i in CHANNELS.values())
SIZE=280
PROBE,HELLO,REQUEST,ACCEPTED,SCAN,CANCEL,STOP,ERROR=range(8)

def crc6(data):
    c=0
    for bit in range(17,-1,-1):
        fb=(c>>5)^((data>>bit)&1);c=(c<<1)&63
        if fb:c^=3
    return c

def sensor_valid(word,idle):
    return bool(idle) and 0<=word<=0xffffff and ((word>>6)&15)==0 and crc6(word>>6)==(word&63)

def crc4(word):
    c=15;word&=0xfffffff0
    for bit in range(31,-1,-1):
        fb=((c>>3)^(word>>bit))&1;c=(c<<1)&15
        if fb:c^=3
    return c

def tm_data(word):return (word>>8)&0xffff

def tm_valid(words):
    if len(words)!=8 or any(w in [0,0xffffffff] or crc4(w)!=(w&15) or w&0xc0000080 for w in words):return False
    pre,post=tm_data(words[3]),tm_data(words[4])
    if pre&0x2700!=0x2700 or post&0x2700!=0x2700 or (pre^post)&0x70:return False
    if tm_data(words[5])&0x9f03 or tm_data(words[6])&0x783f or tm_data(words[7])!=0x3130:return False
    return all(abs(signed16(tm_data(w)))<=31129 for w in words[:3])

def signed16(v):return v-65536 if v&0x8000 else v

def decode(data):
    if len(data)!=SIZE or data[:4]!=b'R5AR' or data[4]!=1 or data[5]>ERROR:raise ValueError('USB frame header/size')
    if data[80:86]!=bytes([6,3,1,0,0,0]) or any(data[i] for i in [6,7,86,87,234,235]):raise ValueError('USB reserved fields')
    if zlib.crc32(data[:276])!=struct.unpack_from('<I',data,276)[0]:raise ValueError('USB CRC32')
    device,tboot,bboot=struct.unpack_from('<QQQ',data,8);scan,token=struct.unpack_from('<II',data,48)
    request,start,end=struct.unpack_from('<QQQ',data,56)
    valid=struct.unpack_from('<Q',data,88)[0];idle=struct.unpack_from('<Q',data,236)[0]
    words=[int.from_bytes(data[96+3*i:99+3*i],'little') for i in range(46)]
    if (valid|idle)>>46:raise ValueError('USB channel mask')
    if data[5]==SCAN:
        if not scan or not token or not request<=start<end or end-start>60000:raise ValueError('USB scan timing')
        for i,w in enumerate(words):
            if bool(valid&(1<<i))!=sensor_valid(w,idle&(1<<i)):raise ValueError('SSI validity-mask mismatch')
    channels={k:{'valid':sensor_valid(words[i],idle&(1<<i)), 'raw_word':words[i], 'raw_deg':(words[i]>>10)*360/16384 if sensor_valid(words[i],idle&(1<<i)) else None,'status_bits':(words[i]>>6)&15} for k,i in CHANNELS.items()}
    tm=list(struct.unpack_from('<8I',data,244));ok=tm_valid(tm)
    channels['WD']=dict(valid=ok,raw_frames=tm,field_mT=[signed16(tm_data(w))*100/32768 for w in tm[:3]] if ok else None)
    return dict(type=data[5],device=device,transport_boot=tboot,body_boot=bboot,capture=data[32:48].hex(),scan=scan,token=token,request_us=request,start_us=start,end_us=end,valid_mask=valid,channels=channels)

def command(kind,identity=None,capture=None):
    d=bytearray(SIZE);d[:4]=b'R5AR';d[4:6]=bytes([1,kind]);d[80:86]=bytes([6,3,1,0,0,0])
    if identity:struct.pack_into('<QQQ',d,8,identity['device'],identity['transport_boot'],identity['body_boot'])
    if capture:d[32:48]=bytes.fromhex(capture)
    struct.pack_into('<I',d,276,zlib.crc32(d[:276]));return bytes(d)

def wrap(x):return (x+180)%360-180

def vector_angle(field,cal):
    if not all(cal.get(k) for k in ['direction_verified','range_verified','coupled_wrist_verified','forward_reverse_verified']):raise ValueError('WD measured calibration incomplete')
    lut=cal['lut'];tol=cal.get('max_residual_mT')
    if len(lut)<11 or tol is None or not 0<tol<=1 or lut[0][0]>-20 or lut[-1][0]<30:raise ValueError('WD LUT coverage/residual gate missing')
    choices=[]
    for p0,p1 in zip(lut,lut[1:]):
        if not 0<p1[0]-p0[0]<=5.01:raise ValueError('WD LUT order/spacing')
        d=[b-a for a,b in zip(p0[1:],p1[1:])];den=sum(x*x for x in d)
        if math.sqrt(den)/(p1[0]-p0[0])<.15:raise ValueError('WD insufficient field sensitivity')
        t=max(0,min(1,sum((b-a)*c for a,b,c in zip(p0[1:],field,d))/den))
        res=math.sqrt(sum((b-(a+t*c))**2 for a,b,c in zip(p0[1:],field,d)))
        choices.append((res,p0[0]+t*(p1[0]-p0[0])))
    choices.sort();res,q=choices[0]
    if res>tol:raise ValueError('WD field outside calibrated curve')
    if any(abs(q-qq)>4 and rr<=res+tol for rr,qq in choices[1:]):raise ValueError('WD ambiguous magnetic field')
    return q

def angles(frame,calibration):
    if not all(frame['channels'][k]['valid'] for k in [*CHANNELS,'WD']):raise ValueError('A required sensor is faulty; no pose emitted')
    output={}
    for key in CHANNELS:
        c=calibration['channels'][key]
        if not c.get('direction_verified') or not c.get('range_verified'):raise ValueError(key+' calibration incomplete')
        raw=frame['channels'][key]['raw_deg'];base=c['reference_raw_deg'];q=c['reference_joint_deg']+c['sign']*wrap(raw-base)
        # Select in raw-angle coordinates before applying measured distortion correction.
        lut=c.get('correction_lut',[])
        bounds=[lut[0][0],lut[-1][0]] if lut else c['limits_deg']
        candidates=[q+360*n for n in [-1,0,1] if bounds[0]-.5<=q+360*n<=bounds[1]+.5]
        if len(candidates)!=1:raise ValueError(key+' outside calibrated range or ambiguous wrap')
        q=candidates[0]
        if lut:
            if len(lut)<2 or any(b[0]<=a[0] for a,b in zip(lut,lut[1:])):raise ValueError(key+' invalid calibration LUT')
            segment=next(((a,b) for a,b in zip(lut,lut[1:]) if a[0]<=q<=b[0]),(lut[0],lut[1]) if q<lut[0][0] else (lut[-2],lut[-1]))
            (x0,e0),(x1,e1)=segment;q+=e0+(e1-e0)*(q-x0)/(x1-x0)
        if not c['limits_deg'][0]-.5<=q<=c['limits_deg'][1]+.5:raise ValueError(key+' corrected angle outside calibrated range')
        output[key]=q
    output['WD']=vector_angle(frame['channels']['WD']['field_mT'],calibration['channels']['WD'])
    return output

def receive(port,deadline):
    b=bytearray()
    while len(b)<SIZE and time.monotonic()<deadline:b.extend(port.read(SIZE-len(b)))
    if len(b)!=SIZE:raise ValueError('USB timeout/truncated frame')
    return bytes(b),decode(bytes(b))

def capture(port_name,seconds,calibration=None):
    import serial
    if not 0<seconds<=55:raise ValueError('--seconds must be in (0,55]')
    if calibration and calibration.get('status')!='MEASURED_ACCEPTANCE_PASSED':raise ValueError('Measured acceptance calibration required')
    session=uuid.uuid4().hex;identity=None;frames=[];packets=[];error=None;previous=0;last_token=0
    with serial.Serial(port_name,115200,timeout=.02,write_timeout=.3) as port:
        try:
            port.reset_input_buffer();port.write(command(PROBE));raw,identity=receive(port,time.monotonic()+2)
            if identity['type']!=HELLO or not identity['device'] or identity['transport_boot']!=identity['body_boot']:raise ValueError('Invalid USB-only HELLO')
            if calibration and calibration.get('device')!=identity['device']:raise ValueError('Calibration belongs to another device')
            packets.append(raw.hex());port.write(command(REQUEST,identity,session));raw,ack=receive(port,time.monotonic()+2);packets.append(raw.hex())
            if ack['type']!=ACCEPTED or ack['capture']!=session:raise ValueError('REQUEST not accepted')
            deadline=time.monotonic()+seconds
            while time.monotonic()<deadline:
                raw,f=receive(port,deadline+.2);packets.append(raw.hex())
                if f['type']!=SCAN or f['capture']!=session or any(f[k]!=identity[k] for k in ['device','transport_boot','body_boot']):raise ValueError('Mixed session/device or firmware stopped')
                if f['scan']!=previous+1 or f['token']<=last_token:raise ValueError('Missing/replayed scan')
                if f['valid_mask']&REQUIRED!=REQUIRED or not f['channels']['WD']['valid']:raise ValueError('Sensor field/CRC/status/coherency fault; inspect raw frames')
                if calibration:f['joint_angles_deg']=angles(f,calibration)
                frames.append(f);previous=f['scan'];last_token=f['token']
        except (ValueError,serial.SerialException) as exc:error=str(exc)
        finally:
            if identity:
                try:port.write(command(STOP,identity,session))
                except serial.SerialException:pass
    return dict(status='REJECTED' if error else ('VALID_CALIBRATED_CAPTURE' if calibration else 'RAW_CAPTURE_NEEDS_CALIBRATION'),error=error,frames=frames,packets_hex=packets,physical_accuracy_qualified=False)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',required=True);parser.add_argument('--seconds',type=float,default=2);parser.add_argument('--calibration');parser.add_argument('--output',required=True)
    a=parser.parse_args();c=json.loads(Path(a.calibration).read_text('utf8')) if a.calibration else None
    result=capture(a.port,a.seconds,c);Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(result['status'],result['error'] or '',len(result['frames']))
    raise SystemExit(1 if result['error'] else 0)
