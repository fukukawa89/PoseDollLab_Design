import json,sys,hashlib,numpy as np
import o22f7 as r
h=r.h

def main():
 r.configure();changed=r.read(r.WORK/'whole_batch_audit.json')['affected_ids'];rows=[]
 for source in r.manifest()['rows']:
  pid=source['id'];path=r.OUT/f'parts/{pid}.npz';n=np.load(path);old=np.load(r.BASE/f'parts/{pid}.npz');body=h.solid(n['v'],n['f']);before=h.solid(old['v'],old['f']);fin=h.solid(n['fin_v'],n['fin_f']);teeth=h.solid(n['teeth_v'],n['teeth_f']);oldfin=h.solid(old['fin_v'],old['fin_f']);oldteeth=h.solid(old['teeth_v'],old['teeth_f']);guard=r.solidfile(r.WORK/f'guards/{pid}.npz');samebody=np.array_equal(n['v'],old['v'])and np.array_equal(n['f'],old['f']);assert samebody==(pid not in changed)
  removed=0. if samebody else max(0.,(before-body).volume());assert removed<1e-5,(pid,removed);assert len(h.material_components(body))==1;assert len(h.material_components(body+fin+teeth))==1;assert(fin^body).volume()<1e-6
  assert all(c.bounding_box()[2]<1e-5 and c.slice(.05).area()>.005 for c in h.material_components(fin));assert np.array_equal(n['fin_v'],old['fin_v']) or(fin-oldfin).volume()<1e-6;assert np.array_equal(n['teeth_v'],old['teeth_v']) or(oldteeth-teeth).volume()<1e-5
  occupied=max(0.,((fin+teeth)^guard).volume());assert occupied<1e-6 or pid in r.RESTORE
  addedguard=0;bodyadded=0
  if pid in changed:
   prefix='r1'if pid=='P095'else'f7';added=h.solid(n[prefix+'_added_body_v'],n[prefix+'_added_body_f']);addedguard=max(0.,(added^guard).volume());assert addedguard<1e-6;bodyadded=added.volume();a=next(x for x in r.read(r.WORK/'whole_batch_audit.json')['rows']if x['id']==pid);H=np.array(a['local_to_print_matrix']);balls=[h.md.Manifold.sphere(x['radius_mm'],96).translate(x['bend']).transform(H[:3])for x in a['candidate_bends']if x['active_flat_capped_elbow']];swept=h.union([r.sweep(s,[0,0,120])for s in balls]);assert(fin^swept).volume()<1e-6
   removal=r.read(r.WORK/f'removal/{pid}.json');assert removal['npz_sha256']==h.sha(path);assert removal['passed']
  else:assert h.sha(path)==h.sha(r.BASE/f'parts/{pid}.npz')
  rep=dict(id=pid,part=source['part'],npz_sha256=h.sha(path),body_sha256=hashlib.sha256(n['v'].tobytes()+n['f'].tobytes()).hexdigest(),base_npz_sha256=h.sha(r.BASE/f'parts/{pid}.npz'),body_changed=not samebody,body_added_mm3=bodyadded,body_removed_numerical_mm3=removed,body_removal_boolean_tolerance_mm3=1e-5,body_components=1,connected_print_components=1,all_fins_bed_rooted=True,fin_body_overlap_mm3=max(0.,(fin^body).volume()),added_body_in_fastener_guard_mm3=addedguard,support_in_fastener_guard_mm3=occupied,hole_support_exception=pid in r.RESTORE,original_tooth_material_preserved=True,new_support_teeth_mm3=0. if np.array_equal(n['teeth_v'],old['teeth_v']) else max(0.,(teeth-oldteeth).volume()),fin_material_removed_mm3=0. if np.array_equal(n['fin_v'],old['fin_v']) else max(0.,(oldfin-fin).volume()),bounds_unchanged=bool(np.allclose(body.bounding_box(),before.bounding_box(),atol=1e-7)),physical_print_tested=False)
  h.put(r.WORK/f'geometry_final/{pid}.json',rep);rows.append(rep)
 h.put(r.WORK/'geometry_summary.json',dict(passed=True,types=len(rows),changed_body_types=changed,body_unchanged_types=150-len(changed),rows=rows));print('GEOMETRY_PASS',len(rows),flush=True)
if __name__=='__main__':main()
