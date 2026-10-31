"""Auditable incremental exact collision proof after local geometry changes.

Unchanged pairs retain a completed full PASS only if meshes, frames and the
entire kinematic profile match. Every pair involving a changed solid is retested
at every original sample. This does not reuse assembly or strength conclusions.
"""
from verify import *
import itertools

def main():
    ref=OUT/'reference/motion_baseline_5a06';oldhash=sha(ref/'assembly_meshes.npz');digest=sha(OUT/'assembly_meshes.npz')
    assert load(ref/'profiles/device_profile.json')==load(OUT/'profiles/device_profile.json'),'Kinematics changed: full sweep required'
    old=read_saved(ref);now=read_saved();oldz=np.load(ref/'assembly_meshes.npz');z=np.load(OUT/'assembly_meshes.npz');byold={p['name']:p for p in old}
    changed=[];unchanged=[]
    for p in now:
        q=byold.get(p['name']);same=q is not None and p['frame']==q['frame']
        if same:
            for suffix in ['v','f']:
                if not np.array_equal(z[str(p['i'])+suffix],oldz[str(q['i'])+suffix]):same=False;break
        (unchanged if same else changed).append(p['name'])
    v=context();solids=[p['s'] for p in now];engine=v.Collision(now,solids);active=np.array([p['name'] in changed for p in now]);ij=np.array(np.where(engine.mask & (active[:,None]|active[None,:]))).T
    corners=np.array([[c for c in itertools.product(*zip(*bounds(p['s'])))] for p in now]);frs=[p['frame'] for p in now];cache={};qcache={};bools=0
    def check(q):
        nonlocal bools
        qkey=json.dumps(q,sort_keys=True)
        if qkey in qcache:return qcache[qkey]
        F=frames(q);rots=np.array([F[fr][:3,:3] for fr in frs]);trans=np.array([F[fr][:3,3] for fr in frs]);pts=np.einsum('nij,nkj->nki',rots,corners)+trans[:,None,:];lo=pts.min(1);hi=pts.max(1)
        broad=ij[np.all(hi[ij[:,0]]>lo[ij[:,1]]+1e-6,1)&np.all(hi[ij[:,1]]>lo[ij[:,0]]+1e-6,1)];hits=[]
        for i,j in broad:
            rel=np.linalg.inv(F[frs[i]])@F[frs[j]];key=(int(i),int(j),np.round(rel,7).tobytes())
            if key not in cache:cache[key]=(solids[i]^moved(solids[j],rel)).volume();bools+=1
            vol=cache[key]
            if vol>.02:hits.append(dict(a=now[i]['name'],b=now[j]['name'],volume_mm3=round(vol,5),segments=[v.segment(frs[i]),v.segment(frs[j])],required_adjacent=True))
        qcache[qkey]=hits;return hits
    # Independent full-engine spot comparisons cover the modified shoulder and
    # head interfaces and detect errors in the reduced candidate-pair traversal.
    controls=[]
    for q in [dict(base.NEUTRAL_ANGLES),{**base.NEUTRAL_ANGLES,'r_clavicle_elevate':25},{**base.NEUTRAL_ANGLES,'r_clavicle_protract':-20},{**base.NEUTRAL_ANGLES,'neck_yaw':70},{**base.NEUTRAL_ANGLES,'r_shoulder_flex':165}]:
        a=engine.check(q);b=check(q);key=lambda x:sorted((r['a'],r['b'],r['volume_mm3']) for r in x);controls.append(dict(angles=q,full_matches_delta=key(a)==key(b)))
    assert all(c['full_matches_delta'] for c in controls),'Incremental/full-engine mismatch'
    proof=dict(baseline_directory=ref.relative_to(OUT).as_posix(),baseline_geometry_sha256=oldhash,changed_parts=changed,unchanged_parts_count=len(unchanged),removed_parts=sorted(set(byold)-{p['name'] for p in now}),unchanged_profile_and_exact_mesh_arrays=True,affected_candidate_pairs=len(ij),full_engine_spot_comparisons=controls)
    summaries=[]
    for name in ['motion_named_endpoints','rom_examination_dense','motion_task_paths','joint_local_grids']:
        r=load(ref/f'verification/{name}.json');assert r['geometry_sha256']==oldhash and r['status'].startswith('PASS')
        fails=0;count=0
        if name=='motion_task_paths':
            for case in r['cases']:
                bad=[]
                for i,q in enumerate(case['path']):
                    h=check(q);count+=1
                    if h:bad.append(dict(index=i,angles=q,collisions=h))
                case['last_failure']=bad[-1] if bad else None;case['status']='FAIL' if bad else 'PASS_SAMPLED_PATH';fails+=len(bad)
            r['status']='FAIL' if fails else 'PASS_SAMPLED_PATHS'
        else:
            cases=r['cases'] if 'cases' in r else [c for g in r['groups'] for c in g['cases']]
            for case in cases:
                assert case['count']==0,'Baseline had collisions'
                h=check(case['angles']);case['count']=len(h);case['collisions']=h;count+=1;fails+=bool(h)
            r['status']='FAIL' if fails else ('PASS_SAMPLED_GRIDS' if name=='joint_local_grids' else 'PASS')
            if name=='motion_named_endpoints':
                pairs={}
                for c in cases:
                    for h in c['collisions']:
                        key=h['a']+' / '+h['b'];x=pairs.setdefault(key,dict(poses=[],max_mm3=0));x['poses'].append(c['pose']);x['max_mm3']=max(x['max_mm3'],h['volume_mm3'])
                r['pairs']=pairs
            if name=='joint_local_grids':
                r['failed_cases']=fails
                for g in r['groups']:g['status']='FAIL' if any(c['count'] for c in g['cases']) else 'PASS'
        r.update(geometry_sha256=digest,incremental_proof=proof)
        put(OUT/f'verification/{name}.json',r);summaries.append(dict(report=name,samples=count,failed_samples=fails));print('DELTA',name,count,fails,flush=True)
    put(OUT/'verification/motion_delta_proof.json',dict(status='PASS_INCREMENTAL_EXACT' if all(r['failed_samples']==0 for r in summaries) else 'FAIL',geometry_sha256=digest,proof=proof,reports=summaries,unique_poses=len(qcache),exact_boolean_tests=bools,scope='Same/adjacent anatomy, different rigid family, 0.02 mm3 overlap threshold. Unchanged pair results proved by exact saved mesh arrays and unchanged profile; all changed pairs recomputed. Finite samples only.'))
if __name__=='__main__':main()
