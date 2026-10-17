"""Evaluate retained internal PCB-post ribs against the actual O22 assembly.
All input/model writes are redirected to this F3 experiment.
"""
import json,shutil,sys
import numpy as np
from pathlib import Path
from explore_revo22_f3 import R,B,O,solid,union,box,vf,audit
import manifold3d as md
import build_revo22_assembly as assembly

def H(rot,tr):
    out=np.eye(4);out[:3,:3]=rot;out[:3,3]=tr;return out

if __name__=='__main__':
    src=O/'candidates/X046'/(sys.argv[1] if len(sys.argv)>1 else 'distributed_box');dst=O/'candidates/X046'/(sys.argv[2] if len(sys.argv)>2 else 'post_ribs')
    for d in ['parts','design','verification']:(dst/d).mkdir(parents=True,exist_ok=True)
    scratch=R/'.local/o22-fins-v3/assembly_readonly_copy';scratch.mkdir(parents=True,exist_ok=True)
    for name in ['sensor_fit.json','end_axis_fit.json','sensor_cassettes.npz','end_axis_parts.npz']:
        target=scratch/name
        if not target.exists():shutil.copy2(B/'mechanical'/name,target)
    assembly.D=scratch;assembly.b.D=scratch
    parts,meta,raw,changed,service,C=assembly.model()
    n=dict(np.load(src/'parts/X046.npz'));r=json.loads((src/'design/X046.json').read_text());old=solid(n['v'],n['f'])
    A=np.array(meta['frame/chest']['transform']);A[:3,1]*=1 if np.linalg.det(A[:3,:3])>0 else -1
    bed=next(x['bed'] for x in json.loads((B/'print_batch/manifest.json').read_text())['rows'] if x['id']=='X046')
    print_from_world=H(np.array(r['orientation']['matrix']),r['orientation']['source_translation_mm'])@H(np.array(bed['rotation']),bed['translation_mm'])@np.linalg.inv(A)
    print_from_box=print_from_world@C
    ribs=[]
    for y in [3,91]:
        ribs.append(box([-1.05,y-.7,1.95],[1.2,y+.7,5.0]))
        # Rear pair: long root provides a sloping underside in the selected print pose.
        poly=np.array([[65,1.95],[76,1.95],[75.6,5],[74.0,5]])
        prism=md.CrossSection([poly]).extrude(1.4).rotate([90,0,0]).translate([0,y+.7,0])
        ribs.append(prism)
    ribs_local=union(ribs)
    ribs_print=ribs_local.transform(print_from_box[:3,:])
    new=old+ribs_print;delta=new-old;delta_local=delta.transform(np.linalg.inv(print_from_box)[:3,:]);delta_world=delta.transform(np.linalg.inv(print_from_world)[:3,:])
    fits=[]
    bb=np.array(delta_world.bounding_box())
    for key,s in parts.items():
        if key=='frame/chest':continue
        sb=np.array(s.bounding_box())
        if np.any(np.minimum(bb[3:],sb[3:])<=np.maximum(bb[:3],sb[:3])+1e-7):continue
        overlap=max(0.,float((delta_world^s).volume()))
        if overlap>1e-7:fits.append({'part':key,'added_overlap_mm3':overlap})
    holes=union([md.Manifold.cylinder(8,1.,1.,64).translate([x,y,-1]) for x in [3,77] for y in [3,91]])
    safe_box=box([-1,-1,1.999999],[81,95,5.000001])
    fins=solid(n['fin_v'],n['fin_f']);teeth=solid(n['teeth_v'],n['teeth_f'])
    original_fin_collision=float((fins^new).volume())
    # Remove the upward shadow of the new permanent ribs from removable fins.
    # A removed upper fragment is never reclassified as a bed-rooted support.
    shadows=[]
    for rib in ribs:
        rv,_=vf(rib.transform(print_from_box[:3,:]))
        offsets=np.array([[x,y,z] for x in [-.3,.3] for y in [-.3,.3] for z in [-.3,180.]])
        shadows.append(md.Manifold.hull_points((rv[:,None,:]+offsets[None,:,:]).reshape(-1,3)))
    fins=fins-union(shadows)
    fins=union([c for c in fins.decompose() if c.bounding_box()[2]<1e-6])
    teeth=union([c for c in teeth.decompose() if (c^fins).volume()>.005 and (c^new).volume()>.005])
    fins=union([c for c in fins.decompose() if (c^teeth).volume()>.005])
    kept=[]
    for rec in r['teeth']:
        bb=rec['bounds_mm'];q=teeth^box(bb[:3],bb[3:])
        if q.volume()>.005:
            rec['part_bite_mm3']=float((q^new).volume());rec['fin_root_mm3']=float((q^fins).volume());kept.append(rec)
    r['teeth']=kept
    n.update(fin_v=vf(fins)[0],fin_f=vf(fins)[1],teeth_v=vf(teeth)[0],teeth_f=vf(teeth)[1])
    reference=parts['frame/chest'].transform(print_from_world[:3,:])
    reference_delta=float(((reference-old)+(old-reference)).volume())
    report={'original_assembly_source_symmetric_difference_mm3':reference_delta,'fin_collision_before_regeneration_mm3':original_fin_collision,'remaining_design_teeth':len(kept),'change':'retained internal PCB-post gussets','added_volume_mm3':float(delta.volume()),'removed_volume_mm3':float((old-new).volume()),
        'added_outside_internal_below_PCB_compartment_mm3':float((delta_local-safe_box).volume()),
        'added_in_M2_clearance_cylinders_mm3':float((delta_local^holes).volume()),'actual_assembly_added_intersections':fits,
        'new_fin_body_intersection_mm3':float((fins^new).volume()),'old_new_bounds_equal':bool(np.allclose(old.bounding_box(),new.bounding_box(),atol=1e-7)),
        'motion_scope':'All added material is inside the existing enclosure below the fixed PCB; no external envelope, joint axis, mount datum, or stop changes. Existing assembly geometry used for electronics and screw checks. Not an elastic/fatigue or continuous motion simulation.',
        'static_assembly_part_count':len(parts),'physical_tested':False}
    report['geometric_fit_pass']=reference_delta<.01 and not fits and report['added_outside_internal_below_PCB_compartment_mm3']<1e-5 and report['added_in_M2_clearance_cylinders_mm3']<1e-6 and report['new_fin_body_intersection_mm3']<1e-6
    (dst/'verification/body_change_fit.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps(report,indent=2),flush=True)
    n['source_f']=n['f'].copy();n['v'],n['f']=vf(new)
    n['added_body_v'],n['added_body_f']=vf(delta)
    np.savez_compressed(dst/'parts/X046.npz',**n)
    r.update(support_volume_mm3=float((fins+teeth).volume()),source_mesh_preserved=False,body_change=report,body_change_kind='internal_post_gussets',body_part_overlap_mm3=report['new_fin_body_intersection_mm3'])
    (dst/'design/X046.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
    if report['geometric_fit_pass']:audit('X046',dst)

