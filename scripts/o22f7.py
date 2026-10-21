"""O22F7 additive elbow correction, whole-batch audit and native checks.
Frozen F5/F6/R1 inputs are never modified.
"""
from pathlib import Path
import json,copy,shutil,itertools,sys,argparse,concurrent.futures
import numpy as np
import o22f7_native as h
from o22f6_final import RESTORE
BASE=h.B/'O22F6_PLA_Final';R1=h.B/'O22F6R1_P095_Elbows'
OLDWORK=h.B/'diagnostics/O22F6_final_20261015'
WORK=h.B/'diagnostics/O22F7_20261016';OUT=h.B/'O22F7_PLA_Final'
ARMS=[('normal_0',[6,-9,-3],[13.8,-11.5,-3],[13.6,-13.5,13.5],1.8),('normal_1',[9,6,-3],[11.5,13.8,-3],[13.5,13.6,13.5],1.8),('wide_0',[6,-9,-5],[27,-9,-5],[27,-13.5,13.5],1.3),('rear_1',[-9,0,-6.5],[-9,27,-6.5],[-13.5,27,-13.5],1.3)]
def read(p):return json.loads(Path(p).read_text('utf8'))
def manifest():return read(BASE/'manifest.json')
def configure():
 h.OUT=OUT;h.WORK=WORK;h.PROJECT_SUFFIX='PLA_final';h.PRINT_SETTINGS_ID='O22-F7 Final / A1 mini PLA 0.4';h.ORIGINAL_PROFILE_IDS=RESTORE;h.SCREEN_LABEL='f7pla';h.TARGET_PART_IDS=None

def solidfile(p):
 n=np.load(p);return h.solid(n['v'],n['f'])
def sweep(s,v):
 q=h.vf(s)[0];return h.md.Manifold.hull_points(np.vstack([q,q+np.array(v)]))
def beam(a,b,r):
 a=np.array(a,float);b=np.array(b,float);z=b-a;L=np.linalg.norm(z);z/=L;seed=np.eye(3)[np.argmin(abs(z))];x=np.cross(seed,z);x/=np.linalg.norm(x)
 return h.md.Manifold.cylinder(L,r,circular_segments=48).transform(np.c_[x,np.cross(z,x),z,a])
def audit():
 configure();WORK.mkdir(parents=True,exist_ok=True)
 meta=read(h.B/'mechanical/assembly_metadata.json')['meta'];exports={r['id']:r for r in read(h.B/'print_batch/manifest.json')['rows']};rows=[];changes=[]
 for row in manifest()['rows']:
  pid=row['id'];d=read(BASE/f'design/{pid}.json');key=d['part'];n=np.load(BASE/f'parts/{pid}.npz');body=h.solid(n['v'],n['f']);rec=dict(id=pid,part=key,source_npz_sha256=h.sha(BASE/f'parts/{pid}.npz'),material_components=len(h.material_components(body)),manifold_status=str(body.status()),body_volume_mm3=body.volume(),candidate_bends=[])
  assert rec['material_components']==1 and rec['manifold_status']=='Error.NoError'
  if key.endswith('/C14'):
   bed=exports[pid]['bed'];A=np.array(meta[key]['transform']);Q=np.eye(4)
   if np.linalg.det(A[:3,:3])<0:Q[1,1]=-1
   H=h.H(d['orientation']['matrix'],d['orientation']['source_translation_mm'])@h.H(bed['rotation'],bed['translation_mm'])@Q
   rec['local_to_print_matrix']=H.tolist()
   for name,a,v,b,r in ARMS:
    ball=h.md.Manifold.sphere(r,96).translate(v).transform(H[:3]);pair=(beam(a,v,r)+beam(v,b,r)).transform(H[:3]);roi=body^ball;expected=pair^ball
    overlap=(roi^expected).volume();missing=(expected-roi).volume();extra=(roi-expected).volume();active=overlap>expected.volume()*.99 and missing<.001 and extra<.001
    rec['candidate_bends'].append(dict(name=name,active_flat_capped_elbow=bool(active),anchor=a,bend=v,tip=b,radius_mm=r,source_pair_missing_mm3=missing,source_pair_extra_mm3=extra,source_pair_overlap_mm3=overlap,occupied_mm3=roi.volume(),fill_mm3=(ball-body).volume(),print_centre=(H@np.r_[v,1])[:3].tolist()))
   rec['classification']='flat_capped_elbows' if any(x['active_flat_capped_elbow']for x in rec['candidate_bends'])else'core_requires_review'
   assert sum(x['active_flat_capped_elbow']for x in rec['candidate_bends'])==2,(pid,rec['candidate_bends'])
   changes.append(pid)
  elif key.startswith('frame/'):
   rec['classification']='rounded_routed_frame_or_terminal_form';rec['basis']='revO15 carriers_swept.py/endforms.py/equipped.py and revO19/20 design.py explicitly union endpoint spheres along routed chains; head crossbar is a T joint, not two meeting flat end caps. Existing assembly/electronics/cable reliefs retained.'
  elif 'sensor_cassette' in key or 'pcb_clip' in key:
   rec['classification']='functional_cassette_and_clip_openings';rec['basis']='O22 sensor-fit/end-axis model and O17 integrated cassette: board-entry, retaining leaf and fastener features; no two-segment end-to-end bent beam.'
  else:
   rec['classification']='bearing_yoke_case_cap_pad_fixture';rec['basis']='Bearing lands, mechanical stops, magnet side-loading ports, case openings and mounting holes retained; no active two-segment end-to-end bent beam in generator.'
  rows.append(rec);print('AUDIT',pid,rec['classification'],[(x['name'],round(x['fill_mm3'],5))for x in rec['candidate_bends']if x['active_flat_capped_elbow']],flush=True)
 h.put(WORK/'whole_batch_audit.json',dict(types=len(rows),instances=sum(len(p['items'])for p in manifest()['plates']),plates=14,affected_ids=changes,rows=rows,scope='Source-construction audit of all released types plus exact local solid comparison at all C14 arm alternatives. Mesh integrity checked for every body. Functional openings are not indiscriminately filled.'))

