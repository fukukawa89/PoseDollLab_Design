"""Cross-check the actual C7 package, its unchanged sources and native output."""
from o22f7_animation import *
from build_revo22_assembly import b
import o22f7_native as h,collections,zipfile,copy
C=WORK/'structure_revision';N=B/'O22F7_PLA_AssemblyRevision';NG=N/'assembly/tutorials/assembly-o22';m=read(N/'manifest.json');g=read(NG/'guide-data.json');seq=read(NG/'animation/sequence.json');sc=read(NG/'scene.json');proof=[]
def ok(name,value,**kw):assert value,(name,kw);proof.append(dict(check=name,passed=True,**kw))
ids={r['id'] for r in m['rows']};its=[q for p in m['plates'] for q in p['items']];ok('current_inventory',len(ids)==151 and len(its)==194 and len(m['plates'])==15 and 'W005' not in ids)
untouched=[]
for pid in sorted(ids-{'W005A','W005B'}):ok('body_and_support_bytes_'+pid,sha(N/f'parts/{pid}.npz')==sha(F/f'parts/{pid}.npz'));untouched.append(pid)
plateproof=[]
for p in m['plates']:
 pp=N/p['project'];d=read(N/p['proof']);ok('native_plate_'+p['id'],d['native_review_resolved'] and d['external_island_count']==0 and d['critical_external_count']==0 and d['project_sha256']==sha(pp))
 if p['id'] not in ['D05','D15']:ok('unchanged_project_'+p['id'],sha(pp)==sha(F/p['project']))
 with zipfile.ZipFile(pp) as z:settings=json.loads(z.read('Metadata/project_settings.config'));ok('PLA_profile_'+p['id'],settings['filament_type']==['PLA'] and settings['enable_support']=='0' and settings['print_sequence']=='by layer')
 plateproof.append({'plate':p['id'],'sha256':sha(pp),'external_islands':0,'critical_external_runs':0})
obs=sc['objects'];printed=[o for o in obs if o.get('print_id')];metal=[o for o in obs if o['role']=='metal'];ok('scene_inventory',len(printed)==186 and len(metal)==960 and len(obs)==1524)
seen=set();metalcount=collections.Counter(o['sku'] for o in metal)
for i,act in enumerate(seq['actions'],1):
 ok('action_'+act['id'],act['id']==f'A{i:04}' and not(seen&set(act['new'])) and np.isfinite(act['path']).all());seen.update(act['new']);assert set(act['moving'])<=seen
ok('every_object_introduced_once',seen==set(range(len(obs))) and len(seq['actions'])==1658 and len(seq['chapters'])==26)
ok('hardware_BOM',all(metalcount[k]==v['net_quantity'] for k,v in g['hardware'].items()))
ok('wiring_coverage',len(g['routes'])==46 and sum(a['kind']=='wire' for a in seq['actions'])==46 and sum(a['kind']=='plug' for a in seq['actions'])==46)
ok('no_unfinished_actions',not seq['coverage']['unverified_insertion_steps'] and not any(a.get('needs_path_review') for a in seq['actions']))
for o in printed:
 q=next(q for q in g['instances'] if q['address']==o['address']);ok('address_'+o['address'],q['id']==o['print_id'] and q['part']==o['label'] and (N/q['project']).exists())
raw=np.fromfile(NG/sc['geometry_url'],dtype='<f4').reshape(-1,6);ok('scene_binary_hash',sha(NG/sc['geometry_url'])==sc['geometry_sha256']==seq['source_geometry_sha256']);ok('sequence_guide_hash',sha(NG/'guide-data.json')==seq['source_guide_sha256'])
for mm in sc['meshes'].values():assert mm['first']>=0 and mm['count']>0 and mm['count']%3==0 and mm['first']+mm['count']<=len(raw)
ok('geometry_finite',np.isfinite(raw).all())
z=np.load(C/'W005_C7.npz');trans=read(C/'print_candidate/changed_plates.json')['local_mount_to_print'];eq=[]
for pid,piece in [('W005A','root'),('W005B','distal')]:
 n=np.load(N/f'parts/{pid}.npz');local=b.g.move(h.solid(n['v'],n['f']),np.linalg.inv(trans[pid]));source=b.b.from_tri_exact(z[piece]);err=max(abs(float((local-source).volume())),abs(float((source-local).volume())));ok('printed_C7_body_'+pid,err<1e-4,symmetric_difference_mm3=err)
 o=next(o for o in printed if o['print_id']==pid);mm=sc['meshes'][o['mesh']];shown=b.b.from_tri_exact(raw[mm['first']:mm['first']+mm['count'],:3].reshape(-1,3,3));err=max(abs(float((shown-source).volume())),abs(float((source-shown).volume())));point_error=float(np.linalg.norm(raw[mm['first']:mm['first']+mm['count'],:3].astype(float)-z[piece].reshape(-1,3),axis=1).max());ok('displayed_C7_body_'+pid,point_error<.0001,triangle_storage_max_error_mm=point_error,symmetric_difference_mm3=err);eq.append({'id':pid,'part':o['label'],'address':o['address'],'npz_sha256':sha(N/f'parts/{pid}.npz'),'print_to_mesh':np.linalg.inv(trans[pid]).tolist(),'display_symmetric_difference_mm3':err})
 old=np.load(F/'parts/W005.npz');oldfin=b.g.move(h.solid(old['fin_v'],old['fin_f']),np.array(trans[pid])@np.linalg.inv(trans['W005B']));d=read(N/f'design/{pid}.json');allowed=oldfin+h.union([h.box(q['bounds'][:3],q['bounds'][3:]) for q in d.get('c7_bed_contacts',[])]);novel=float((h.solid(n['fin_v'],n['fin_f'])-allowed).volume());ok('fin_provenance_'+pid,novel<1e-5,unsupported_new_fin_material_mm3=max(0.,novel))
