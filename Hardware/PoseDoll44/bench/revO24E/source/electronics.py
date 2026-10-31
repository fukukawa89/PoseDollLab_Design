"""Preserve 38 sensor boards, update wrist endpoints, recheck A routing and slack."""
from verify import *
import harness as router_module
import shutil

def main():
    parts=read_saved();digest=sha(OUT/'assembly_meshes.npz');route=load(BASE/'harness/routes.json')
    router_module.FA=FA
    router=router_module.Router(parts,[p['s'] for p in parts]);nodes={n['id']:n for n in route['nodes']}
    for side in ['l','r']:
        n=nodes['sensor_'+side+'_wrist'];M=np.array(next(w for w in load(OUT/'profiles/wrists.json') if w['side']==side)['mirror'])
        local=(np.linalg.inv(F0[side+'_forearm_roll'])@F0[side+'_wrist_flex']@M@np.array([0,29,-7,1]))[:3]
        n.update(local_mm=local.tolist(),ignore=side+'_E_wrist_connector')
        n['A']=(FA[n['frame']]@np.r_[local,1])[:3].tolist()
        n['direction_A']=(FA[side+'_wrist_flex'][:3,:3]@M[:3,:3]@np.array([0,1,0])).tolist()
    poses={n:p['angles'] for n,p in load(OUT/'profiles/poses.json').items()}
    for ax in PROFILE['axes']:
        for q in np.linspace(*ax['limits_deg'],21):poses[ax['id']+'/'+str(q)]={**base.NEUTRAL_ANGLES,ax['id']:float(q)}
    FF=[(name,frames(q)) for name,q in poses.items()];checks=[];lumps=[];scene=trimesh.Scene()
    for s in route['spans']:
        start,end=nodes[s['start']],nodes[s['end']];pts=np.array(s['guide_A_mm']);pts[0]=start['A'];pts[-1]=end['A'];r=s['diameter_mm']/2
        ignore=[x.get('ignore','') for x in [start,end]]
        good=all(router.clear(a,b,r,ignore) for a,b in zip(pts[:-1],pts[1:]))
        reroute=False;error=None
        if not good:
            try:pts=router.route(start,end,r);good=True;reroute=True
            except Exception as e:error=str(e)
        length=float(np.linalg.norm(np.diff(pts,axis=0),axis=1).sum());worst=0;worstname=''
        for name,F in FF:
            a=(F[start['frame']]@np.r_[start['local_mm'],1])[:3];b=(F[end['frame']]@np.r_[end['local_mm'],1])[:3];dd=float(np.linalg.norm(b-a))
            if dd>worst:worst=dd;worstname=name
        bend=route['minimum_dynamic_bend_radius_mm'];reserve=2*math.pi*bend+12 if start['frame']!=end['frame'] else 15
        cut=math.ceil(max(length+15,worst+reserve,s['cut_length_per_cable_mm'])/5)*5
        s.update(guide_A_mm=pts.tolist(),guide_length_mm=length,cut_length_per_cable_mm=cut,max_endpoint_distance_mm=worst,worst_extension_pose=worstname,reserve_over_max_distance_mm=cut-worst,A_CSG_clear=good)
        checks.append(dict(span=s['id'],status='PASS_A_ROUTE' if good else 'FAIL',rerouted=reroute,error=error,max_distance_mm=worst,cut_per_cable_mm=cut,guide_length_mm=length))
        mass=cut*len(s['cables'])*route['mass_assumption_g_per_mm_of_6_core']
        for n in [start,end]:lumps.append(dict(frame=n['frame'],local_mm=n['local_mm'],mass_g=mass/2,source=s['id']))
        for i,(a,b) in enumerate(zip(pts[:-1],pts[1:])):
            if np.linalg.norm(a-b)<1e-7:continue
            vv,ff=base.a.mesh_data(beam(a,b,r));m=trimesh.Trimesh(vv*.001,ff,process=False);m.visual.vertex_colors=[50,70,90,255];scene.add_geometry(m,node_name=s['id']+'/'+str(i))
        print('WIRE',s['id'],good,reroute,flush=True)
    route.update(geometry_sha256=digest,status='PASS_A_ROUTES_SLACK_BUDGET' if all(r['status']=='PASS_A_ROUTE' for r in checks) else 'REVIEW_REQUIRED',motion_cases=len(FF),nodes=list(nodes.values()),
        total_wire_mass_g=sum(x['mass_g'] for x in lumps),scope='Actual E fixed A-pose swept cable envelopes and 870 finite endpoint samples; flexible intermediate sweep, bend-radius deformation, pinching and fatigue remain physical acceptance items.')
    put(OUT/'harness/routes.json',route);put(OUT/'harness/mass_lumps.json',dict(geometry_sha256=digest,lumps=lumps))
    scene.export(OUT/'harness/O24E_wire_guides_A.glb')
    put(OUT/'verification/harness.json',dict(geometry_sha256=digest,status=route['status'],rows=checks,dynamic_pinching_verified=False))
    with (OUT/'harness/CABLE_CUTLIST.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f);w.writerow(['span','start','end','cables','qty','cut_mm_each','extra_over_max_distance_mm'])
        for s in route['spans']:w.writerow([s['id'],s['start'],s['end'],';'.join(s['cables']),len(s['cables']),s['cut_length_per_cable_mm'],s['reserve_over_max_distance_mm']])
    dest=OUT/'electronics/inherited_D';dest.mkdir(parents=True,exist_ok=True)
    for sub in ['carrier','sensors']:shutil.copytree(BASE/'electronics'/sub,dest/sub,dirs_exist_ok=True)
    files={p.relative_to(dest).as_posix():sha(p) for p in dest.rglob('*') if p.is_file()}
    put(OUT/'electronics/pcb_reuse_manifest.json',dict(files=files,changes_to_pcb=0,sensor_boards=38,single_axis_boards=36,wrist_field_boards=2,raw_scalars=42,physical_dof=40,calibration_reused=False))
    put(OUT/'electronics/integration.json',dict(geometry_sha256=digest,boards=38,raw_scalars=42,wrist='Two fixed-side TMAG5170 boards, each sees one keyed moving dipole; updated bounded Ry@Rx calibration mandatory',wire_across_wrist_axes=False,pcb_native_files='inherited_D',ERC_DRC='Existing D board routing unchanged by hash; no new electrical hardware result claimed',full_power_on_test=False,magnetic_steel_interference_test=False))

if __name__=='__main__':main()
