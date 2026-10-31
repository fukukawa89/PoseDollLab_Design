"""Split zero-bead-contact paths at the previous solid boundary.
This avoids calling a long internal skin path external because of a micron-scale endpoint.
The v1 report is retained unchanged; limits are unchanged and split endpoints gain no anchors.
"""
from pathlib import Path
import sys,json,numpy as np,concurrent.futures,zipfile,shutil
from shapely.geometry import LineString
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,union
from o22_cross_section_geometry import polygon
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def refine(pid,label):
 p=O/'candidates'/pid/label;d=json.loads((p/'verification/full_bead_contacts.json').read_text());dest=p/'verification/full_bead_contacts_v2.json'
 project=p/'projects'/json.loads((p/'verification/local_extrusion.json').read_text())['project']
 with zipfile.ZipFile(project) as z:actual=json.loads(z.read('Metadata/project_settings.config'))
 lh=float(actual['layer_height']);initial=float(actual['initial_layer_print_height']);design=json.loads((p/'design'/f'{pid}.json').read_text());declared=float(design.get('required_layer_height_mm',.12 if 'fine' in label else .2))
 if dest.exists():
  q=json.loads(dest.read_text())
  if q['project_sha256']==d['project_sha256'] and abs(q.get('actual_constant_layer_height_mm',declared)-lh)<1e-8 and (abs(initial-lh)<1e-8 or q.get('first_layer_geometry_center_corrected',False)):return q
  if not dest.with_name('full_bead_contacts_v2_pre_profile99.json').exists():shutil.copy2(dest,dest.with_name('full_bead_contacts_v2_pre_profile99.json'))
 oldfree=d['external_free_runs'];newfree=[];internal=d['internal_infill_gaps'].copy();n=np.load(p/'parts'/f'{pid}.npz');it=json.loads((p/'verification/plate_manifest.json').read_text())['items'][0];s=union([solid(n[v],n[f]) for v,f in [('v','f'),('fin_v','fin_f'),('teeth_v','teeth_f')] if len(n[f])]).transform(np.c_[it['rotation_matrix'],it['translation_mm']]);cache={}
 for q in oldfree:
  z=round(q['z_mm'],4)
  if z not in cache:
   prev_center=initial/2 if abs(z-(initial+lh))<.001 else z-1.5*lh
   cache={z:polygon(s.slice(prev_center)).buffer(.015)}
  g=LineString(q['xy_mm']);prev=cache[z];ex=g.difference(prev);inside=g.intersection(prev)
  for shape,isinternal in [(ex,False),(inside,True)]:
   for piece in getattr(shape,'geoms',[shape]):
    if piece.geom_type!='LineString' or piece.length<.15:continue
    whole=piece.equals(g);anchors=q['anchors'] if whole else 0;out=dict(q,xy_mm=np.array(piece.coords).tolist(),length_mm=float(piece.length),bounds_mm=list(piece.bounds),anchors=anchors,inside_previous_solid_geometry=isinternal,parent_free_run_length_mm=q['length_mm'],classification='internal_infill_gap' if isinternal else 'critical_external_run' if piece.length>(3 if anchors==2 else 1) else 'short_external_gap')
    (internal if isinternal else newfree).append(out)
 critical=[q for q in newfree if q['classification']=='critical_external_run'];d.update(audit_schema='full-bead-v2-split-at-solid-boundary',actual_constant_layer_height_mm=lh,actual_initial_layer_height_mm=initial,first_layer_geometry_center_corrected=True,layer_profile_source='actual native project settings, not candidate design metadata',external_free_runs=newfree,internal_infill_gaps=internal,critical_external_runs=critical,critical_external_count=len(critical),max_external_free_run_mm=max([q['length_mm'] for q in newfree],default=0),native_review_resolved=not critical and not d['external_islands'],previous_report='full_bead_contacts.json',refinement='A zero-bead-contact line is partitioned at previous solid geometry, instead of classifying its full length as external when only a small section crosses the boundary. Split endpoints are conservatively unanchored. Previous solid section uses the recorded constant layer height for this candidate.');dest.write_text(json.dumps(d,indent=2));return d
if __name__=='__main__':
 specs=[tuple(s.split(':')) for s in sys.argv[1:]] if sys.argv[1:] else [(p.parents[2].name,p.parents[1].name) for p in (O/'candidates').glob('*/*/verification/full_bead_contacts.json') if 'fine' not in p.parents[1].name]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
  for d in pool.map(lambda x:x,[]):pass
  fs=[pool.submit(refine,*s) for s in specs]
  out=[{k:d[k] for k in ['id','label','critical_external_count','external_island_count','native_review_resolved']} for f in concurrent.futures.as_completed(fs) for d in [f.result()]]
 (O/'full_bead_refined_progress.json').write_text(json.dumps(out,indent=2));print('REFINED',len(out),'CLEAR',sum(q['native_review_resolved'] for q in out),flush=True)
