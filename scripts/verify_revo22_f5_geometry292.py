"""Certify selected F5 body identity, fin roots and continuous withdrawal."""
import sys,json,hashlib,math,concurrent.futures,traceback,numpy as np
from search_revo22_f5_orientation268 import O,B,OLD,put
from build_revo22_fins import solid,vf,box,union,md
from o22_material_components import material_components
from verify_revo22_x062_removal245 import exact_clear

def run(pid,label=None):
 sel={'label':label} if label is not None else json.loads((O/'selections'/f'{pid}.json').read_text());folder=O/'candidates'/pid/sel['label'];fp=folder/'parts'/f'{pid}.npz';sha=hashlib.sha256(fp.read_bytes()).hexdigest();out=folder/'verification/f5_geometry.json'
 d=json.loads((folder/'design'/f'{pid}.json').read_text())
 if out.exists()and json.loads(out.read_text())['parts_npz_sha256']==sha and (not d.get('connector_void_policy') or json.loads(out.read_text()).get('whole_stem_extraction_verified')):return json.loads(out.read_text())
 n=np.load(fp);d=json.loads((folder/'design'/f'{pid}.json').read_text());old=np.load(OLD/'parts'/f'{pid}.npz');od=json.loads((OLD/'design'/f'{pid}.json').read_text());Q=np.array(d.get('f4_to_current_matrix',np.array(d['orientation']['matrix'])@np.array(od['orientation']['matrix']).T));off=np.array(d.get('f4_to_current_translation_mm',np.array(d['orientation']['source_translation_mm'])-Q@np.array(od['orientation']['source_translation_mm'])));expected=old['v']@Q.T+off;exact=old['v'].shape==n['v'].shape and np.array_equal(old['f'],n['f']);err=float(abs(expected-n['v']).max())if exact else None;exact=exact and err<1e-6
 body=solid(n['v'],n['f']);fin=solid(n['fin_v'],n['fin_f']);teeth=solid(n['teeth_v'],n['teeth_f']);reference=solid(expected,old['f']);added=0. if exact else float((body-reference).volume());removed=0. if exact else float((reference-body).volume());assert exact or added<1e-6 or (d.get('f5_additions') and added<min(10.,reference.volume()*.002)),(pid,'Unexpected added permanent material',added);assert exact or d.get('part_body_modified_from_F4',False),(pid,'Unreported body change');assert(fin^body).volume()<1e-6
 groups=material_components(fin);rows=[];outgeom={};distance=max(220.,float(n['v'][:,2].max())+60)
 for i,g in enumerate(groups,1):
  bed=float(g.slice(.1).area());touch=float((g^teeth).volume());assert g.bounding_box()[2]<1e-6 and bed>.01 and touch>.005
  dirs=[[0.,0.,-1.]]
  for rec in d.get('local_route_repairs',[]):
   a=np.array(rec['root'])
   if(g^box(a-[.4,.4,.2],a+[.4,.4,.2])).volume()>.005:dirs.append(rec.get('removal_vector',[0.,0.,-1.]))
  dirs +=[[math.cos(a)*.8,math.sin(a)*.8,-1.]for a in np.arange(0,2*np.pi,np.pi/6)];good=[]
  for dr in dirs:
   dr=np.array(dr);dr/=np.linalg.norm(dr)
   if any(np.allclose(dr,x)for x in good):continue
   clear,_=exact_clear(g,body,dr*distance)
   if clear:good.append(dr);break
  assert good,(pid,'Fin cannot be withdrawn',i);rows.append(dict(id=f'S{i:02}',bounds_mm=list(g.bounding_box()),volume_mm3=float(g.volume()),bed_contact_mm2=bed,tooth_overlap_mm3=touch,body_gap_mm_capped_at_05=float(g.min_gap(body,.5)),removal_vector=good[0].tolist(),continuous_body_clearance=True));outgeom[f'g{i}_v'],outgeom[f'g{i}_f']=vf(g)
 todo=list(range(len(groups)));stages=[]
 while todo:
  moved=False
  for i in sorted(todo,key=lambda i:abs(rows[i]['removal_vector'][2])):
   others=union([groups[j]for j in todo if j!=i]);dr=np.array(rows[i]['removal_vector']);ok,_=exact_clear(groups[i],others,dr*distance)
   if ok:stages.append(dict(groups=[rows[i]['id']],vector=dr.tolist(),simultaneous=False));todo.remove(i);moved=True;break
  if moved:continue
  for i in todo:
   others=body+union([groups[j]for j in todo if j!=i]);alternatives=[[math.cos(a)*lean,math.sin(a)*lean,-1.]for lean in [.8,1.5,3.]for a in np.arange(0,2*np.pi,np.pi/6)]+[[1.,0.,0.],[-1.,0.,0.],[0.,1.,0.],[0.,-1.,0.]]
   for dr in alternatives:
    dr=np.array(dr);dr/=np.linalg.norm(dr);ok,_=exact_clear(groups[i],others,dr*distance)
    if ok:
     rows[i]['removal_vector']=dr.tolist();stages.append(dict(groups=[rows[i]['id']],vector=dr.tolist(),simultaneous=False));todo.remove(i);moved=True;break
   if moved:break
  if moved:continue
  rest=union([groups[i]for i in todo]);ok,_=exact_clear(rest,body,np.array([0.,0.,-distance]))
  if ok:stages.append(dict(groups=[rows[i]['id']for i in todo],vector=[0,0,-1],simultaneous=True,instruction='Hold these bed-rooted fins together and lift the freed body upward after all yellow connectors have been cleared.'));todo=[];break
  raise AssertionError((pid,'Fin-to-fin removal lock',todo))
 contacts=[]
 for c in material_components(teeth):
  rb=float((c^body).volume());rf=float((c^fin).volume());assert rb>.005 and rf>.005,(pid,'orphan connector',rb,rf);contacts.append(dict(body_overlap_mm3=rb,fin_overlap_mm3=rf))
 guardfile=folder/'verification/guards.npz';guard_volume=None;core_guard_volume=None
 if guardfile.exists():
  gn=np.load(guardfile);ban=solid(gn['v'],gn['f'])-body;guard_volume=float((teeth^ban).volume());core_guard_volume=float((fin^ban).volume())
  if d.get('connector_void_policy')!='whole_stem_extraction':assert guard_volume<1e-6,(pid,'Connector in functional space',guard_volume)
 extraction=[];stem_order=[];strict_guard_volume=None
 if d.get('connector_void_policy')=='whole_stem_extraction':
  mn=np.load(folder/'verification/strict_magnet_guards.npz');mb=solid(mn['v'],mn['f'])-body;strict_guard_volume=float((teeth^mb).volume());assert strict_guard_volume<1e-6,(pid,'Magnet entry blocked',strict_guard_volume)
  rods=[];free=[]
  for j,rec in enumerate(d.get('local_route_repairs',[])):
   if rec.get('kind')!='extractable_void_contact_341':continue
   a=np.array(rec['root']);b=np.array(rec['tip']);middle=a+(b-a)*max(0.,1.-rec.get('taper_height_mm',.45)/(b[2]-a[2]));middle=b-np.array([0,0,rec.get('taper_height_mm',.9)]) if rec.get('contact_pad') else middle;xy=np.array([[-1,-1,0],[1,-1,0],[1,1,0],[-1,1,0]]);tt=union([md.Manifold.hull_points(np.vstack([xy*.4+a,xy*.4+middle])),md.Manifold.hull_points(np.vstack([xy*.4+middle,xy*(rec.get('tip_width_mm',.6)/2)+b]))]);tt=tt^box([-1000,-1000,0],[1000,1000,1000]) if d.get('teeth_clipped_at_bed') else tt
   if rec.get('mesh_key'):tt=solid(n[rec['mesh_key']+'_v'],n[rec['mesh_key']+'_f'])
   if d.get('bed_drop_mm',0)>0 or d.get('teeth_clipped_by_body_relief'):
    tt=tt^teeth
    if tt.is_empty() or(tt^body).volume()<.005:continue
   else:assert(tt-teeth).volume()<1e-5
   excess=tt-body;dr=np.array(rec['stem_removal_vector']);dr/=np.linalg.norm(dr);rods.append(tt);overlap=float((excess^ban).volume())
   if overlap>1e-6:
    clear,_=exact_clear(excess,body,dr*distance);assert clear,(pid,'Trapped cavity stem',j)
    free.append(excess-fin);extraction.append(dict(record_index=j,root=a.tolist(),tip=b.tolist(),removal_vector=dr.tolist(),continuous_whole_stem_clearance=True,functional_guard_overlap_mm3=overlap))
  assert ((teeth-union(rods))^ban).volume()<1e-6,(pid,'Unrecorded tooth enters hardware clearance')
  todo=list(range(len(free)))
  while todo:
   for k in todo:
    others=union([free[z]for z in todo if z!=k]);dr=np.array(extraction[k]['removal_vector']);ok,_=exact_clear(free[k]-others,others,dr*distance)
    if ok:stem_order.append(extraction[k]['record_index']);todo.remove(k);break
   else:
    group=union([free[z]for z in todo]);solved=False
    for dr in [np.array([0.,0.,-1.])]+[np.array(extraction[z]['removal_vector'])for z in todo]:
     if exact_clear(group,body,dr*distance)[0]:
      stem_order.append(dict(simultaneous_records=[extraction[z]['record_index']for z in todo],vector=dr.tolist()));todo=[];solved=True;break
    assert solved,(pid,'Stem withdrawal sequence blocked',todo)
 vv=np.r_[n['v'],n['fin_v'],n['teeth_v']];assert vv[:,2].min()>-1e-6,(pid,'Geometry below bed');oldvol=float((solid(old['fin_v'],old['fin_f'])+solid(old['teeth_v'],old['teeth_f'])).volume());supvol=float((fin+teeth).volume());lengths=[q['free_vertical_mm']for q in d.get('teeth',[])+d.get('local_route_repairs',[])if'free_vertical_mm'in q]
 r=dict(id=pid,label=sel['label'],parts_npz_sha256=sha,geometric_constraints_passed=True,body_exact_rigid_copy_of_F4=bool(exact),body_rigid_transform_error_mm=err,body_added_from_F4_mm3=added,body_removed_from_F4_mm3=removed,body_change_fit_and_pose_required=not exact,fin_body_intersection_mm3=float((fin^body).volume()),all_fins_bed_rooted=True,fin_count=len(groups),fin_bodies=rows,removal_stages=stages,withdrawal_sweep_distance_mm=distance,all_fin_bodies_have_continuous_removal_path=True,withdrawal_condition='Clear all yellow connector material from the removal path first. Intersecting branches can need more than one cut; the proof is for fin bodies, not scissors access or force.',connected_tooth_components=len(contacts),connector_contacts=contacts,connector_extra_material_in_functional_guard_mm3=guard_volume,removable_fin_material_temporarily_in_functional_guard_mm3=core_guard_volume,temporary_core_policy='Orange fins can traverse empty assembly space only while printing; all must be removed before hardware installation, along the verified path.',support_volume_mm3=supvol,old_support_volume_mm3=oldvol,support_volume_reduction_percent=100*(1-supvol/oldvol)if oldvol else 0,envelope_mm=np.ptp(vv,axis=0).tolist(),neck_free_height_mm=dict(min=min(lengths),median=float(np.median(lengths)),max=max(lengths))if lengths else None,physical_print_tested=pid=='X062',strength_or_thermal_simulation=False)
 r.update(connector_void_policy=d.get('connector_void_policy','strict_functional_clearance'),whole_stem_extraction_verified=d.get('connector_void_policy')=='whole_stem_extraction',extractable_stems=extraction,stem_removal_record_order=stem_order,magnet_entry_extra_connector_volume_mm3=strict_guard_volume)
 put(out,r);np.savez_compressed(folder/'verification/f5_fin_groups.npz',**outgeom);print('F5_GEOMETRY_PASS',pid,sel['label'],len(groups),'removed',round(removed,5),flush=True);return r
if __name__=='__main__':
 ids=sys.argv[1:]or[p.stem for p in(O/'selections').glob('*.json')]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as pool:
  fs={pool.submit(run,pid):pid for pid in ids}
  for f in concurrent.futures.as_completed(fs):
   try:f.result()
   except Exception:traceback.print_exc();print('GEOMETRY_ERROR',fs[f],flush=True)

