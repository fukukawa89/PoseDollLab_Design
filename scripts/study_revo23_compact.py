"""Read-only compact shoulder/backpack placement experiment.

Hinge axes keep their orientation, zero and raw input. Their centres may move;
neutral UE landmarks are explicitly restored by the downstream rigid transform.
The experiment omits replaced chest/collar carrier material, so its collision
screen is a lower bound, never an assembly clearance pass.
"""
from study_revo23_backpack import *
import copy


def relocate_hinge(p, jid, world_position):
    ff=frames(p,p['neutral_raw_deg'])
    j=next(j for j in p['joints'] if j['id']==jid)
    assert j['kind']=='hinge'
    oldchild=ff['f:'+j['child']]
    parent=ff['f:'+j['parent']]
    A=np.array(j['parent_to_mount_mm']);A[:3,3]=(np.linalg.inv(parent)@np.r_[world_position,1])[:3]
    Q=np.eye(4);Q[:3,:3]=kin.b.b.rot(2,p['neutral_raw_deg'][j['raw_ids'][0]])
    G=np.linalg.inv(parent@A@Q)@oldchild
    j['parent_to_mount_mm']=A.tolist();j['rotor_to_child_mm']=G.tolist()


def compact_profile(p,x=-25,y=24,z=549,ex=20,ey=28,ez=555):
    out=copy.deepcopy(p)
    for side,sign in [('l',1),('r',-1)]:
        relocate_hinge(out,'clavicle_'+side+'.protract',[x,sign*y,z])
        relocate_hinge(out,'clavicle_'+side+'.elevate',[ex,sign*ey,ez])
    old,new=frames(p,p['neutral_raw_deg']),frames(out,out['neutral_raw_deg'])
    assert max(np.max(abs(old[k]-new[k])) for k in old if k.startswith('f:'))<1e-9
    return out


def main():
    parts=load_current();p=read(B/'profiles/device_profile.json')
    # Removed material must later be replaced by real load-bearing geometry.
    omitted={k for k in parts if k.startswith(('frame/clavicle','revision/clavicle')) or k=='frame/chest'}
    study={k:v for k,v in parts.items() if k not in omitted}
    variants={'retained':p,
      'compact':compact_profile(p),
      'wide_front':compact_profile(p,x=-12,y=32,z=556,ex=24,ey=28,ez=562)}
    rows=[]
    for variant,p2 in variants.items():
        _,_,bounds,records=prepare(study,p2)
        for zc in (510,530,550,570,590):
            for x in (-48,-60,-72,-84,-96,-108):
                # PCB candidate 64 x 60, box 70 high x 66 wide x 34 deep.
                lo=np.array([x-34,-33,zc-35]);hi=np.array([x,33,zc+35])
                mask=np.all(np.minimum(hi+1,bounds[:,3:])-np.maximum(lo-1,bounds[:,:3])>0,axis=1)
                ii=np.flatnonzero(mask)
                caseset={s for i in ii for s in records[i]['poses'] if not s.startswith('combined')}
                rows.append(dict(variant=variant,x=x,zc=zc,lower_mm=lo,upper_mm=hi,
                    aabb_pairs=len(ii),aabb_noncombined_poses=len(caseset)))
        candidates=sorted([r for r in rows if r['variant']==variant],key=lambda r:(r['aabb_noncombined_poses'],r['aabb_pairs'],abs(r['x'])))[:5]
        cache={}
        for row in candidates:
            lo=np.array(row['lower_mm']);hi=np.array(row['upper_mm']);envelope=box(lo-1,hi+1)
            ii=np.flatnonzero(np.all(np.minimum(hi+1,bounds[:,3:])-np.maximum(lo-1,bounds[:,:3])>0,axis=1));hits=[]
            for i in ii:
                r=records[i]
                if i not in cache:cache[i]=move(study[r['key']]['s'],r['matrix'])
                v=float((envelope^cache[i]).volume())
                if v>.03:hits.append(dict(key=r['key'],poses=r['poses'],volume_mm3=v))
            row['exact_envelope_hits']=hits
            row['noncombined_poses']=sorted({p for r in hits for p in r['poses'] if not p.startswith('combined')})
            print(variant,'x',row['x'],'z',row['zc'],'unique',len(hits),'single poses',len(row['noncombined_poses']),flush=True)
        put(B/'verification/compact_layout_study.json',dict(input_sha256=sha(B/'assembly.npz'),
            omitted_carriers=sorted(omitted),clearance_allowance_mm=1,rows=rows,full_assembly_pass=False))


if __name__=='__main__':main()
