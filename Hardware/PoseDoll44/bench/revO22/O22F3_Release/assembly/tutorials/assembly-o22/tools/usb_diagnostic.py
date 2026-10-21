"""Read-only O22 assembly diagnostics; partial populations are never valid captures.
Only an explicit --port opens hardware. No flash, calibration or UE export.
"""
from pathlib import Path
import argparse, json, sys, time, uuid
BASE=Path(__file__).resolve().parents[3]/'bench/revO22'
sys.path.insert(0,str(BASE/'source'))
from usb_capture import PROBE,HELLO,REQUEST,ACCEPTED,SCAN,STOP,command,read_packet
from mt6701 import decode_word


def summarize(frames,routes,requested):
    by_port={r['connector']:r for r in routes}
    if not frames:raise ValueError('No scan frames received')
    rows=[]
    for name in requested:
        route=by_port[name];i=route['raw_index'];decoded=[decode_word(f['words'][i],bool(f['idle_high_mask']&(1<<i))) for f in frames]
        angles=[v['counts']*360/16384 for v in decoded if v['valid']]
        rows.append({'port':name,'carrier_reference':route['carrier_reference'],'raw_id':route['raw_id'],
            'scans':len(decoded),'valid_scans':sum(v['valid'] for v in decoded),'crc_failures':sum(not v['crc_ok'] for v in decoded),
            'ssi_status_values':sorted({v['status'] for v in decoded}),'idle_low_scans':sum(not v['idle_high'] for v in decoded),
            'uncalibrated_angle_min_deg':min(angles) if angles else None,'uncalibrated_angle_max_deg':max(angles) if angles else None})
    return rows


def run(port_name,requested,seconds,output):
    import serial
    routes=json.loads((BASE/'harness/routing_plan.json').read_text(encoding='utf8'))['rows']
    available={r['connector'] for r in routes}
    if not requested or len(set(requested))!=len(requested) or set(requested)-available:raise ValueError('Use unique existing ports A01-A14, B01-B16, C01-C16')
    if not 0.1<=seconds<=2:raise ValueError('Duration must be 0.1..2 seconds')
    output=Path(output)
    if output.exists():raise FileExistsError('Choose a new output filename; existing evidence is not overwritten')
    packets=[];frames=[];identity=None;capture=uuid.uuid4().hex
    record={'schema':'POSEDOLL-O22-ASSEMBLY-DIAGNOSTIC/1','status':'DIAGNOSTIC_ONLY','valid_measurement':False,'physical_qualification':False,'ports':requested,'capture':capture,'reason':None}
    try:
        with serial.Serial(port_name,115200,timeout=.02,write_timeout=.2) as port:
            try:
                port.reset_input_buffer();port.write(command(PROBE));raw,identity=read_packet(port,time.monotonic()+1);packets.append(raw.hex())
                if identity['type']!=HELLO or not identity['device'] or not identity['transport_boot'] or identity['transport_boot']!=identity['body_boot']:raise ValueError('Invalid USB-only HELLO')
                sent=time.monotonic();port.write(command(REQUEST,identity,capture));raw,ack=read_packet(port,sent+1);packets.append(raw.hex())
                if ack['type']!=ACCEPTED or ack['capture']!=capture or any(ack[k]!=identity[k] for k in ('device','transport_boot','body_boot')):raise ValueError('Capture request rejected or identity mismatch')
                deadline=time.monotonic()+seconds;token=0;seq=0
                while time.monotonic()<deadline:
                    raw,f=read_packet(port,deadline+.15);packets.append(raw.hex())
                    if f['type']!=SCAN or f['capture']!=capture or any(f[k]!=identity[k] for k in ('device','transport_boot','body_boot')):raise ValueError('Wrong frame or device')
                    if f['request_us']!=ack['request_us'] or f['token']<=token or f['scan']!=seq+1:raise ValueError('Replayed, missing or mixed scan')
                    frames.append(f);token=f['token'];seq=f['scan']
                record['channels']=summarize(frames,routes,requested)
                record['selected_raw_channels_ok']=all(r['valid_scans']==r['scans'] for r in record['channels'])
            finally:
                if identity:
                    try:port.write(command(STOP,identity,capture))
                    except serial.SerialException:pass
    except (ValueError,serial.SerialException,OSError) as e:
        record['reason']=str(e);record['selected_raw_channels_ok']=False
    record.update(packets_hex=packets,decoded_frames=frames,note='Raw, uncalibrated diagnostics only. Invalid/missing channels are not replaced, interpolated, or exported to UE. Angle range uses linear min/max; crossing 0/360 is not an error metric.')
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    for r in record.get('channels',[]):print(f"{r['port']} {r['raw_id']} valid {r['valid_scans']}/{r['scans']} CRC-fail={r['crc_failures']} status={r['ssi_status_values']} idle-low={r['idle_low_scans']} raw-deg=[{r['uncalibrated_angle_min_deg']}, {r['uncalibrated_angle_max_deg']} (uncalibrated)")
    print('DIAGNOSTIC_ONLY',record['reason'] or ('Selected raw channels received' if record['selected_raw_channels_ok'] else 'Inspect selected channels'))
    return record

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--port',required=True);p.add_argument('--ports',nargs='+',required=True);p.add_argument('--seconds',type=float,default=1);p.add_argument('--output',required=True);a=p.parse_args()
    try:r=run(a.port,[x.upper() for x in a.ports],a.seconds,a.output)
    except (ValueError,FileExistsError) as e:p.error(str(e))
    raise SystemExit(0 if r['selected_raw_channels_ok'] else 1)
