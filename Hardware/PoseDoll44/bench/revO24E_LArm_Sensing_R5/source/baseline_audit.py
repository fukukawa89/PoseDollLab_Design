from check_geometry import *
from collections import Counter
from pose_bridge import transforms,AXES

def run():
    a,ss=saved();old,os=baseline();old_by={p['name']:(p,s) for p,s in zip(old,os)};rows=[];issues=[]
    for p,s in zip(a,ss):
        if len([c for c in s.decompose() if abs(c.volume())>.01])!=1:issues.append('Disconnected '+p['name'])
        if p.get('baseline_name') and not p.get('reprint'):
            op,o=old_by[p['name']];delta=(s-o).volume()+(o-s).volume()
            if abs(delta)>.001:issues.append('Changed reused '+p['name'])
            rows.append(dict(name=p['name'],symmetric_difference_mm3=delta))
    protected=[]
    for p,s in zip(a,ss):
        if not p.get('reprint'):continue
        op,orig=old_by[p['name']];removed=moved(orig-s,F0[p['frame']])
        near=[];outside_tessellation=removed-expanded(moved(s,F0[p['frame']]),.005)
        for hp,hs in zip(old,os):
            if hp['role']=='structure':continue
            if hp.get('sku') not in ['AX4','A8','FW4','W4','W6L']:continue
            w=moved(hs,F0[hp['frame']])
            if np.any(e.bounds(w)[0]>e.bounds(removed)[1]+.15) or np.any(e.bounds(w)[1]<e.bounds(removed)[0]-.15):continue
            v=(removed^expanded(w,.15)).volume()
            beyond=(outside_tessellation^expanded(w,.15)).volume()
            if v>.001:near.append(dict(hardware=hp['name'],sku=hp['sku'],mesh_difference_mm3=v,removed_beyond_0p005_mm_surface_tolerance_mm3=beyond))
        protected.append(dict(name=p['name'],removed_near_original_load_hardware=near))
        if any(r['removed_beyond_0p005_mm_surface_tolerance_mm3']>.001 for r in near):issues.append('Load face check '+p['name'])
    # Independent Rodrigues bridge is compared to the inherited kinematics.
    worst=0
    for _,q in named_poses():
        full={a['id']:q.get(a['id'],0) for a in PROFILE['axes']};expected=frames(full)
        for row in transforms(full,PROFILE):worst=max(worst,float(np.max(abs(np.array(row['world_matrix_mm'])-expected[row['frame']]))))
    if worst>1e-8:issues.append('Angle chain mismatch')
    kit=load(OUT/'kit.json');guide=load(OUT/'assembly_guide/steps.json');seen={p for st in guide['steps'] for p in st['visible']};missing={p['part_number'] for p in a}-seen
    if missing:issues.append('Missing guide parts '+str(missing))
    plates=load(OUT/'printing/plates.json')['plates'];printed=[p['id'] for pl in plates if not pl['optional'] for p in pl['items']]
    expected={p['part_number'] for p in kit['structural_parts'] if p.get('reprint') or p['new_accessory']}|{'R5-J003','R5-J004'}
    if set(printed)!=expected or len(printed)!=len(expected):issues.append('Print plate coverage')
    result=dict(passed=not issues,issues=issues,geometry_sha256=sha(OUT/'production_meshes.npz'),baseline_sha256=sha(BASE/'production_meshes.npz'),roles=dict(Counter(p['role'] for p in a)),unchanged_bodies=rows,protected_load_regions=protected,bridge_max_matrix_error=worst,guide_coverage=len(seen&{p['part_number'] for p in a}),upgrade_print_count=len(printed),limits='0.15 mm neighborhoods of original load hardware checked for removed material. This is a geometry audit, not stiffness/creep qualification.')
    put(OUT/'verification/baseline_audit.json',result);print('BASELINE',result['passed'],issues,'BRIDGE',worst,flush=True)
    for r in protected:print(r,flush=True)

if __name__=='__main__':run()

