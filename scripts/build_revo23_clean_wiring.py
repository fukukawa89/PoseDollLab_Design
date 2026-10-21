"""Reuse the E fixture checks on F, with placements on the new sparse structure."""
from revo23_clean import *
import build_revo23_wire_seats as seats
import math


def new_skin(key,p,cfg):
    z=np.load(FROOT/(key.replace('/','__')+'_skin.npz'))
    return solid(z['v'],z['f'])


def positions(body,N,cfg,needed,host=None):
    old=read(EHISTORY/'wire_seats.json')['seats']
    geom=canonical(body,N,cfg)
    outer=move(geom[1],np.linalg.inv(N)@geom[3]) if geom else None
    # Retain the former cable route where a complete new surface still exists.
    for r in old:
        if r['body']==body and r['part'].startswith('frame/'):
            yield np.array(r['transform_body_mm']),outer,dict(previous_seat=r['id'])
    if geom:
        rows,A=geom[2:];fn=PchipInterpolator(rows[:,0],rows[:,1:],axis=0)
        for theta in np.deg2rad([180,157.5,202.5,135,225,112.5,247.5,90,270,67.5,292.5,45,315,22.5,337.5,0]):
            for fraction in (.25,.75,.5,.15,.85):
                z=rows[0,0]+(rows[-1,0]-rows[0,0])*fraction
                cx,cy,rx,ry=fn(z);inward=-np.array([np.cos(theta)/rx,np.sin(theta)/ry,0.])
                inward/=np.linalg.norm(inward);up=np.array([0.,0.,1.])
                C=np.eye(4);C[:3,:3]=np.c_[np.cross(inward,up),inward,up]
                C[:3,3]=[cx+(rx-2.4)*np.cos(theta),cy+(ry-2.4)*np.sin(theta),z]
                C[:3,3]+=inward*1.5
                yield np.linalg.inv(N)@A@C,outer,dict(theta_deg=np.rad2deg(theta),z_mm=z)
    # Also offer broad faces of the sparse rods. Saddles fuse directly to the
    # rod/wall, never stand on another set of connector struts.
    v,f=vf(host);tri=v[f]
    norm=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);area=np.linalg.norm(norm,axis=1)
    norm/=np.maximum(area[:,None],1e-12);centroid=tri.mean(1)
    back=N[:3,:3].T@np.array([-1.,0,0])
    ranking=np.argsort(-(area*(1+2*np.maximum(0,norm@back))))
    _,first=np.unique(np.floor(centroid[ranking]/3).astype(int),axis=0,return_index=True)
    for n in ranking[np.sort(first)]:
        if area[n]<.05:continue
        outward=norm[n]
        if geom:
            c=(N@np.r_[centroid[n],1])[:3]-geom[3][:3,3]
            worldn=N[:3,:3]@outward
            if c[:2]@worldn[:2]>3 and np.linalg.norm(c[:2])>20:continue
        up=N[:3,:3].T@np.array([0.,0.,1.])
        up-=outward*np.dot(up,outward)
        if np.linalg.norm(up)<.15:
            up=np.eye(3)[np.argmin(abs(outward))]
            up-=outward*np.dot(up,outward)
        up/=np.linalg.norm(up);across=np.cross(outward,up)
        M=np.eye(4);M[:3,:3]=np.c_[across,outward,up];M[:3,3]=centroid[n]+outward*1.5
        yield M,outer,dict(sparse_structure_face=int(n))


def configure(module):
    module.load_e=load_f;module.EROOT=FROOT;module.DHISTORY=EHISTORY;module.DHASH=EHASH
    module.local_skin=new_skin


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--keys',nargs='*')
    ap.add_argument('--route',action='store_true');ap.add_argument('--channels',action='store_true')
    ap.add_argument('--verify',action='store_true');args=ap.parse_args()
    configure(seats);seats.candidate_positions=positions
    casepath=FROOT/'o22__controller_housing.npz'
    if not casepath.exists():shutil.copy2(EHISTORY/'candidates'/casepath.name,casepath)
    if not (FROOT/'wire_seats.json').exists():
        old=read(EHISTORY/'wire_seats.json')
        old['seats']=[r for r in old['seats'] if r['part']=='o22/controller_housing']
        put(FROOT/'wire_seats.json',old)
    if args.route:
        import route_revo23_harness as route
        configure(route);route.main()
    elif args.channels:
        import channel_revo23_harness as channels
        configure(channels)
        channels.main(args.keys)
    elif args.verify:
        import verify_revo23_wire_fixtures
    else:seats.build_seats(args.keys)
