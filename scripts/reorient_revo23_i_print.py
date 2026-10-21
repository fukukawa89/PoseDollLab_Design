"""Choose a broad bed face while keeping the verified connector layer direction."""
from print_revo23_i import *

def run(rid,rank):
    specpath=PRINT/'candidates'/(rid+'.json');spec=read(specpath);old=copy.deepcopy(spec['candidates'][0]);m=trimesh.load(IROOT/spec['source']['staged_stl'],process=True)
    parts,p,cfg=load_i();N=frames(p,p['neutral_raw_deg']);T=np.linalg.inv(N[parts[spec['key']]['token']]);lines=[]
    for r in i_records(spec['key'])['rods']:
        lines.append(dict(points=np.array(r['centerline_world_mm'])@T[:3,:3].T+T[:3,3],radius=r['radius_mm'],mount=r['mount']))
    normals={}
    for n,a in zip(np.round(m.face_normals,3),m.area_faces):normals[tuple(n)]=normals.get(tuple(n),0.)+a
    directions=[-np.array(k)for k,a in sorted(normals.items(),key=lambda x:-x[1])[:150]]+[d*s for d in np.eye(3)for s in(-1,1)]
    previous=opt.metrics(m,np.array(old['matrix']),lines);ranked=[];seen=[]
    for d in directions:
        d=d/np.linalg.norm(d)
        if any(d@q>.99999 for q in seen):continue
        seen.append(d);M,size=opt.placement(m.vertices,opt.frame(d));met=opt.metrics(m,M,lines)
        if max(size[:2])>170 or size[2]>178 or met['bed_contact_projection_mm2']<2:continue
        if met['rod_verticality']>previous['rod_verticality']+.08 or met['max_rod_angle_to_bed_deg']>previous['max_rod_angle_to_bed_deg']+15:continue
        score=met['overhang_projection_volume_proxy_mm3']/1000+25*met['rod_verticality']+30/(met['bed_contact_projection_mm2']+1)+size[2]*.015
        ranked.append(dict(matrix=M,size_mm=size,metrics=met,score=score))
    ranked.sort(key=lambda r:r['score']);assert len(ranked)>rank,(rid,'no broad face with a suitable rod direction')
    c=copy.deepcopy(old);c.update(ranked[rank]);c.update(name=f'unified_broadface_{rank}',support='snug',blocker_margin_mm=2.2,shield_enforcers=True,enforce_sources=[])
    for name in ('manual_caps','enforce_mesh','enforce_source'):c.pop(name,None)
    c.setdefault('settings',{}).update(support_threshold_angle='45',support_object_xy_distance='.6',support_expansion='0',support_top_z_distance='.24',support_bottom_z_distance='.24',bridge_no_support='0')
    put(PRINT/'orientation_ranks'/(rid+'.json'),dict(previous=previous,ranked=ranked))
    trial=dict(spec,candidates=[c]);opt.build_candidate(trial,c);result=run_one(trial)
    if result['passed']:spec['candidates']=[c]+[x for x in spec['candidates']if x['name']!=c['name']];put(specpath,spec)
    print('I BROADFACE',rid,result['passed'],{k:result[k]['passed']for k in('native','clearance','islands','caps')},flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('id');ap.add_argument('--rank',type=int,default=0);a=ap.parse_args();configure_print();run(a.id,a.rank)
