"""Broaden a measured rod-to-mount neck with a smooth, unclipped conical foot."""
from revo23_smooth import *
from verify_revo23_g import rod_body
from audit_revo23_load_paths import screen
from channel_revo23_harness import sweep

def wire_spaces(key):
    out=[];path=GROOT/'wire_seats.json'
    if not path.exists():return md.Manifold()
    records=read(path)['seats']
    for r in records:
        if r['part']!=key:continue
        M=np.array(r['transform_body_mm']);w=r['reserved_channel_width_mm'];h=r['reserved_channel_height_mm'];half=4.5 if r['body'].startswith('forearm_') else 6
        out.extend([move(box([-w/2-3.1,.6,-1.7],[w/2+3.1,2.4,1.7]),M),move(box([-w/2,4.95,-half],[w/2,4.95+h,half]),M)])
    path=GROOT/'wire_channels.json'
    if path.exists():
        for r in read(path)['rows']:
            if r['part']!=key or not r['channel_open_in_actual_print']:continue
            a=next(s for s in records if s['id']==r['a']);M=np.array(a['transform_body_mm'])
            out.append(sweep(np.array(r['centerline_body_mm']),M[:3,0],M[:3,1],r['width_mm'],r['height_mm']))
    return union(out)

def improve(key,other=None,threshold=24.):
    parts,p,cfg=load_g();N=frames(p,p['neutral_raw_deg']);M=N[parts[key]['token']];I=np.linalg.inv(M);R=np.diag([1.,-1.,1.,1.]);path=GROOT/(key.replace('/','__')+'.npz');report=read(path.with_suffix('.json'))
    keep=raw_keep(key,parts,p,N);skin=skin_of(key);s=parts[key]['s'];audit=screen(key,s,keep,skin,1.);spaces=Space(key,parts,p,N,False);wires=move(wire_spaces(key),M)
    if other:
        O=N[parts[other]['token']];OI=np.linalg.inv(O);os=parts[other]['s'];okp=raw_keep(other,parts,p,N);oss=Space(other,parts,p,N,False);owires=move(wire_spaces(other),O)
    for weak in sorted(audit['rows'],key=lambda r:r['conservative_cut_area_mm2']):
        if weak['conservative_cut_area_mm2']>=threshold:continue
        options=[r for r in report['rods'] if r['mount']==weak['land']]
        found=False
        for rod in options:
            pts=np.array(rod['centerline_world_mm']);a=pts[0];direction=pts[1]-a;direction/=np.linalg.norm(direction);radius=rod['radius_mm']
            for rad in (radius+1.,radius+2.,radius+3.,radius+4.):
                for length in (5.,8.,11.):
                    for depth in (1.,3.,5.):
                        pad=tapered(a+direction*length,a-direction*depth,radius,rad)
                        if (pad^wires).volume()>.01:continue
                        good,reason=spaces.clear(pad)
                        if good and other:good,reason=oss.clear(move(pad,R))
                        if not good or other and (move(pad,R)^owires).volume()>.01:continue
                        result=s+move(pad,I);after=screen(key,result,keep,skin,1.)
                        row=next(q for q in after['rows'] if q['land']==weak['land'])
                        if row['conservative_cut_area_mm2']<threshold:continue
                        if other:
                            oresult=os+move(pad,OI@R);oaudit=screen(other,oresult,okp,skin_of(other),1.)
                            if min(q['conservative_cut_area_mm2'] for q in oaudit['rows'])<threshold:continue
                        s=result;found=True;foot=dict(start_world_mm=a+direction*length,end_world_mm=a-direction*depth,r0_mm=radius,r1_mm=rad,geometric_screen_after=row['conservative_cut_area_mm2'])
                        rod.setdefault('source_feet',[]).append(foot)
                        if other:
                            os=oresult;op=GROOT/(other.replace('/','__')+'.npz');orr=read(op.with_suffix('.json'))
                            matched=min(orr['rods'],key=lambda r:np.linalg.norm(np.array(r['centerline_world_mm'])[0]-a*[1,-1,1]))
                            foot2=dict(foot,start_world_mm=np.array(foot['start_world_mm'])*[1,-1,1],end_world_mm=np.array(foot['end_world_mm'])*[1,-1,1])
                            matched.setdefault('source_feet',[]).append(foot2);save_s(op,os);orr['candidate_sha256']=sha(op);put(op.with_suffix('.json'),orr)
                        save_s(path,s);report['candidate_sha256']=sha(path);put(path.with_suffix('.json'),report)
                        print('ROOT FOOT',key,weak['land'],rad,length,depth,row['conservative_cut_area_mm2'],flush=True);break
                    if found:break
                if found:break
            if found:break
        if not found:print('ROOT NEEDS DIFFERENT ROUTE',key,weak['land'],flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('key');ap.add_argument('--mirror');ap.add_argument('--threshold',type=float,default=24.);a=ap.parse_args();improve(a.key,a.mirror,a.threshold)
