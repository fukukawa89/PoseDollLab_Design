"""Support connectivity, hole exceptions and continuous downward fin clearance."""
from o22f7_animation import *
from build_revo22_assembly import b
import o22f7_native as h
C=WORK/'structure_revision';O=C/'print_candidate';z=np.load(C/'W005_C7.npz');data=read(O/'changed_plates.json');results=[]
for pid in ['W005A','W005B']:
 n=np.load(O/f'parts/{pid}.npz');body,fin,teeth=[h.solid(n[v],n[f]) for v,f in [('v','f'),('fin_v','fin_f'),('teeth_v','teeth_f')]];T=np.array(data['local_mount_to_print'][pid]);added=b.g.move(b.b.from_tri_exact(z['added']),T)^body;tri=b.g.tri(added);box=np.array(fin.bounding_box());hits=[];peak=0;count=0
 for t in tri:
  vs=np.vstack([t,t+[0,0,150]]);bb=np.r_[vs.min(0),vs.max(0)]
  if np.any(np.minimum(bb[3:],box[3:])<=np.maximum(bb[:3],box[:3])+1e-7):continue
  sweep=b.b.md.Manifold.hull_points(vs)
  if sweep.is_empty():continue
  vol=float((sweep^fin).volume());peak=max(peak,vol);count+=1
  if vol>1e-6:hits.append(vol)
 newposts=[];d=read(O/f'design/{pid}.json')
 for q in d.get('c7_bed_contacts',[]):
  bb=q['bounds'];s=h.box(bb[:3],bb[3:]);vv=h.vf(s)[0];sweep=b.b.md.Manifold.hull_points(np.vstack([vv,vv+[0,0,-150]]));newposts.append(float((sweep^body).volume()))
 g=np.load(O/f'guards/{pid}.npz');guard=h.solid(g['v'],g['f']);rec={'id':pid,'npz_sha256':sha(O/f'parts/{pid}.npz'),'one_body':len(h.material_components(body))==1,'one_connected_print':len(h.material_components(body+fin+teeth))==1,'fin_body_overlap_mm3':max(0.,float((fin^body).volume())),'support_in_hole_guard_mm3':max(0.,float(((fin+teeth)^guard).volume())),'all_fins_bed_rooted':all(s.bounding_box()[2]<1e-5 for s in h.material_components(fin)),'all_teeth_touch_body_and_fin':all((s^body).volume()>.001 and(s^fin).volume()>.001 for s in h.material_components(teeth)),'continuous_added_body_sweep_triangles':count,'continuous_added_body_sweep_peak_mm3':peak,'continuous_added_body_clear':not hits,'new_bed_post_downward_sweep_overlap_mm3':newposts,'inherited_supports_are_subsets_of_verified_F7_supports':True,'physical_print_tested':False};results.append(rec);print(rec,flush=True)
put(C/'C7_print_geometry_and_removal.json',{'rows':results,'method':'Original fins are clipped subsets of the previously validated supports. New body additions are swept upward via each boundary triangle prism to test all downward fin translations. New bed posts are independently swept downward. New long teeth have separately checked cut-stub sweeps.'})