def stage():
 configure();assert not(OUT/'RELEASED.json').exists()
 audit=read(WORK/'whole_batch_audit.json')
 for sub in['parts','design','projects','verification']:(OUT/sub).mkdir(parents=True,exist_ok=True)
 for sub in['guards','initial']:shutil.copytree(OLDWORK/sub,WORK/sub,dirs_exist_ok=True)
 shutil.copy2(OLDWORK/'profile_overrides.json',WORK/'profile_overrides.json')
 for row in audit['rows']:
  pid=row['id'];src=R1 if pid=='P095' else BASE
  for sub,ext in[('parts','.npz'),('design','.json')]:shutil.copy2(src/sub/(pid+ext),OUT/sub/(pid+ext))
  if pid not in audit['affected_ids'] or pid=='P095':continue
  n=dict(np.load(OUT/f'parts/{pid}.npz'));d=read(OUT/f'design/{pid}.json');body=h.solid(n['v'],n['f']);fin=h.solid(n['fin_v'],n['fin_f']);teeth=h.solid(n['teeth_v'],n['teeth_f']);H=np.array(row['local_to_print_matrix']);active=[x for x in row['candidate_bends']if x['active_flat_capped_elbow']]
  balls=[h.md.Manifold.sphere(x['radius_mm'],96).translate(x['bend']).transform(H[:3])for x in active];added=h.union(balls)-body;after=body+h.union(balls);after.volume();after=after.as_original()
  clearance=[h.md.Manifold.sphere(x['radius_mm']+.35,96).translate(x['bend']).transform(H[:3])for x in active];exclusion=h.union([sweep(s,[0,0,120])for s in clearance]);newfin=fin-exclusion
  guard=solidfile(WORK/f'guards/{pid}.npz');assert(added^guard).volume()<1e-6,(pid,'guard',float((added^guard).volume()))
  assert(body-after).volume()<1e-5,(pid,'body_removed',(body-after).volume());assert len(h.material_components(after))==1
  assert(newfin^after).volume()<1e-6;assert len(h.material_components(after+newfin+teeth))==1
  assert all(c.bounding_box()[2]<1e-5 and c.slice(.05).area()>.005 for c in h.material_components(newfin))
  assert all((c^newfin).volume()>.001 and(c^after).volume()>.001 for c in h.material_components(teeth))
  assert(newfin^h.union([sweep(s,[0,0,120])for s in balls])).volume()<1e-6
  n['v'],n['f']=h.vf(after);n['fin_v'],n['fin_f']=h.vf(newfin);n['f7_added_body_v'],n['f7_added_body_f']=h.vf(added);np.savez_compressed(OUT/f'parts/{pid}.npz',**n)
  rep=dict(id=pid,added_mm3=added.volume(),removed_mm3=max(0.,(body-after).volume()),guard_overlap_mm3=max(0.,(added^guard).volume()),fin_removed_mm3=(fin-newfin).volume(),body_components=1,whole_components=1,bounds_unchanged=bool(np.allclose(body.bounding_box(),after.bounding_box(),atol=1e-7)),all_fins_bed_rooted=True,fin_body_overlap_mm3=max(0.,(newfin^after).volume()),continuous_downward_fin_exit=True,fin_gap_at_new_body_mm=.35,existing_teeth_preserved=True,active_bends=active,local_to_print_matrix=H.tolist(),source_sha256=h.sha(BASE/f'parts/{pid}.npz'),npz_sha256=h.sha(OUT/f'parts/{pid}.npz'))
  h.put(WORK/f'geometry/{pid}.json',rep);d.update(body_changed=True,body_change_reference='O22F6_PLA_Final',part_body_modified_from_F4=True,body_f4_faces_identical=False,body_rigid_transform_only=False,f7_elbows=rep,native_pending=True);h.put(OUT/f'design/{pid}.json',d);print('STAGED',pid,rep['added_mm3'],rep['fin_removed_mm3'],flush=True)

def build_one(p):configure();return h.build_plate(p)
def screen_one(p):configure();return h.screen_plate(p)
def run(action,ids=None):
 jobs=[p for p in read(h.SRC/'manifest.json')['plates']if not ids or p['id']in ids];fn={'build':build_one,'screen':screen_one}[action]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as pool:
  for result in pool.map(fn,jobs):pass
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('action');ap.add_argument('--ids',nargs='*');a=ap.parse_args()
 if a.action in['audit','stage']:globals()[a.action]()
 else:run(a.action,a.ids)
