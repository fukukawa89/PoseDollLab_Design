"""Analytic symmetric exterior patches. No obstacle-shaped cuts in a skin."""
from revo23_clean import *


def surface(rows,theta,z,wall=0):
    q=PchipInterpolator(rows[:,0],rows[:,1:],axis=0)(z)
    return np.c_[q[:,0]+(q[:,2]-wall)*np.cos(theta),
                 q[:,1]+(q[:,3]-wall)*np.sin(theta),z]


def patch(rows,center,halfangle,zmid,zhalf,wall=2.4,power=0.6):
    """One rounded rectangular patch mapped onto an anatomical surface."""
    n=128; nr=14;v=[];f=[]
    theta=np.linspace(0,2*np.pi,n,endpoint=False)
    u=np.sign(np.cos(theta))*abs(np.cos(theta))**power
    w=np.sign(np.sin(theta))*abs(np.sin(theta))**power
    for depth in (0,wall):
        v.extend(surface(rows,np.array([center]),np.array([zmid]),depth))
        for ring in range(1,nr+1):
            r=ring/nr
            v.extend(surface(rows,center+halfangle*u*r,zmid+zhalf*w*r,depth))
    layer=1+n*nr
    for d in (0,1):
        off=d*layer
        for i in range(n):
            j=(i+1)%n
            f.append([off,off+1+i,off+1+j])
        for ring in range(nr-1):
            a=off+1+ring*n;b=a+n
            for i in range(n):
                j=(i+1)%n
                f.extend([[a+i,b+i,b+j],[a+i,b+j,a+j]])
    # First orient each surface by a signed mesh, then join the boundary.
    f=np.array(f)
    f[:len(f)//2]=f[:len(f)//2,::-1]
    edge=1+(nr-1)*n
    side=[]
    for i in range(n):
        j=(i+1)%n
        side.extend([[edge+i,edge+j,layer+edge+j],
                     [edge+i,layer+edge+j,layer+edge+i]])
    m=trimesh.Trimesh(np.array(v),np.vstack((f,side)),process=False)
    m.fix_normals(multibody=True)
    assert m.is_watertight
    return solid(m.vertices,m.faces)


def tube(rows,bottom,top,wall=2.4):
    n=128;nz=48;v=[];f=[]
    theta=np.linspace(0,2*np.pi,n,endpoint=False)
    lo=bottom(theta);hi=top(theta)
    for depth in (0,wall):
        for t in np.linspace(0,1,nz):
            v.extend(surface(rows,theta,lo+(hi-lo)*t,depth))
    layer=n*nz
    for d in (0,1):
        for k in range(nz-1):
            a=d*layer+k*n;b=a+n
            for i in range(n):
                j=(i+1)%n
                face=[[a+i,a+j,b+i],[a+j,b+j,b+i]]
                f.extend(face if d==0 else [x[::-1] for x in face])
    for k in (0,nz-1):
        a=k*n
        for i in range(n):
            j=(i+1)%n
            face=[[a+i,layer+a+i,layer+a+j],[a+i,layer+a+j,a+j]]
            f.extend(face if k==0 else [x[::-1] for x in face])
    return solid(v,f)


def symmetric_frame(key,parts,N,cfg):
    item=parts[key];n=N[item['token']]
    geom=canonical(item['body'],n,cfg)
    if geom is None:return None
    A=geom[3].copy();body=item['body']
    if body.endswith(('_l','_r')):
        other=body[:-1]+('r' if body[-1]=='l' else 'l')
        on=N[parts['frame/'+other]['token']]
        A[:3,3]=[(n[0,3]+on[0,3])/2,
                  (abs(n[1,3])+abs(on[1,3]))/2*(1 if body[-1]=='l' else -1),
                  (n[2,3]+on[2,3])/2]
    else:A[1,3]=0
    return geom[2],A


def fist(side):
    stations=[[-43,2,0,9,12],[-37,2,0,12,16],[-29,2,0,13,17],
              [-24,3,0,18,20],[-22,4,0,19,21]]
    palm=loft(stations)-(loft(stations,3.2)^box([-70,-70,-39.8],[70,70,-21]))
    fingers=[]
    for y,zbottom,r in [(12,-39,3.7),(4,-42,3.9),(-4,-41,3.7),(-12,-37,3.3)]:
        y*=side
        points=np.array([[-4,y,zbottom+6],[8,y,zbottom],[16,y,zbottom+5],[15.5,y,-27]])
        fingers.extend([capsule(points[i],points[i+1],r*(1-.08*i)) for i in range(3)])
    tp=np.array([[9,side*17.5,-25],[19,side*13,-27.5],[21,side*5,-31]])
    return palm+union(fingers)+capsule(tp[0],tp[1],4.6)+capsule(tp[1],tp[2],4.1)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--keys',nargs='*');args=ap.parse_args()
    archive_e();FROOT.mkdir(exist_ok=True)
    parts,p,cfg=load_e_snapshot();N=frames(p,p['neutral_raw_deg'])
    reports=[]
    for key,item in parts.items():
        if item['role']!='structure':continue
        if args.keys and key not in args.keys:continue
        body=item['body'];geom=symmetric_frame(key,parts,N,cfg)
        skin=md.Manifold();definition='Open compact connector; no ineffective decorative skin.'
        if geom:
            rows,A=geom
            if body.startswith('thigh_'):
                side=1 if body.endswith('_l') else -1
                skin=tube(rows,lambda t:-130-22*np.cos(t),lambda t:-31+13*side*np.sin(t)-8*np.cos(t))
                definition='Full thigh tube; mirrored broad sloped hip and knee openings.'
            elif body.startswith('calf_'):
                skin=tube(rows,lambda t:np.full_like(t,-134.5),lambda t:-38+18*np.cos(t))
                definition='Full calf tube; flat ankle rim and one broad sloped knee opening.'
            elif body=='head':
                outer=loft(rows)
                inner=loft(rows,2.4)^box([-100,-100,-100],[100,100,rows[-1,0]-2.4])
                skin=(outer-inner)^box([-100,-100,39],[100,100,100])
                definition='Closed crown with one level neck opening.'
            elif body=='chest':
                skin=patch(rows,0,np.deg2rad(29),46,22,power=.65)
                definition='One symmetric rounded sternum plate.'
            elif body=='waist':
                skin=patch(rows,np.pi,np.deg2rad(88),47,10.5,power=.65)
                definition='One symmetric rounded rear waist plate; front left open.'
            elif body=='pelvis':
                skin=patch(rows,np.pi,np.deg2rad(73),29,10,power=.65)
                definition='One symmetric rounded rear pelvic plate; hip openings continuous.'
            elif body.startswith('upperarm_'):
                skin=patch(rows,np.pi,np.deg2rad(47),-70,12,power=.8)
                definition='Small mirrored rounded rear upper-arm plate.'
            elif body.startswith('elbow_'):
                skin=patch(rows,np.pi,np.deg2rad(58),-22,7,power=.8)
                definition='Small mirrored rear elbow plate, with the hinge left open.'
            elif body.startswith('forearm_'):
                side=1 if body.endswith('_l') else -1
                skin=patch(rows,side*np.pi/2,np.deg2rad(28),-28,12,power=.8)
                definition='One mirrored rounded lateral forearm plate.'
            elif body.startswith('foot_'):
                skin=patch(rows,0,np.deg2rad(43),12,32,power=.65)
                definition='One mirrored rounded sole plate; ankle and toe remain open.'
            elif body.startswith('ball_'):
                skin=tube(rows,lambda t:np.full_like(t,22),lambda t:np.full_like(t,33.5))
                definition='One mirrored smooth toe cup with a level opening.'
                outer=loft(rows);inner=loft(rows,2.4)
                skin=skin+(outer^box([-60,-60,32],[60,60,34]))
            elif body.startswith('hand_'):
                skin=fist(1 if body.endswith('_l') else -1)
                definition='Approved five-finger closed fist; continuous wrist collar.'
            if not skin.is_empty():
                skin=move(skin,np.linalg.inv(N[item['token']])@A)
        save_s(FROOT/(key.replace('/','__')+'_skin.npz'),skin)
        reports.append(dict(key=key,definition=definition,volume_mm3=skin.volume(),
                            component_count=len([x for x in skin.decompose() if x.volume()>.01]),
                            canonical_frame_mm=geom[1] if geom else None))
        print(key,definition,round(skin.volume(),1),flush=True)
    # Use a single actual mesh for each pair. This removes independent Boolean
    # triangulation differences, as well as tiny inherited FK rounding errors.
    reflection=np.diag([1.,-1.,1.,1.])
    for r in reports:
        key=r['key']
        if not key.startswith(('frame/hand_','frame/ball_')) or not key.endswith('_l'):continue
        other=key[:-1]+'r';path=FROOT/(key.replace('/','__')+'_skin.npz')
        z=np.load(path)
        if not len(z['v']):continue
        M=np.linalg.inv(N[parts[other]['token']])@reflection@N[parts[key]['token']]
        mirrored=move(solid(z['v'],z['f']),M)
        save_s(FROOT/(other.replace('/','__')+'_skin.npz'),mirrored)
    if args.keys and (FROOT/'skins.json').exists():
        reports=[r for r in read(FROOT/'skins.json')['skins'] if r['key'] not in args.keys]+reports
    put(FROOT/'skins.json',dict(revision=FREV,skins=reports,
        geometry_method='Low-order analytic openings or a single rounded rectangular patch; no obstacle-imprint cuts.'))


if __name__=='__main__':
    main()
