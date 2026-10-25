"""Transfer collision evidence only after exact per-feature containment proof.

If every new solid is a subset of its previously tested solid in the same frame,
no previously clear pair can acquire an intersection in any unchanged pose.
No load or connectivity result is transferred by this argument.
"""
from validate import *

def main():
    olddir=OUT/'history/face_relief_parent';old=load(olddir/'assembly.json');oz=np.load(olddir/'assembly_meshes.npz');parts,z,ss=read_assembly();before=sha(olddir/'assembly_meshes.npz');after=sha(OUT/'assembly_meshes.npz')
    for n in ['profiles/device_profile.json','profiles/poses.json']:
        if load(olddir/n)!=load(OUT/n):raise ValueError('Changed motion contract '+n)
    lookup={p['name']:p for p in old['parts']};rows=[]
    for p,s in zip(parts,ss):
        q=lookup[p['name']];assert q['frame']==p['frame'];i=str(q['i']);prior=md.Manifold(md.Mesh64(np.array(oz[i+'v'],copy=True,order='C'),np.array(oz[i+'f'],dtype=np.uint64,copy=True,order='C')))
        extra=(s-prior).volume();removed=(prior-s).volume();rows.append(dict(part=p['name'],new_material_outside_old_mm3=extra,removed_mm3=removed))
    maximum=max(r['new_material_outside_old_mm3'] for r in rows);ok=maximum<1e-6
    report=dict(status='PASS_EXACT_CONTAINMENT' if ok else 'FAIL',geometry_sha256=after,parent_geometry_sha256=before,max_outside_volume_mm3=maximum,removed_volume_mm3=sum(r['removed_mm3'] for r in rows),deleted_features=sorted(set(lookup)-{p['name'] for p in parts}),rows=rows,scope='Exact Manifold set-difference, 1e-6 mm3 numerical tolerance, unchanged rigid frames and pose contract. Only removal from previously tested solids. Therefore previous finite collision-free samples remain clear; no strength, stiffness or connectedness conclusion inherited.')
    put(OUT/'verification/material_removal_proof.json',report)
    if not ok:raise ValueError('Geometry contains added material; full collision rerun required')
    for name in ['rom_examination.json','rom_examination_dense.json','motion_named.json','motion_task_paths.json']:
        r=load(olddir/'verification'/name);assert r['geometry_sha256']==before and r['status'].startswith('PASS')
        r.update(geometry_sha256=after,verification_method='Original exhaustive finite samples plus exact per-feature removal containment',parent_geometry_sha256=before,containment_proof='material_removal_proof.json')
        put(OUT/'verification'/name,r)
    print('REMOVAL PROOF',ok,maximum,'removed',report['removed_volume_mm3'],flush=True)

if __name__=='__main__':main()
