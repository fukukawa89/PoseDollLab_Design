"""Mirror wrist printed geometry; rigidly flip (never mirror) purchased PCBs."""
from build_revo23_continuous import *


def main():
    p=read(DROOT/'source/device_profile.json');F=frames(p,p['neutral_raw_deg'])
    z=np.load(C_HISTORY/'assembly.npz');doc=read(C_HISTORY/'assembly.json')
    parts={x['key']:dict(x,s=solid(z[str(x['index'])+'v'],z[str(x['index'])+'f'])) for x in doc['items']}
    L=F['j:wrist_l:C02'];R=F['j:wrist_r:C02']
    # In joint coordinates the central inversion commutes with both rotations.
    # This corrects the upside-down inherited right ankle donor without changing q.
    inversion=np.diag([-1.,-1.,-1.,1.])
    W=R@inversion@np.linalg.inv(L)
    out={};records=[]
    for key,item in parts.items():
        if not key.startswith('wrist_r/'):continue
        left=parts[key.replace('wrist_r/','wrist_l/')]
        T=inversion.copy()
        if item['role']=='sensor':
            family=key.split('/')[1]
            pcb=parts['wrist_l/'+family+'/pcb']['s']
            bb=np.array(pcb.bounding_box());c=(bb[:3]+bb[3:])/2
            axis=1 if family.startswith('C01') else 0
            reflect=np.eye(4);reflect[axis,axis]=-1;reflect[axis,3]=2*c[axis]
            T=inversion@reflect
            assert np.linalg.det(T[:3,:3])>.999
        s=move(left['s'],T);out[key+'|v'],out[key+'|f']=vf(s)
        records.append(dict(key=key,source=left['key'],transform=T,
                            purchased_board_rigid_transform=item['role']=='sensor'))
    kz=np.load(DROOT/'source/retained_interfaces.npz');keeps={k:kz[k] for k in kz.files}
    def patch(body,jid):
        key='frame/'+body;shape=move(solid(kz[key+'|v'],kz[key+'|f']),F['f:'+body])
        anchors=interface_anchors(body,p,F);a=next(x for x in anchors if x['joint']==jid)
        for b in anchors:
            d=b['point']-a['point']
            if np.linalg.norm(d)<1e-8:continue
            n=d/np.linalg.norm(d)
            shape=shape.split_by_plane(n,float(n@((a['point']+b['point'])/2)))[1]
        return shape
    hand=move(solid(kz['frame/hand_l|v'],kz['frame/hand_l|f']),F['f:hand_l'])
    hand=move(hand,np.linalg.inv(F['f:hand_r'])@W)
    keeps['frame/hand_r|v'],keeps['frame/hand_r|f']=vf(hand)
    separated=DROOT/'source/separate_forearm_lands.npz'
    if separated.exists():
        sz=np.load(separated)
        def separate_land(body,jid):
            tag='frame/'+body+'|'+jid
            return move(solid(sz[tag+'|v'],sz[tag+'|f']),F['f:'+body])
        forearm=separate_land('forearm_r','forearm_r.twist')+move(separate_land('forearm_l','wrist_l'),W)
    else:
        forearm=patch('forearm_r','forearm_r.twist')+move(patch('forearm_l','wrist_l'),W)
    forearm=move(forearm,np.linalg.inv(F['f:forearm_r']))
    keeps['frame/forearm_r|v'],keeps['frame/forearm_r|f']=vf(forearm)
    relief_path=DROOT/'source/interface_edge_reliefs.npz'
    if relief_path.exists():
        assert read(relief_path.with_suffix('.json'))['profile_sha256']==profile_signature(p)
        rz=np.load(relief_path)
        for name in rz.files:
            if not name.endswith('|v'):continue
            key=name[:-2]
            kept=solid(keeps[key+'|v'],keeps[key+'|f'])-solid(rz[key+'|v'],rz[key+'|f'])
            keeps[key+'|v'],keeps[key+'|f']=vf(kept)
    np.savez_compressed(DROOT/'source/retained_interfaces.npz',**keeps)
    np.savez_compressed(DROOT/'source/part_overrides.npz',**out)
    err=0.
    for flex in (-45,0,45):
        for dev in (-20,0,20):
            q=dict(p['neutral_raw_deg'])
            q.update({f'hand_{side}.{name}/r0':value for side in ('l','r') for name,value in [('flex',flex),('deviate',dev)]})
            ff=frames(p,q)
            for owner in ('C02','ring','C01'):
                err=max(err,float(np.max(abs(ff['j:wrist_r:'+owner]@inversion-W@ff['j:wrist_l:'+owner]))))
    assert err<1e-8,err
    put(DROOT/'source/right_wrist_mirror.json',dict(records=records,
        mirror_trajectory_error=err,raw_profile_changed=False,
        pcb_layout_mirrored=False,pcb_component_clearance_requires_check=True,
        note='Printed right wrist parts mirror the left donor. Existing sensor PCBs use a proper rigid rotation; component positions remain those of the original manufactured boards.'))
    print('WRIST',len(records),'trajectory error',err,flush=True)


if __name__=='__main__':main()
