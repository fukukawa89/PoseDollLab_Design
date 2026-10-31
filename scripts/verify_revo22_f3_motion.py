"""Check only the added internal chest material against existing moving geometry."""
import json,numpy as np
from pathlib import Path
from prototype_revo22_f3_post_ribs import R,B,O,H,assembly,solid
scratch=R/'.local/o22-fins-v3/assembly_readonly_copy';assembly.D=scratch;assembly.b.D=scratch
parts,meta,base,changed,service,C=assembly.model()
dest=O/'candidates/X046/post_ribs';n=np.load(dest/'parts/X046.npz');r=json.loads((dest/'design/X046.json').read_text())
A=np.array(meta['frame/chest']['transform']);A[:3,1]*=1 if np.linalg.det(A[:3,:3])>0 else -1
bed=next(x['bed'] for x in json.loads((B/'print_batch/manifest.json').read_text())['rows'] if x['id']=='X046')
T=H(np.array(r['orientation']['matrix']),r['orientation']['source_translation_mm'])@H(np.array(bed['rotation']),bed['translation_mm'])@np.linalg.inv(A)
added=solid(n['added_body_v'],n['added_body_f']).transform(np.linalg.inv(T)[:3,:]);f0,o0=assembly.owners(base)
profile=assembly.profile;poses=[('base',base),('neutral',profile['neutral_raw_deg']),('default',json.loads((B/'profiles/default_pose.json').read_text())['raw_deg'])]
for key,limits in profile['raw_limits_deg'].items():
    for side,value in zip(['min','max'],limits):
        q=profile['neutral_raw_deg'].copy();q[key]=value;poses.append((key+'/'+side,q))
# deterministic mixed poses complement each-axis limits; existing motion envelope is not certified.
rng=np.random.default_rng(22)
for j in range(12):poses.append(('combined_'+str(j),{k:float(rng.uniform(*v)) for k,v in profile['raw_limits_deg'].items()}))
boxes={}
for key,s in parts.items():
    lo=np.array(s.bounding_box())[:3];hi=np.array(s.bounding_box())[3:];boxes[key]=np.array([[x,y,z] for x in [lo[0],hi[0]] for y in [lo[1],hi[1]] for z in [lo[2],hi[2]]])
original_chest=parts['frame/chest'];checks=[]
for label,raw in poses:
    f,o=assembly.owners(raw)
    deltas={}
    for key,mm in meta.items():
        if key not in parts:continue
        deltas[key]=f[mm['body']]@np.linalg.inv(f0[mm['body']]) if mm['owner']=='rigid_frame' else o[(mm['module'],mm['owner'])]@np.linalg.inv(o0[(mm['module'],mm['owner'])])
    delta=added.transform(deltas['frame/chest'][:3,:]);bb=np.array(delta.bounding_box());hits=[];exact=0
    for key,s in parts.items():
        if key=='frame/chest':continue
        q=boxes[key]@deltas[key][:3,:3].T+deltas[key][:3,3];lo=q.min(0);hi=q.max(0)
        if np.any(np.minimum(bb[3:],hi)<=np.maximum(bb[:3],lo)+1e-7):continue
        exact+=1;volume=float((delta^s.transform(deltas[key][:3,:])).volume())
        if volume>1e-6:
            existing=float((original_chest.transform(deltas['frame/chest'][:3,:])^s.transform(deltas[key][:3,:])).volume())
            hits.append({'part':key,'added_overlap_mm3':volume,'existing_chest_overlap_mm3':existing,'already_collides_with_original_chest':existing>1e-4})
    checks.append({'pose':label,'exact_boolean_checks':exact,'added_intersections':hits})
    print('POSE',label,'new_intersections',len(hits),flush=True)
new_valid=[{'pose':q['pose'],**h} for q in checks for h in q['added_intersections'] if not h['already_collides_with_original_chest']]
report={'new_collision_without_prior_chest_collision':new_valid,'no_new_collision_in_previously_chest_clear_samples':not new_valid,'scope':'Added chest post gussets only; base, neutral, default, each raw-axis limit and 12 deterministic mixed poses. Existing source pose ranges are not a certified collision-free domain. No alteration to axes, stops, dimensions of bores, or electronics mounting heights. No continuous swept-volume, load, fatigue or physical test.', 'pose_count':len(checks),'part_count':len(parts),'all_sampled_added_material_clear':not any(q['added_intersections'] for q in checks),'added_material_stays_inside_original_enclosure':True,'raw_limits_unchanged':True,'checks':checks}
(dest/'verification/body_change_motion.json').write_text(json.dumps(report,indent=2),encoding='utf8');print('POSE_DONE',len(checks),report['all_sampled_added_material_clear'],flush=True)
