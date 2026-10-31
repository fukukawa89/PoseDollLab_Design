"""Relieve final reinforced shoulder pairs while preserving accepted D material."""
from build_revo23_wire_seats import *
from build_revo23_reinforced import padded_hull
from audit_revo23_load_paths import screen

parts,p,cfg=load_e();baseline,_,_=load_d()
poses=read(DHISTORY/'profiles/daily_poses.json')['poses']
poses.update(read(DHISTORY/'profiles/edge_path_poses.json')['poses'])
FF={n:frames(p,q) for n,q in poses.items()}
kz=np.load(DHISTORY/'source/retained_interfaces.npz')
changed=set();records=[]
for a,b in [('frame/clavicle_l','frame/upperarm_l'),
            ('frame/clavicle_r','frame/upperarm_r'),
            ('frame/clavicle_l','frame/clavicle_l.protract_frame'),
            ('frame/clavicle_r','frame/clavicle_r.protract_frame')]:
    seen=set()
    for name,F in FF.items():
        T=np.linalg.inv(F[parts[a]['token']])@F[parts[b]['token']]
        sig=tuple(np.round(T,6).ravel())
        if sig in seen:continue
        seen.add(sig)
        sa=parts[a]['s'];sb=move(parts[b]['s'],T)
        ba=np.array(sa.bounding_box());bb=np.array(sb.bounding_box())
        if np.any(np.minimum(ba[3:],bb[3:])-np.maximum(ba[:3],bb[:3])<=0):continue
        hit=sa^sb;volume=max(0.,hit.volume())
        if volume<.025:continue
        # Only added reinforcement may be removed. D's external skin, precision
        # lands and existing material remain intact. If the first part's old
        # material is involved, remove the neighbour's added material instead.
        cutter=padded_hull(hit,.6)
        na=sa-(cutter-baseline[a]['s'])
        remaining=na^sb
        if remaining.volume()>.005:
            cb=move(padded_hull(remaining,.6),np.linalg.inv(T))-baseline[b]['s']
            nb=parts[b]['s']-cb
        else:nb=parts[b]['s']
        na=max(na.decompose(),key=lambda x:x.volume())
        nb=max(nb.decompose(),key=lambda x:x.volume())
        assert ((sa-na)^baseline[a]['s']).volume()<.01,(a,name,'D material split')
        assert ((parts[b]['s']-nb)^baseline[b]['s']).volume()<.01,(b,name,'D material split')
        residual=max(0.,(na^move(nb,T)).volume())
        assert residual<.025,(a,b,name,residual)
        removed_a=sa.volume()-na.volume();removed_b=parts[b]['s'].volume()-nb.volume()
        if removed_a>.001:parts[a]['s']=solid(*vf(na));changed.add(a)
        if removed_b>.001:parts[b]['s']=solid(*vf(nb));changed.add(b)
        records.append(dict(pair=[a,b],pose=name,before_mm3=volume,
            removed_a_mm3=removed_a,removed_b_mm3=removed_b,after_mm3=residual))
        print('SHOULDER RELIEF',a,b,name,round(volume,3),round(removed_a,3),round(removed_b,3),flush=True)
for key in changed:
    path=EROOT/(key.replace('/','__')+'.npz')
    backup=EROOT/'checkpoints/before_final_shoulder_relief';backup.mkdir(parents=True,exist_ok=True)
    if not (backup/path.name).exists():shutil.copy2(path,backup/path.name)
    v,f=vf(parts[key]['s']);assert trimesh.Trimesh(v,f,process=False).is_watertight
    np.savez_compressed(path,v=v,f=f)
    keep=solid(kz[key+'|v'],kz[key+'|f'])
    audit=screen(key,parts[key]['s'],keep,local_skin(key,p,cfg),1.)
    audit['candidate_mesh_sha256']=sha(path)
    put(EROOT/'load_paths_candidate'/(key.replace('/','__')+'.json'),audit)
put(EROOT/'final_shoulder_relief.json',dict(rows=records,changed_parts=sorted(changed),
    input_geometry_sha256=DHASH,pose_count=len(poses),D_material_removed=False))
print('SHOULDER RELIEF COMPLETE',sorted(changed),flush=True)
