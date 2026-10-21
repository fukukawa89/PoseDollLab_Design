"""Check the rigidly flipped purchased wrist PCBs against their actual parts."""
from build_revo23_continuous import *
import itertools


def main():
    parts=load_c();p=read(DROOT/'source/device_profile.json')
    keys=[k for k in parts if k.startswith('wrist_r/')]
    sensors=[k for k in keys if parts[k]['role']=='sensor']
    obstacles=[k for k in keys if parts[k]['role']!='sensor']
    bounds={}
    for k in keys:
        bb=parts[k]['s'].bounding_box();bounds[k]=np.array(list(itertools.product(*zip(bb[:3],bb[3:]))))
    hits=[];cache={}
    for flex,dev in itertools.product((-45,0,45),(-20,0,20)):
        q=dict(p['neutral_raw_deg']);q['hand_r.flex/r0']=flex;q['hand_r.deviate/r0']=dev
        ff=frames(p,q);bb={}
        for k in keys:
            M=ff[parts[k]['token']];v=bounds[k]@M[:3,:3].T+M[:3,3];bb[k]=np.r_[v.min(0),v.max(0)]
        for a,b in itertools.product(sensors,obstacles):
            if np.any(np.minimum(bb[a][3:],bb[b][3:])-np.maximum(bb[a][:3],bb[b][:3])<=0):continue
            T=np.linalg.inv(ff[parts[a]['token']])@ff[parts[b]['token']]
            sig=(a,b,tuple(np.round(T,7).ravel()))
            if sig not in cache:cache[sig]=max(0.,float((parts[a]['s']^move(parts[b]['s'],T)).volume()))
            if cache[sig]>.05:hits.append(dict(flex_deg=flex,deviation_deg=dev,pair=[a,b],overlap_mm3=cache[sig]))
    align=[]
    inversion=np.diag([-1.,-1.,-1.,1.])
    for family in ('C01','C02'):
        left=parts[f'wrist_l/{family}_sensor_PCB/SOP8_max']['s']
        right=parts[f'wrist_r/{family}_sensor_PCB/SOP8_max']['s']
        a=np.asarray(move(left,inversion).bounding_box());b=np.asarray(right.bounding_box())
        align.append(dict(family=family,sensor_package_center_error_vs_mirrored_donor_mm=float(np.linalg.norm((a[:3]+a[3:]-b[:3]-b[3:])/2))))
    result=dict(source_hardware_overrides_sha256=sha(DROOT/'source/part_overrides.npz'),
        tested_angle_pairs=9,sensor_package_alignment=align,contacts=hits,passed=not hits,
        scope='Both PCB substrates, component envelopes and solder envelope versus every non-PCB part of the right wrist, including rigid attachments.',
        wire_flexibility_checked=False,physical_zero_and_direction_calibration_required=True,
        purchased_board_layout_mirrored=False,manufacturing_release=False)
    put(B/'verification/right_wrist_boards.json',result)
    print('WRIST BOARDS',result['passed'],len(hits),'alignment',align,flush=True)
    for row in hits[:10]:print(row,flush=True)


if __name__=='__main__':main()
