"""P21R/1 USB capture reference. Only explicit --port can open hardware.
Preserves original packets; no IK, interpolation, or fault-to-zero fallback.
"""
from pathlib import Path
import argparse, json, struct, time, uuid, zlib
from measurement import capture_window
from mt6701 import decode_word
SIZE=248;COUNTS=bytes([14,16,16,0,0,0]);MASK=(1<<46)-1
PROBE,HELLO,REQUEST,ACCEPTED,SCAN,CANCEL,STOP,ERROR=range(8)

def decode(data):
    if len(data)!=SIZE or data[:4]!=b'P21R' or data[4]!=1 or data[5]>ERROR:raise ValueError('P21R/1 length or header')
    if any(data[i] for i in (6,7,86,87,234,235)) or data[80:86]!=COUNTS:raise ValueError('reserved fields or chain order')
    if zlib.crc32(data[:244])!=struct.unpack_from('<I',data,244)[0]:raise ValueError('CRC')
    device,tboot,bboot=struct.unpack_from('<QQQ',data,8);scan,token=struct.unpack_from('<II',data,48)
    request,start,end=struct.unpack_from('<QQQ',data,56);mask=struct.unpack_from('<Q',data,88)[0];words=[int.from_bytes(data[96+3*i:99+3*i],'little') for i in range(46)];idle=struct.unpack_from('<Q',data,236)[0]
    if (mask|idle)&~MASK:raise ValueError('mask outside 46 channels')
    if data[5]==SCAN:
        if not scan or not token or not request<=start<end or end-start>60000:raise ValueError('scan timing or sequence')
        if any(bool(mask&(1<<i))!=decode_word(v,bool(idle&(1<<i)))['valid'] for i,v in enumerate(words)):raise ValueError('validity/word disagreement')
    return dict(type=data[5],device=device,transport_boot=tboot,body_boot=bboot,capture=data[32:48].hex(),
        scan=scan,token=token,request_us=request,start_us=start,end_us=end,valid_mask=mask,idle_high_mask=idle,words=words)

def command(kind,identity=None,capture=None):
    d=bytearray(SIZE);d[:4]=b'P21R';d[4:6]=bytes([1,kind]);d[80:86]=COUNTS
    if identity:struct.pack_into('<QQQ',d,8,identity['device'],identity['transport_boot'],identity['body_boot'])
    if capture:d[32:48]=bytes.fromhex(capture)
    struct.pack_into('<I',d,244,zlib.crc32(d[:244]));return bytes(d)

def measurement_scans(profile,frames,capture):
    identity=None;previous=0;seq=0;request=None;rows=[]
    for f in frames:
        current=(f['device'],f['transport_boot'],f['body_boot'])
        if f['type']!=SCAN or f['capture']!=capture:raise ValueError('wrong capture or message type')
        if not all(current) or current[1]!=current[2] or (identity is not None and identity!=current):raise ValueError('mixed device or boot')
        if f['valid_mask']!=MASK:raise ValueError('faulty sensor; capture rejected')
        if f['token']<=previous or f['scan']!=seq+1:raise ValueError('replayed, missing or reordered scan')
        if request is not None and request!=f['request_us']:raise ValueError('mixed request clock')
        start,end=f['start_us']/1000,f['end_us']/1000
        rows.append({'device_id':str(f['device']),'boot_id':str(f['body_boot']),'capture_id':int(capture,16),
            'sequence':f['scan'],'time_ms':end,'integrity':'valid',
            'channel_time_semantics':'conservative earliest bound of sequential whole scan',
            'sample_time_bound_ms':[start,end],
            'channels':{k:{'sensor_deg':(v>>10)*360/16384,'status':'valid','time_ms':start} for k,v in zip(profile['raw_order'],f['words'])}})
        identity=current;previous=f['token'];seq=f['scan'];request=f['request_us']
    return rows

def read_packet(port,deadline):
    data=bytearray()
    while len(data)<SIZE and time.monotonic()<deadline:
        data.extend(port.read(SIZE-len(data)))
    if len(data)!=SIZE:raise ValueError('USB packet timeout/truncation')
    return bytes(data),decode(bytes(data))

def run(port_name,profile,calibration,output):
    import serial
    packets=[];frames=[];record={'schema':'POSEDOLL-O21-USB-RECORD/1','status':'INCOMPLETE','physical_qualification':False}
    identity=None;capture=uuid.uuid4().hex
    with serial.Serial(port_name,115200,timeout=.02,write_timeout=.2) as port:
        try:
            port.reset_input_buffer();port.write(command(PROBE));raw,identity=read_packet(port,time.monotonic()+1)
            packets.append(raw.hex())
            if identity['type']!=HELLO or not identity['device'] or not identity['transport_boot'] or identity['transport_boot']!=identity['body_boot']:raise ValueError('USB-only device HELLO')
            sent=time.monotonic();port.write(command(REQUEST,identity,capture));raw,ack=read_packet(port,sent+1);packets.append(raw.hex())
            if ack['type']!=ACCEPTED or ack['capture']!=capture or any(ack[k]!=identity[k] for k in ('device','transport_boot','body_boot')):raise ValueError('request rejected or wrong device')
            deadline=sent+2.5
            while time.monotonic()<deadline:
                raw,f=read_packet(port,deadline);packets.append(raw.hex());frames.append(f)
                if f['type']!=SCAN:raise ValueError('device stopped capture')
                rows=measurement_scans(profile,frames,capture)
                if rows[-1]['time_ms']-rows[0]['time_ms']>=profile['capture_policy']['stable_window_ms'] and len(rows)>=profile['capture_policy']['minimum_scans']:
                    # Mapping host elapsed time from BEFORE request transmission is
                    # a conservative upper bound in device time. It does not hide
                    # USB buffering age behind the last received timestamp.
                    evaluation=ack['request_us']/1000+(time.monotonic()-sent)*1000
                    record['measurement']=capture_window(profile,calibration,rows,expected_capture_id=int(capture,16),evaluation_time_ms=evaluation)
                    record['status']=record['measurement']['status'];break
            else:raise ValueError('no complete stable window')
        except (ValueError,serial.SerialException) as e:
            record.update(status='REJECTED',reason=str(e))
        finally:
            if identity:
                try:port.write(command(STOP,identity,capture))
                except serial.SerialException:pass
    record.update(packets_hex=packets,decoded_frames=frames,capture=capture,calibration=calibration,
        note='No UE target adapter applied. Hardware tests and calibration are separate requirements.')
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return record

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',required=True);p.add_argument('--profile',required=True);p.add_argument('--calibration',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();read=lambda x:json.loads(Path(x).read_text(encoding='utf-8-sig'))
    r=run(a.port,read(a.profile),read(a.calibration),a.output);print(r['status']);raise SystemExit(0 if r['status']=='VALID_MEASUREMENT' else 1)