sh=sha(C/'W005_C7.npz')
for name in ['W005_C7_surface_review.json','W005_C7_function_review.json']:
 d=read(C/name);ok(name,d['passed'] and d['candidate_sha256']==sh)
for name in ['W005_C7_preassembly_review.json','W005_C7_stock_review.json','W005_C7_sequence_interfaces.json']:
 d=read(C/name);ok(name,all(q['passed'] for q in d['checks']))
 if 'sequence_sha256' in d:ok(name+'_source',d['sequence_sha256']==sha(NG/'animation/sequence.json'))
d=read(C/'C7_chest_rotation_review.json');ok('chest_rotation',d['passed'] and d['sequence_sha256']==sha(NG/'animation/sequence.json'))
for row in read(C/'C7_print_geometry_and_removal.json')['rows']:
 ok('support_removal_'+row['id'],row['npz_sha256']==sha(N/f"parts/{row['id']}.npz") and row['one_body'] and row['one_connected_print'] and row['all_fins_bed_rooted'] and row['all_teeth_touch_body_and_fin'] and row['continuous_added_body_clear'] and max(row['new_bed_post_downward_sweep_overlap_mm3'],default=0)<1e-6)
original=read(WORK/'before.json')
for rel,digest in original['manufacturing'].items():ok('original_manufacturing_preserved_'+rel,sha(F/rel)==digest)
ok('original_release_archive_preserved',sha(B/'O22F7_PLA_完整打印包_20261016.zip')==original['archive_sha256'])
ok('guide_native_project_hashes',g['native_project_sha256']=={p['project']:sha(N/p['project']) for p in m['plates']})
for ch in seq['chapters']:
 ii=[i for a in seq['actions'][ch['start']:ch['end']] for i in a['new']];st=next(t for t in g['steps'] if t['step']==ch['id']);ok('chapter_inventory_'+ch['id'],st['new_parts']==[obs[i]['label'] for i in ii if obs[i].get('print_id')] and st['stock']==dict(collections.Counter(obs[i]['sku'] for i in ii if obs[i]['role']=='metal')))
for pid in ['W005A','W005B']:
 row=next(r for r in m['rows'] if r['id']==pid);d=read(N/f'design/{pid}.json');ok('current_design_record_'+pid,not d['native_pending'] and not d['fit_and_pose_pending'] and d['support_count']==row['fin_count'] and d['npz_sha256']==sha(N/f'parts/{pid}.npz'))
transition=read(C/'C7_release_metadata_transition.json');payload=lambda d:{k:v for k,v in d.items() if k not in ['status','source_guide_sha256']};canonical=lambda d:hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest();beforeseq=read(N/'verification/prior_release/assembly/tutorials/assembly-o22/animation/sequence.json');ok('verified_motion_payload_preserved',canonical(payload(seq))==canonical(payload(beforeseq))==transition['mechanical_action_payload_sha256'])
# Complete current mesh evidence while preserving the inherited source rows.
d=read(G/'evidence/current_body_meshes.json');d['rows']=[q for q in d['rows'] if q['id']!='W005']+eq;d.update(installed_instances=186,revision=seq['revision']);put(NG/'evidence/current_body_meshes.json',d)
summary={'passed':True,'version':'O22F7-PLA-Final','revision':seq['revision'],'status':'DIGITAL_CONTENT_CHECKS_PASSED','types':151,'total_print_instances':194,'installed_print_instances':186,'gauge_instances':1,'optional_samples':7,'hardware_instances':960,'plates':15,'unchanged_type_count':len(untouched),'unchanged_native_plate_count':13,'all_native_plates_passed':True,'plate_results':plateproof,'native_external_islands':0,'native_critical_external_runs':0,'new_hole_support_exception':'W005B','inherited_hole_exception_type_count':16,'assembly_chapters':26,'assembly_actions':len(seq['actions']),'sensor_boards':46,'wiring_routes':46,'all_scene_objects_have_unique_first_installation':True,'resolved_clavicle_insertion_paths':2,'whole_device_pose_comparisons':414,'critical_interface_path_checks':len(read(C/'W005_C7_sequence_interfaces.json')['checks']),'path_checks_are_sampled':True,'all_animation_paths_continuously_collision_certified':False,'physical_print_tested':False,'physical_assembly_tested':False,'strength_or_fatigue_tested':False,'sequence_sha256':sha(NG/'animation/sequence.json'),'geometry_sha256':sha(NG/sc['geometry_url']),'candidate_geometry_sha256':sh,'checks':proof}
put(C/'C7_package_verification.json',summary);put(N/'verification/C7/package_verification.json',summary);print('PACKAGE_VERIFIED',len(proof),'checks',summary['sequence_sha256'],flush=True)
