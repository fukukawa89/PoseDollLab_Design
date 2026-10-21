"""Export the actual O23 meshes for rendering and an offline WebGL viewer."""
from build_revo23 import *
import gzip,base64
import shutil

COLORS={'structure':[.79,.78,.71], 'frame':[.14,.19,.20], 'metal':[.32,.36,.39],
        'sensor':[.10,.33,.25], 'print':[.19,.25,.26], 'other':[.19,.25,.26]}

def load_current():
    document=read(B/'assembly.json');n=np.load(B/'assembly.npz'); parts={}
    for p in document['items']:
        i=str(p['index']);parts[p['key']]=dict(p,s=solid(n[i+'v'],n[i+'f']))
    return parts

def main():
    parts=load_current();p=read(B/'profiles/device_profile.json');default=read(B/'profiles/default_pose.json')['raw_deg']
    # Once an export has passed the independent checks, render its exact
    # printable surface instead of CAD's zero-thickness Boolean residue.
    display_exports={}
    manifest=B/'verification/export_formats.json'
    if manifest.exists():
        exported=read(manifest)
        if exported.get('geometry_sha256')==sha(B/'assembly.npz') and not exported.get('stl_failures'):
            for row in exported['rows']:
                if not row.get('review_stl'):continue
                path=B/row['review_stl'];assert sha(path)==row['stl_sha256']
                mesh=trimesh.load(path,process=True)
                parts[row['key']]['s']=solid(mesh.vertices,mesh.faces)
                display_exports[row['key']]=row['stl_sha256']
    poses={'A':default,'N':p['neutral_raw_deg']}
    for name in ('left_elbow','asymmetric','right_forearm'):
        poses[name]=read(H/'bench/revO22/ue'/f'{name}.payload.json')['joint_angles_deg']
    if (B/'profiles/daily_poses.json').exists():
        daily=read(B/'profiles/daily_poses.json')['poses']
        for name in list(poses):poses[name]=daily[{'A':'A_STAND_35','N':'N_NEUTRAL'}.get(name,name)]
        for name in ('daily_seated','daily_reach_front','daily_carry_front','daily_shallow_squat','daily_step'):
            poses[name]=daily[name]
    output={};catalog=[];vertex=[];offset=0
    for key,part in parts.items():
        v,f=vf(part['s']);i=str(part['index']);output[i+'v']=v;output[i+'f']=f
        role=part['role'];color=COLORS.get(role,COLORS['other']);t=v[f]
        n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-15)
        g=np.concatenate([t,np.repeat(n[:,None,:],3,axis=1)],axis=2).reshape(-1,6).astype('<f4')
        vertex.append(g);catalog.append(dict(index=part['index'],key=key,role=role,color=color,
            first=offset,count=len(g),token=part['token'],local_center=((v.min(0)+v.max(0))/2).tolist(),view_span=float(np.linalg.norm(np.ptp(v,axis=0))*1.25)));offset+=len(g)
    transforms={}
    for name,q in poses.items():
        ff=frames(p,q);transforms[name]={k:v.flatten().tolist() for k,v in ff.items()}
    put(B/'preview/scene.json',dict(items=catalog,poses=transforms,colors=COLORS))
    geometry=np.concatenate(vertex).tobytes();(B/'preview/geometry.bin').write_bytes(geometry)
    # Script payload allows file:// usage without fetch/CORS or a server.
    encoded=base64.b64encode(gzip.compress(geometry,compresslevel=6)).decode()
    verification=read(B/'verification/geometry.json')
    motion=read(B/'verification/daily_motion.json')
    edge=read(B/'verification/edge_paths.json')
    current_hash=sha(B/'assembly.npz')
    assert verification['geometry_sha256']==current_hash,'Check current geometry before presenting it.'
    quick_current=motion['geometry_sha256']==current_hash
    review=dict(revision=REV,height_mm=verification['geometry']['height_mm'],
        structures=sum(x['role']=='structure' for x in catalog),invalid=len(verification['geometry']['invalid_parts']),
        daily_contacts=len(motion['blocking_contacts'])if quick_current else None,
        daily_poses=motion['pose_count']if quick_current else None,
        transition_poses=edge['pose_count'] if edge['geometry_sha256']==current_hash else None,
        transition_contacts=len(edge['blocking_contacts']) if edge['geometry_sha256']==current_hash else None,
        nonadjacent_advisories=len(motion['nonadjacent_advisory'])if quick_current else None,
        a_contacts=sum(x['pose']=='A_STAND_35'for x in motion['blocking_contacts'])if quick_current else None,
        upper_torso_raise_mm=p['o23_design'].get('upper_torso_raise_mm',0),
        geometry_sha256=current_hash,manufacturing_release=False)
    hip=read(B/'verification/hip_centers.json')
    review['actual_hip_spacing_mm']=hip['physical_center_spacing_mm']
    review['hip_target_error_mm']=max(x['error_mm'] for x in hip['hip_centers'])
    count_path=B/'verification/physical_rod_count.json'
    if count_path.exists():
        counts=read(count_path)
        if counts.get('geometry_sha256')==current_hash and counts['passed']:
            review['maximum_rods_per_adjacent_component']=counts['maximum_rods_per_adjacent_component']
            review['explicit_rod_count']=sum(r['rods'] for r in counts['rows'])
    review['pose_contacts']={}
    for pose in poses:
        label={'A':'A_STAND_35','N':'N_NEUTRAL'}.get(pose,pose)
        hits=[x for x in motion['blocking_contacts']if x['pose']==label]if quick_current else []
        advisory=[x for x in motion['nonadjacent_advisory']if x['pose']==label]if quick_current else []
        review['pose_contacts'][pose]=dict(count=len(hits)if quick_current else None,
            affected_keys=sorted({k for x in hits for k in x['pair']}),
            advisory_count=len(advisory)if quick_current else None,
            advisory_keys=sorted({k for x in advisory for k in x['pair']}))
    exports=read(B/'verification/export_formats.json')if(B/'verification/export_formats.json').exists()else None
    review['exports_by_key']={}
    if exports and exports['geometry_sha256']==current_hash:
        review['exports_by_key']={r['key']:r['review_3mf']for r in exports['rows']}
        review['stl_topology_failed_count']=len(exports['stl_failures'])
        review['stl_count']=len(exports['rows'])
        review['stl_slicing_verified']=exports.get('native_print_slicing_verified',False)
    harness=None
    if (B/'harness/routing_plan.json').exists():
        h=read(B/'harness/routing_plan.json')
        if h.get('geometry_sha256')==current_hash:
            channels=read(B/'harness/wire_channels.json')['rows']
            harness=dict(seats=h['seats'],channels=[r for r in channels if r['channel_open_in_actual_print']])
            review['wire_seat_count']=len(h['seats'])
    (B/'preview/data.js').write_text('window.O23='+json.dumps(dict(items=catalog,poses=transforms,geometry=encoded,review=review,harness=harness),separators=(',',':'))+';',encoding='utf8')
    np.savez_compressed(B/'preview/render_meshes.npz',**output)
    put(B/'preview/render_scene.json',dict(items=[dict(i=x['index'],key=x['key'],color=x['color'],role=x['role'],matrix=transforms['A'][x['token']]) for x in catalog],poses=transforms))
    for src in (H/'cad/revO23/web').iterdir():shutil.copy2(src,B/'preview'/src.name)
    # A reload of the HTML can otherwise retain an older cached geometry or
    # viewer script. Bind every asset URL to the actual bytes being delivered.
    assets={name:sha(B/'preview'/name) for name in ('data.js','viewer.js','style.css')}
    index=B/'preview/index.html';html=index.read_text(encoding='utf8')
    for name,digest in assets.items():html=html.replace('"'+name+'"','"'+name+'?v='+digest[:16]+'"')
    index.write_text(html,encoding='utf8');assets['index.html']=sha(index)
    put(B/'preview/provenance.json',dict(geometry_sha256=current_hash,profile_sha256=sha(B/'profiles/device_profile.json'),
        geometry_bin_sha256=sha(B/'preview/geometry.bin'),render_meshes_sha256=sha(B/'preview/render_meshes.npz'),
        asset_hashes=assets,review=review))
    if display_exports:
        path=B/'preview/provenance.json';record=read(path)
        record.update(render_source='Actual verified STL for exported printed parts; original CAD for retained hardware and electronics.',stl_sha256=display_exports)
        put(path,record)
    print('PREVIEW',len(catalog),'triangles',offset//3,flush=True)

if __name__=='__main__':main()
