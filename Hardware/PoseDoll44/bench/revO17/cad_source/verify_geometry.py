"""Read-only verification of O17 geometry, new-part collision regression and exports."""
import itertools,struct,sys
import numpy as np
from geometry import *
from layout_fullbody import build,fk
from common import hits

def topology(tt):
    vv,ii=np.unique(tt.reshape(-1,3),axis=0,return_inverse=True);ff=ii.reshape(-1,3)
    edges=np.concatenate([ff[:,[0,1]],ff[:,[1,2]],ff[:,[2,0]]]);_,counts=np.unique(np.sort(edges,axis=1),axis=0,return_counts=True)
    return int(np.count_nonzero(counts!=2))

def main():
    change=read(OUT/'changes.json');rows=read(BENCH/'print_batch/manifest.json')['rows'];issues=[];export_checks=[]
    assert sha(H/'bench/revO16/PoseDoll_O16_Universal_Design.zip')==change['source_o16_zip_sha256']=='b4944bcba95b2ab10523fd785509abc652174c75843798b3c82d85f966861096'
    p,m,states,fail,pr,prov=build_fitted('quinn',ASSEMBLY_POSE);assert not fail
    replacement={r['part']:r for r in change['replacements']};new={k:from_tri_exact(v).simplify(1e-4) for k,v in np.load(OUT/'changed_parts.npz').items()}
    deleted={k for r in replacement.values() for k in r['replaces']}|set(change['removed_parts']);keys=[k for k in p if k not in deleted]+list(new)
    sources={k:[k] for k in p if k not in deleted};sources.update({k:r['replaces'] for k,r in replacement.items()})
    for r in rows:
        assert sha(BENCH/r['stl'])==r['stl_sha256']
        if not r['id'].startswith('N'):continue
        raw=(BENCH/r['stl']).read_bytes();n=struct.unpack_from('<I',raw,80)[0]
        a=np.frombuffer(raw[84:],dtype=np.dtype([('normal','<f4',(3,)),('vertices','<f4',(3,3)),('attr','<u2')]))
        assert len(a)==n and 84+50*n==len(raw)
        tt=a['vertices'].astype(float);bad=topology(tt);solid=from_tri_exact(tt)
        row={'id':r['id'],'triangles':n,'nonmanifold_edges':bad,'solid_count':solid_count(solid),'status':str(solid.status()),'stl_volume_mm3':float(solid.volume()),'three_mf_exists':(BENCH/'print_batch'/(r['id']+'.3mf')).exists()}
        export_checks.append(row)
        if bad or solid_count(solid)!=1 or solid.status()!=md.Error.NoError:issues.append(row)
    assert not issues,issues
    poses={'assembly':ASSEMBLY_POSE,**read(H/'mechanical_manifest/revO_pose_cases.json')['cases']};results=[];maximum_increase=0.;new_bad=[];neutral=None
    for name,angles in poses.items():
        _,meta,st,f,profile=build('quinn',angles,geometry=False);assert not f;T,_=fk(profile,angles)
        def transform(k):
            mm=m[k]
            if mm['owner']=='rigid_frame':return T[mm['body']]
            ref=mm.get('follows_part',k)
            return meta[ref]['transform']
        positioned={};old_positioned={}
        for k in p:
            M=transform(k);old_positioned[k]=move(p[k],M@np.linalg.inv(m[k]['transform']))
        for k in keys:
            if k in new:positioned[k]=move(new[k],transform(replacement[k]['anchor']))
            else:positioned[k]=old_positioned[k]
        if name=='neutral':
            bb=np.array([s.bounding_box() for s in positioned.values()]);lo=bb[:,:3].min(0);hi=bb[:,3:].max(0);neutral={'min_mm':lo.tolist(),'max_mm':hi.tolist(),'size_mm':(hi-lo).tolist(),'height_mm':float(hi[2]-lo[2]),'parts':len(positioned)}
        bb={k:np.array(s.bounding_box()) for k,s in positioned.items()};findings=[];tested=0
        for i,a in enumerate(keys):
            for b in keys[i+1:]:
                if a not in new and b not in new:continue
                if np.any(np.minimum(bb[a][3:],bb[b][3:])<=np.maximum(bb[a][:3],bb[b][:3])+1e-8):continue
                tested+=1;v=max(0.,float((positioned[a]^positioned[b]).volume()))
                if v<.001:continue
                baseline=max(0.,sum(float((old_positioned[x]^old_positioned[y]).volume()) for x in sources[a] for y in sources[b]))
                increase=v-baseline;maximum_increase=max(maximum_increase,increase)
                row={'pair':[a,b],'overlap_mm3':v,'O16_same_pair_overlap_mm3':baseline,'increase_mm3':increase}
                findings.append(row)
                if increase>.001:new_bad.append({'pose':name,**row})
        results.append({'pose':name,'new_part_bbox_pairs_checked':tested,'findings':findings});print('POSE',name,'findings',len(findings),'new',len(new_bad),flush=True)
    assert neutral and neutral['height_mm']<=600
    services=change['service_checks'];badservice=[r for r in services if r.get('maximum_overlap_with_latch_released_mm3',0)>1e-4 or r.get('installed_pcba_overlap_mm3',0)>1e-4 or r.get('maximum_open_path_overlap_mm3',0)>1e-4]
    assert not badservice,badservice
    oldprofile=read(H/'bench/revO16/profiles/device_profile.json');newprofile=read(BENCH/'profiles/device_profile.json')
    fields=['root_transform_mm','joints','fixed_markers','raw_order','raw_limits_deg','neutral_raw_deg']
    assert all(oldprofile[k]==newprofile[k] for k in fields)
    report={'status':'REGRESSION_PASS_WITH_INHERITED_OVERLAPS' if not new_bad else 'NEW_COLLISIONS_FOUND','scope':'New printable geometry against O16 in 24 discrete cases (23 poses plus assembly); NOT full-domain or tether collision certification',
        'neutral_exact_geometry':neutral,'new_print_roundtrip':export_checks,'service_checks_passed':len(services),
        'inherited_overlap_cases':sum(bool(r['findings']) for r in results),'manufacturing_release':False,'poses':results,'new_collisions':new_bad,'maximum_overlap_increase_mm3':maximum_increase,'overlap_regression_tolerance_mm3':.001,
        'kinematic_profile_unchanged_fields':fields,'raw_channels':46,'physical_tested':False,'ue_end_to_end_tested':False,'continuous_collision_proof':False,
        'nominal_parametric_vs_old_tessellation_added_mm3_max':max(r['added_outside_old_mm3'] for r in replacement.values()),
        'sources_sha256':{p.name:sha(p) for p in [Path(__file__),OUT/'changed_parts.npz',OUT/'changes.json',BENCH/'print_batch/manifest.json',BENCH/'profiles/device_profile.json']}}
    write(OUT/'geometry_verification.json',report);print(report['status'],'height',neutral['height_mm'],'new collisions',len(new_bad),flush=True)
    if new_bad:raise SystemExit(1)
if __name__=='__main__':main()
