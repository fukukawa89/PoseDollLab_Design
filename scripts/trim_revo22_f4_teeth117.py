"""Trim the temporary teeth to growth reachable from bed-rooted fins alone.
The permanent part and all functional surfaces are unchanged.
"""
from pathlib import Path
import sys,json,numpy as np,shutil,time
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,vf,box,union,md
from o22_material_components import material_components
from verify_revo22_f4_portal_layers import check as growth
from verify_revo22_f4_repaired_geometry import check as geom
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
from refine_revo22_f4_lateral104 import check as refine
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def trial(pid,parent,label):
 src=O/'candidates'/pid/parent;dst=O/'candidates'/pid/label
 for sub in ['parts','design','verification']:(dst/sub).mkdir(parents=True,exist_ok=True)
 n=dict(np.load(src/'parts'/f'{pid}.npz'));d=json.loads((src/'design'/f'{pid}.json').read_text());s=solid(n['v'],n['f']);fin=solid(n['fin_v'],n['fin_f']);old=solid(n['teeth_v'],n['teeth_f']);h=max(old.bounding_box()[5],fin.bounding_box()[5]);pieces=[];prev=None;st=time.time()
 for j,z in enumerate(np.arange(.1,h+.1,.2)):
  fcs=fin.slice(float(z));tcs=old.slice(float(z))
  if prev is not None:
   tcs=tcs^prev.offset(.195,circular_segments=12);curr=fcs+tcs;keep=union([])if False else md.CrossSection.batch_boolean([c for c in curr.decompose()if(c^prev.offset(.01,circular_segments=12)).area()>.005],md.OpType.Add);tcs=tcs^keep
  if not tcs.is_empty():pieces.append(tcs.extrude(.200002).translate([0,0,max(0.,float(z-.100001))]))
  prev=fcs+tcs
  if j%100==0:print('TEETH117_LAYER',pid,j,round(time.time()-st,1),flush=True)
 teeth=union(pieces)^old;teeth=union([c for c in material_components(teeth)if(c^fin).volume()>.005 and(c^s).volume()>.005]);fin=union([c for c in material_components(fin)if(c^teeth).volume()>.005]);ind=growth(fin+teeth,d);print('TEETH117_RESULT',pid,'removed_temporary_mm3',float((old-teeth).volume()),'independent_growth',ind['passed'],flush=True);(dst/'verification/support_and_teeth_independent_growth.json').write_text(json.dumps(ind,indent=2));n['fin_v'],n['fin_f']=vf(fin);n['teeth_v'],n['teeth_f']=vf(teeth);d.update(support_volume_mm3=float((fin+teeth).volume()),temporary_teeth_growth_trim={'source':parent,'removed_temporary_volume_mm3':float((old-teeth).volume()),'body_unchanged':True,'model_does_not_participate_in_support_growth':True});np.savez_compressed(dst/'parts'/f'{pid}.npz',**n);(dst/'design'/f'{pid}.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
 if(src/'verification/body_change_fit_and_pose.json').exists():shutil.copy2(src/'verification/body_change_fit_and_pose.json',dst/'verification/body_change_fit_and_pose.json')
 g=geom(pid,label)
 if ind['passed']and g['geometric_constraints_passed']:run(pid,label);check(pid,label);refine(pid,label)
if __name__=='__main__':trial(*sys.argv[1:])
