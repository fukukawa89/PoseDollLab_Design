from pathlib import Path
import sys,json,numpy as np,shutil
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,vf,box
from inspect_revo22_f4_magnet_retention import assess
import repair_revo22_f4_guarded_chamfer as ctx
O=ctx.O;pid='P001';src=O/'candidates'/pid/'complete58_01';dst=O/'candidates'/pid/'control_loaded_face62'
for x in ['parts','design','verification']:(dst/x).mkdir(parents=True,exist_ok=True)
n=dict(np.load(src/'parts'/f'{pid}.npz'));d=json.loads((src/'design'/f'{pid}.json').read_text());parts,key,T=ctx.context(d,pid);bb=np.array(parts['waist/P_magnet_nut_-5.8'].bounding_box());cut=box([bb[0]-.01,bb[4]-.01,bb[2]-.01],[bb[3]+.01,bb[4]+.7,bb[5]+.01]).transform(T[:3,:]);body=solid(n['v'],n['f']);bad=body-cut;n['v'],n['f']=vf(bad);np.savez_compressed(dst/'parts'/f'{pid}.npz',**n);(dst/'design'/f'{pid}.json').write_text(json.dumps(d));a=assess(pid,'complete58_01');b=assess(pid,'control_loaded_face62');positive=all(q['qualified_magnet_retention_entry_relief'] for q in a);negative=not next(q for q in b if q['part']=='waist/P_magnet_nut_-5.8')['qualified_magnet_retention_entry_relief'];assert positive and negative
(O/'magnet_retention_controls.json').write_text(json.dumps({'actual_unloaded_entry_relief_qualified':positive,'intentional_loaded_wall_cut_rejected':negative,'negative_control_removed_volume_mm3':float((body-bad).volume()),'fixture_not_printable':True},indent=2));print('MAGNET_CONTROLS_PASS',flush=True)
