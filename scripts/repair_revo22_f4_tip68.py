"""Remove only isolated downward tips, retaining all actual hardware contact envelopes.
The cut is bounded to the flagged bead footprint and less than 1 mm of height;
its purpose is to postpone an isolated first speck until its surrounding wall exists.
"""
from pathlib import Path
import sys,json,numpy as np,concurrent.futures,traceback
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,vf,box,union
from o22_reference_mesh import reference_solid
from o22_material_components import material_components
from repair_revo22_f4_guarded_chamfer import context
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
from refine_revo22_f4_full_bead import refine
from verify_revo22_f4_body_change import check as fit
from verify_revo22_f4_repaired_geometry import check as geom
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def trial(pid,parent,label):
 src=O/'candidates'/pid/parent;dst=O/'candidates'/pid/label;n=dict(np.load(src/'parts'/f'{pid}.npz'));d=json.loads((src/'design'/f'{pid}.json').read_text());audit=refine(pid,parent);it=json.loads((src/'verification/plate_manifest.json').read_text())['items'][0];M=np.array(it['rotation_matrix']);t=np.array(it['translation_mm']);old=solid(n['v'],n['f']);original=reference_solid(n,d);new=old;parts,key,T=context(d,pid);offsets=np.array([[x,y,z]for x in[-.08,0,.08]for y in[-.08,0,.08]for z in[-.08,0,.08]]);guards={};rows=[]
 for issue in audit['external_islands']:
  b=issue['bounds_mm'];z=issue['z_mm'];pts=(np.array([[x,y,z]for x in[b[0]-.12,b[2]+.12]for y in[b[1]-.12,b[3]+.12]])-t)@M;lo=pts.min(0);hi=pts.max(0);roi=box([lo[0],lo[1],z-.4],[hi[0],hi[1],z+.6]);cut=roi;delta=new^cut;world=delta.transform(np.linalg.inv(T)[:3,:]);bb=np.array(world.bounding_box());gg=[]
  if not 1e-6<float(delta.volume())<8.:continue
  for k,s in parts.items():
   if k==key:continue
   sb=np.array(s.bounding_box());sep=np.maximum(np.maximum(sb[:3]-bb[3:],bb[:3]-sb[3:]),0)
   if np.linalg.norm(sep)>.16:continue
   if k not in guards:guards[k]=union([s.translate(o)for o in offsets]).transform(T[:3,:])
   gg.append(guards[k])
  cut=cut-union(gg);delta=new^cut
  if delta.volume()<1e-6:continue
  proposal=new-cut
  if len(material_components(proposal))!=len(material_components(old)):continue
  if abs((proposal-original).volume())>1e-6:continue
  if (original-proposal).volume()>min(60.,original.volume()*.008):continue
  new=proposal;rows.append({'kind':'isolated_downward_tip_truncation','native_island':issue,'local_bounds_mm':list(roi.bounding_box()),'removed_volume_mm3':float(delta.volume()),'cut_height_mm':1.,'hardware_margin_mm':.08})
 if not rows:return {'id':pid,'label':label,'no_contact_clear_tip_cut':True}
 fin=solid(n['fin_v'],n['fin_f']);teeth=solid(n['teeth_v'],n['teeth_f']);teeth=union([q for q in material_components(teeth)if(q^new).volume()>.005 and(q^fin).volume()>.005]);fin=union([q for q in material_components(fin)if(q^teeth).volume()>.005]);n['source_f']=n.get('source_f',n['f']);n['v'],n['f']=vf(new);n['removed_body_v'],n['removed_body_f']=vf(original-new);n['fin_v'],n['fin_f']=vf(fin);n['teeth_v'],n['teeth_f']=vf(teeth);bc=d.get('body_change',{});bc.update(kind='isolated_print_tip_truncation',chamfers=bc.get('chamfers',[])+rows,removed_volume_mm3=float((original-new).volume()),added_volume_mm3=float((new-original).volume()),source_body_volume_mm3=float(original.volume()),removed_fraction=float((original-new).volume()/original.volume()),assembly_contact_validation_pending=True);d.update(body_change=bc,source_mesh_preserved=False)
 for sub in ['parts','design','verification']:(dst/sub).mkdir(parents=True,exist_ok=True)
 np.savez_compressed(dst/'parts'/f'{pid}.npz',**n);(dst/'design'/f'{pid}.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');print('TIP_TRUNCATION',pid,label,len(rows),bc['removed_volume_mm3'],flush=True);run(pid,label);check(pid,label);q=refine(pid,label);out={k:q[k]for k in['id','label','external_island_count','critical_external_count','native_review_resolved']}
 if q['native_review_resolved']:out['fit']=fit(pid,label)['fit_and_pose_geometry_passed'];out['geometry']=geom(pid,label)['geometric_constraints_passed']
 return out

def one(spec):
 pid,parent=spec.split(':');out=[]
 try:
  for j in range(1,4):
   label='tip68_'+str(j).zfill(2);q=trial(pid,parent,label);out.append(q);print('TIP68_RESULT',q,flush=True)
   if q.get('native_review_resolved')or q.get('no_contact_clear_tip_cut'):break
   parent=label
  return {'id':pid,'results':out}
 except Exception:return {'id':pid,'results':out,'error':traceback.format_exc()}
if __name__=='__main__':
 out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as pool:
  for f in concurrent.futures.as_completed([pool.submit(one,s)for s in sys.argv[1:]]):
   out.append(f.result());(O/'tip68_progress.json').write_text(json.dumps(out,indent=2))
