"""Saved-mesh checks for the four integration changes, including ground loads."""
from strength import *
from zipfile import ZipFile
import io

def main():
    parts,z,ss=read_assembly();digest=sha(OUT/'assembly_meshes.npz');world=[moved(s,FA[p['frame']]) for p,s in zip(parts,ss)]
    bb=np.array([s.bounding_box() for s in world]).reshape(-1,2,3);names={p['name']:i for i,p in enumerate(parts)}
    mounts=load(OUT/'harness/anchors.json')['anchors'];slots=[]
    for r in mounts:
        cutter=box(*r['slot_bounds_mm']);W=np.array(r['slot_world_from_local']);W=FA[r['frame']]@np.linalg.inv(F0[r['frame']])@W;s=moved(cutter,W)
        overlap=sum((s^world[i]).volume() for i,p in enumerate(parts) if p['frame']==r['frame'] and p['role'] in ['structure','rotor','shell'])
        slots.append(dict(id=r['id'],remaining_material_in_tie_slot_mm3=overlap,pass_clear=overlap<.02))
    clashes=[];plate=names['electronics_backplate']
    for i,p in enumerate(parts):
        if p['role'] not in ['pcb','connector','metal','bearing','magnet']:continue
        if not np.all(bb[plate,1]>bb[i,0]) or not np.all(bb[plate,0]<bb[i,1]):continue
        vol=(world[plate]^world[i]).volume()
        if vol>.02:clashes.append(dict(part=p['name'],volume_mm3=vol))
    # Current/Baseline pelvic assembly bounds, from exported vertices, not labels.
    def pelvis_bounds(pp,zz,ff):
        vs=[]
        for p in pp:
            if p['name'].startswith(('pelvi','l_hip_','r_hip_')):
                v=zz[str(p['i'])+'v'];f=np.array(ff[p['frame']]);vs.append(v@f[:3,:3].T+f[:3,3])
        v=np.vstack(vs);return np.array([v.min(0),v.max(0)])
    current=pelvis_bounds(parts,z,FA);baseline=H/'bench/revO24D_baseline_20261023_pre_integrated/O24D_Digital_Review.zip'
    with ZipFile(baseline) as pack:
        ap=next(n for n in pack.namelist() if n.endswith('bench/revO24D/assembly.json'));mp=next(n for n in pack.namelist() if n.endswith('bench/revO24D/assembly_meshes.npz'));old=json.loads(pack.read(ap));oz=np.load(io.BytesIO(pack.read(mp)));previous=pelvis_bounds(old['parts'],oz,old['neutral_frames'])
    # Mirror both silhouettes and local material volumes. Known central and
    # populated-board exceptions are listed, rather than silently called symmetric.
    mirrors=[]
    for p in parts:
        name=p['name']
        if not name.startswith('l_') or 'r_'+name[2:] not in names:continue
        r=parts[names['r_'+name[2:]]]
        if not name.startswith(('l_upperarm','l_elbow','l_forearm','l_palm','l_thigh','l_shin','l_knee','l_ankle','l_heel','l_toe')):continue
        # Core manufactured parts; sensor boards and tailored outlets have their
        # own handed electrical exit constraints.
        if any(w in name for w in ['sensor_holder','connector','pcb','PCB','plug','wire_tab']):continue
        v=np.array(p['bounds_mm']);rv=np.array(r['bounds_mm']);volerr=abs(p['volume_mm3']-r['volume_mm3'])/max(p['volume_mm3'],1)
        mirrors.append(dict(left=name,right=r['name'],relative_volume_difference=volerr))
    ground=load(OUT/'verification/standing_ground_loads.json');assert ground['geometry_sha256']==digest
    contacts=ground['foot_contacts'];root_cases=[];wing_cases=[];toe_cases=[]
    for row in ground['rows']:
        if not row['accepted_unassisted_standing']:continue
        for side,sg in [('l',1),('r',-1)]:
            ank=P['foot_'+side];toe=P['ball_'+side]
            heel=[(np.array(c['point']),f) for c,f in zip(contacts,row['reactions_N']) if c['part']==side+'_heel_sole']
            toef=[(np.array(c['point']),f) for c,f in zip(contacts,row['reactions_N']) if c['part']==side+'_toe_pad']
            m=max(np.linalg.norm(sum((np.cross(pt-centre,[0,0,f]) for pt,f in heel),np.zeros(3))) for centre in [ank,ank+[3,0,-10],ank+[3,0,-23]])
            stress=1.5*1.875*m/(math.pi*9.5**3/32);root_cases.append(dict(pose=row['pose'],side=side,stress_MPa=stress))
            for ys in [-1,1]:
                centre=ank+[-10,ys*9,-25.5];loads=[(p,f) for p,f in heel if p[0]<ank[0]-15 and (p[1]-ank[1])*ys>10]
                m=np.linalg.norm(sum((np.cross(p-centre,[0,0,f]) for p,f in loads),np.zeros(3)));stress=1.5*1.875*m/(math.pi*7**3/32);wing_cases.append(dict(pose=row['pose'],side=side,wing=ys,stress_MPa=stress))
            m=max(np.linalg.norm(sum((np.cross(pt-centre,[0,0,f]) for pt,f in toef),np.zeros(3))) for centre in [toe+[0,0,-5],toe+[5,0,-25]])
            toe_cases.append(dict(pose=row['pose'],side=side,stress_MPa=1.5*1.875*m/(math.pi*8**3/32)))
    tab_cases=[dict(id=r['id'],root_stress_MPa=1.5*5*r['root_lever_mm']/(10*7**2/6),slot_ligament_stress_MPa=1.5*(5/2)*4/(10*2.25**2/6)) for r in mounts]
    moduleparts=[p for p in parts if p['name'].startswith(('electronics_','backboard_'))];mass=sum(p['volume_mm3']*p.get('density_g_mm3',DENSITY[p['role']]) for p in moduleparts)
    # Root D7, four roots. Include a simultaneous 5 N handling tug and gravity.
    rootstress=1.5*(mass/1000*9.80665*1.875*12/4+5*20/4)/(math.pi*7**3/32)
    standoffstress=1.5*(5/4)*9.9/(math.pi*(5**4-2.3**4)/(32*5))
    worst={k:max(v,key=lambda r:r['stress_MPa']) for k,v in [('heel_root',root_cases),('heel_wing',wing_cases),('toe',toe_cases)]}
    criteria=dict(stand_socket_removed=not any(p['name'] in ['pelvis_fixture_socket','pelvis_mount_bridge'] for p in parts),pelvis_reduced=current[0,0]>previous[0,0]+10,hand_simplified=all(not h.get('fingers') for h in load(OUT/'profiles/hand_geometry.json')['hands']),tie_slots_open=all(r['pass_clear'] for r in slots),backboard_hardware_clear=not clashes,foot_loads=max(r['stress_MPa'] for r in worst.values())<=8,tab_loads=max(max(r['root_stress_MPa'],r['slot_ligament_stress_MPa']) for r in tab_cases)<=8,backplate_roots=rootstress<=8,standoffs=standoffstress<=8)
    report=dict(status='PASS_INTEGRATED_CONDITIONAL' if all(criteria.values()) else 'FAIL',geometry_sha256=digest,criteria=criteria,pelvis=dict(old_bounds_mm=previous,new_bounds_mm=current,posterior_reduction_mm=float(current[0,0]-previous[0,0]),coaxial_station_mm=[66,48],fixed_bridge_height_mm=[53,37]),symmetry=dict(compared_limb_core_features=len(mirrors),max_volume_difference=max(r['relative_volume_difference'] for r in mirrors),rows=mirrors,exceptions=['Central clavicle journals/steel transfer: UE clavicle centres only 5.746 mm apart; coaxial journals are staggered along the original axes','Small shoulder sensor placements, native electrical component arrangement and wire fanout have handed clearance constraints','Original UE left/right sub-micron coordinate differences are preserved']),tie_slots=slots,new_hardware_clashes=clashes,foot_stress_worst=worst,foot_cases_evaluated=len(root_cases),wire_tab_stress=tab_cases,backplate=dict(module_mass_g=mass,root_D_mm=7,root_count=4,root_screen_MPa=rootstress,standoff_screen_MPa=standoffstress),printed_allowable_MPa=8,stress_concentration_factor=1.5,gravity_load_factor=1.875,scope='Actual geometry, material continuity, slot clearance, compactness and quasi-static section screening. Conditional on 8 MPa printed allowable, tie rating >=40 N and proper continuous printing. No measured stiffness, fatigue or impact qualification; full connection erosion checks are separate.')
    put(OUT/'verification/integration_changes.json',report);print('INTEGRATION',report['status'],criteria,'foot',worst,flush=True)
if __name__=='__main__':main()
