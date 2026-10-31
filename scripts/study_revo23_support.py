"""Read-only comparison of higher support roots after the deeper box move."""
from study_revo23_backpack import *
from deepen_revo23_backpack import fastener_pair

def candidate(center):
    cx=-204.7;z=550.;out=[]
    out+=[box([-52.2,y-8,center-15],[-50.2,y+8,center+15])for y in(-30,30)]
    out+=[box([cx+2.2,y-8,z-7],[cx+7.2,y+8,z+19])for y in(-55,55)]
    for side in(-1,1):
        a=[-51.2,side*20,center];lo=[cx+6.2,side*20,z-2];hi=[cx+6.2,side*20,z+14]
        out +=[capsule(a,lo,3.5),capsule(a,hi,3.5),capsule(lo,hi,3.5)]
    out +=[capsule([cx+6.2,-55,zz],[cx+6.2,55,zz],3)for zz in(z-2,z+14)]
    bracket=union(out)^box([-400,-100,400],[-50.2,100,700])
    hardware=[]
    for y,zz in itertools.product((-30.,30.),(center-8,center+8)):hardware.extend(fastener_pair([-52.2,y,zz]))
    for y,zz in itertools.product((-55.,55.),(z,z+12)):hardware.extend(fastener_pair([cx,y,zz]))
    return bracket+union(hardware)

def main():
    parts=load_current();p=read(B/'profiles/device_profile.json');_,_,bounds,records=prepare(parts,p);cache={};rows=[]
    for z in(505.,520.,535.,550.):
        s=candidate(z);bb=np.array(s.bounding_box())
        ix=np.flatnonzero(np.all(np.minimum(bb[3:],bounds[:,3:])-np.maximum(bb[:3],bounds[:,:3])>0,axis=1));hits=[]
        for i in ix:
            r=records[i]
            if i not in cache:cache[i]=move(parts[r['key']]['s'],r['matrix'])
            v=float((s^cache[i]).volume())
            if v>.03:hits.append(dict(key=r['key'],poses=r['poses'],overlap_mm3=v))
        poses=sorted({q for h in hits for q in h['poses']});trunk=[q for q in poses if q.startswith(('waist/','chest/'))]
        rows.append(dict(root_center_z_mm=z,hits=hits,poses=poses,trunk_poses=trunk))
        print('ROOT',z,'PART_POSES',len(hits),'POSES',len(poses),'TRUNK',len(trunk),flush=True)
    put(B/'verification/backpack_support_root_study.json',dict(geometry_sha256=sha(B/'assembly.npz'),rows=rows,
        scope='Bracket exterior and mounting hardware vs other rigid owners in 343 poses. New chest landing pads and nut holes are not modeled; no assembly or strength approval.'))

if __name__=='__main__':main()
