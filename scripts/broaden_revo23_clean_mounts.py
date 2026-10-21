"""Broaden a mounting boss locally; no new shell-to-mount rod is introduced."""
from repair_revo23_clean_paths import *


def broaden(key,land_index,padding=6):
    parts,p,cfg=load_f();base,_,_=load_e_snapshot();F=frames(p,p['neutral_raw_deg'])
    kz=np.load(EHISTORY/'source/retained_interfaces.npz');keep=source_keep(key,kz,base[key],p,F)
    lands=sorted([c for c in keep.decompose() if c.volume()>50],key=lambda c:-c.volume())
    path=FROOT/(key.replace('/','__')+'.npz');z=np.load(path.with_name(path.stem+'_skin.npz'))
    skin=solid(z['v'],z['f']);original=parts[key]['s'];voids=wire_voids(key)
    # The pad stays within the already checked hardware/rotation envelope.
    # Its extent is measured from this one mounting land, never from the whole
    # structure's hull.
    boss=solid(*vf((padded_hull(lands[land_index],padding)^base[key]['s'])-voids))
    candidate=solid(*vf(original+boss))
    candidate=max(candidate.decompose(),key=lambda c:c.volume())
    assert (original-candidate).volume()<.02
    candidate=save_s(path,candidate)
    r=read(path.with_suffix('.json'))
    r.setdefault('local_mount_bosses',[]).append(dict(land=land_index,padding_mm=padding,
        added_volume_mm3=max(0,candidate.volume()-original.volume()),additional_rods=0))
    r.update(candidate_sha256=sha(path),volume_mm3=candidate.volume())
    put(path.with_suffix('.json'),r)
    report=screen(key,candidate,keep,skin,1)
    report['candidate_sha256']=sha(path);put(FROOT/'load_paths'/(path.stem+'.json'),report)
    print('BOSS',key,land_index,padding,flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('key');ap.add_argument('land',type=int)
    ap.add_argument('--padding',type=float,default=6)
    a=ap.parse_args();broaden(a.key,a.land,a.padding)
