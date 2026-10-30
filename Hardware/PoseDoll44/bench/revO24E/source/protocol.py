"""Fail-closed host contract for E; this is not flashed firmware or calibration."""
from build import *

def accept_packet(packet,calibration):
    if packet.get('schema')!='POSEDOLL_O24E_40_A_1':raise ValueError('Wrong schema; old D / 46-channel packet forbidden')
    if packet.get('units')!='deg':raise ValueError('Explicit degree units required')
    if not packet.get('calibrated') or not calibration.get('measured_and_accepted'):raise ValueError('Physical calibration not accepted')
    if calibration.get('geometry_sha256')!=sha(OUT/'assembly_meshes.npz'):raise ValueError('Calibration geometry mismatch')
    if calibration.get('wrist_order')!=PROFILE['wrist_order']:raise ValueError('Wrist chain mismatch')
    if set(packet.get('angles',{}))!={a['id'] for a in PROFILE['axes']}:raise ValueError('Exactly 40 named physical axes required')
    for a in PROFILE['axes']:
        value=packet['angles'][a['id']]
        if not isinstance(value,(int,float)) or not math.isfinite(value) or not a['limits_deg'][0]<=value<=a['limits_deg'][1]:raise ValueError('Invalid angle '+a['id'])
    return frames(packet['angles'])

def main():
    packet=load(OUT/'profiles/channel_map.json')['packet_candidate'];template=dict(revision='O24E',geometry_sha256=sha(OUT/'assembly_meshes.npz'),wrist_order=PROFILE['wrist_order'],measured_and_accepted=False,
        physical_sensor_boards=38,raw_scalars=42,wrist_lut_status='IDEAL_ONLY_NOT_VALID_CALIBRATION',required_records=['both wrist axes finite grid with held-out residuals','left/right physical sensor frame and signs','A raw references for 36 single axes','temperature, hysteresis, steel interference, saturation, wire motion'])
    put(OUT/'electronics/calibration_template.json',template);checks=[]
    for label,mut in [('unmeasured',{}),('old_D',{'schema':'POSEDOLL_O24D_40_A_2'}),('legacy_46',{'schema':'POSEDOLL_O22_46'}),('packet_claim_only',{'calibrated':True})]:
        try:accept_packet({**packet,**mut},template);ok=False
        except ValueError as e:ok=True;reason=str(e)
        checks.append(dict(case=label,rejected=ok,reason=reason if ok else 'incorrectly accepted'))
    put(OUT/'verification/protocol_guard.json',dict(geometry_sha256=sha(OUT/'assembly_meshes.npz'),status='PASS_NEGATIVE_CONTROLS' if all(r['rejected'] for r in checks) else 'FAIL',rows=checks,firmware_flashed=False,UE_runtime_connected=False))
    shutil.copyfile(HERE/'protocol.py',OUT/'electronics/protocol_reference.py')
if __name__=='__main__':main()
