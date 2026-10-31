"""Five distinct curled fingers, fixed to a hollow palm and the preserved wrist."""
from revo23_reinforcement import *
from audit_revo23_load_paths import screen


def build(key,parts,p,cfg):
    side=1 if key.endswith('_l') else -1
    item=parts[key];N=frames(p,p['neutral_raw_deg'])[item['token']]
    A=canonical(item['body'],N,cfg)[3];T=np.linalg.inv(A)@N
    path=EROOT/(key.replace('/','__')+'.npz')
    z=np.load(path);old_local=solid(z['v'],z['f']);old=move(old_local,T)
    # Keep the entire wrist attachment. Shape changes start beyond its -20.25 mm end.
    upper=old^box([-100,-100,-24],[100,100,100])
    # Remove the old featureless thumb mass, outside the actual mounting land.
    thumb_zone=box([0,12.5,-45],[60,55,-12]) if side==1 else box([0,-55,-45],[60,-12.5,-12])
    upper=upper-thumb_zone
    stations=[[-43,2,0,9,12],[-37,2,0,12,16],[-29,2,0,13,17],
              [-24,3,0,18,20],[-22,4,0,19,21]]
    palm=loft(stations)
    inner=loft(stations,3.2)^box([-70,-70,-39.8],[70,70,-21])
    palm=palm-inner
    fingers=[];definitions=[]
    for name,y,zbottom,r in [('index',12,-39,3.7),('middle',4,-42,3.9),
                             ('ring',-4,-41,3.7),('little',-12,-37,3.3)]:
        y*=side
        points=np.array([[-4,y,zbottom+6],[8,y,zbottom],[16,y,zbottom+5],[15.5,y,-27]])
        s=union([capsule(points[i],points[i+1],r*(1-.08*i)) for i in range(3)])
        fingers.append(s)
        definitions.append(dict(name=name,centerline_canonical_mm=points,radius_mm=r))
    tp=np.array([[9,side*17.5,-25],[19,side*13,-27.5],[21,side*5,-31]])
    thumb=capsule(tp[0],tp[1],4.6)+capsule(tp[1],tp[2],4.1)
    fingers.append(thumb);definitions.append(dict(name='thumb',centerline_canonical_mm=tp,radius_mm=4.6))
    sculpt=upper+palm+union(fingers)
    kz=np.load(DHISTORY/'source/retained_interfaces.npz')
    keep=solid(kz[key+'|v'],kz[key+'|f'])
    local=move(sculpt,np.linalg.inv(T))+keep
    v,f=vf(local);m=trimesh.Trimesh(v,f,process=False)
    components=[c for c in local.decompose() if c.volume()>1e-4]
    assert len(components)==1 and m.is_watertight,(key,len(components))
    assert (keep-local).volume()<.001
    backup=EROOT/'checkpoints'/'before_fingers';backup.mkdir(parents=True,exist_ok=True)
    if not (backup/path.name).exists():shutil.copy2(path,backup/path.name)
    np.savez_compressed(path,v=v,f=f)
    report=read(path.with_suffix('.json'))
    report.update(finger_design=dict(fixed_finger_count=5,definitions=definitions,
        palm_wall_radial_mm=3.2,anatomical_axes='canonical +X palm/front, thumb on side*Y; fingers curl toward palm',
        articulated=False),source_watertight=True,component_count=1,volume_mm3=local.volume(),
        original_wrist_interface_loss_mm3=max(0.,(keep-local).volume()))
    put(path.with_suffix('.json'),report)
    # Use the distal fist as the load target, separated from the wrist land.
    # A hollow palm's inner/outer slicer contours alone are an ambiguous target.
    target=local^move(box([-60,-60,-60],[60,60,-31]),np.linalg.inv(T))
    cut=screen(key,local,keep,target,1.)
    put(EROOT/'load_paths_candidate'/(key.replace('/','__')+'.json'),cut)
    print('FIST',key,'five fingers','volume',local.volume(),flush=True)


if __name__=='__main__':
    parts,p,cfg=load_d()
    for key in ('frame/hand_l','frame/hand_r'):build(key,parts,p,cfg)
