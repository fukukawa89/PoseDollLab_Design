from pathlib import Path
r=Path('PoseDoll_HW44_Plan/design/scripts')
p=r/'optimize_revo22_f5_276.py';s=p.read_text();s=s.replace("and (not q[4].get('f5_additions')", "and (not q[4].get('connector_void_policy') or ((O/'candidates'/pid/q[2]/'verification/f5_geometry.json').exists() and json.loads((O/'candidates'/pid/q[2]/'verification/f5_geometry.json').read_text()).get('whole_stem_extraction_verified'))) and (not q[4].get('f5_additions')");p.write_text(s)
p=r/'resolve_revo22_f5_extract341.py';s=p.read_text().replace("if q['native_review_resolved']:return(pid,label,True)\n return(pid,False)","if q['native_review_resolved']:return(pid,'extract341_micro',True)\n return(pid,False)");p.write_text(s)
p=r/'verify_revo22_f5_geometry292.py';s=p.read_text();s=s.replace("from build_revo22_fins import solid,vf,box,union", "from build_revo22_fins import solid,vf,box,union,md");s=s.replace(" if out.exists()and json.loads(out.read_text())['parts_npz_sha256']==sha:return json.loads(out.read_text())", " d=json.loads((folder/'design'/f'{pid}.json').read_text())\n if out.exists()and json.loads(out.read_text())['parts_npz_sha256']==sha and (not d.get('connector_void_policy') or json.loads(out.read_text()).get('whole_stem_extraction_verified')):return json.loads(out.read_text())")
s=s.replace(";assert guard_volume<1e-6,(pid,'Connector in functional space',guard_volume)","\n  if d.get('connector_void_policy')!='whole_stem_extraction':assert guard_volume<1e-6,(pid,'Connector in functional space',guard_volume)")
needle=" vv=np.r_[n['v'],n['fin_v'],n['teeth_v']]"
insert=''' extraction=[];stem_order=[];strict_guard_volume=None
 if d.get('connector_void_policy')=='whole_stem_extraction':
  mn=np.load(folder/'verification/strict_magnet_guards.npz');mb=solid(mn['v'],mn['f'])-body;strict_guard_volume=float((teeth^mb).volume());assert strict_guard_volume<1e-6,(pid,'Magnet entry blocked',strict_guard_volume)
  rods=[];free=[]
  for j,rec in enumerate(d.get('local_route_repairs',[])):
   if rec.get('kind')!='extractable_void_contact_341':continue
   a=np.array(rec['root']);b=np.array(rec['tip']);middle=a+(b-a)*max(0.,1.-rec.get('taper_height_mm',.45)/(b[2]-a[2]));xy=np.array([[-1,-1,0],[1,-1,0],[1,1,0],[-1,1,0]]);tt=union([md.Manifold.hull_points(np.vstack([xy*.4+a,xy*.4+middle])),md.Manifold.hull_points(np.vstack([xy*.4+middle,xy*(rec.get('tip_width_mm',.6)/2)+b]))]);assert(tt-teeth).volume()<1e-5
   excess=tt-body;dr=np.array(rec['stem_removal_vector']);dr/=np.linalg.norm(dr);clear,_=exact_clear(excess,body,dr*distance);assert clear,(pid,'Trapped stem',j);rods.append(tt);free.append(excess-fin);extraction.append(dict(record_index=j,root=a.tolist(),tip=b.tolist(),removal_vector=dr.tolist(),continuous_whole_stem_clearance=True,functional_guard_overlap_mm3=float((excess^ban).volume())))
  assert ((teeth-union(rods))^ban).volume()<1e-6,(pid,'Unrecorded tooth enters hardware clearance')
  todo=list(range(len(free)))
  while todo:
   for k in todo:
    others=union([free[z]for z in todo if z!=k]);dr=np.array(extraction[k]['removal_vector']);ok,_=exact_clear(free[k]-others,others,dr*distance)
    if ok:stem_order.append(extraction[k]['record_index']);todo.remove(k);break
   else:raise AssertionError((pid,'Stem withdrawal sequence blocked',todo))
'''
s=s.replace(needle,insert+needle)
s=s.replace(" put(out,r);np.savez_compressed", " r.update(connector_void_policy=d.get('connector_void_policy','strict_functional_clearance'),whole_stem_extraction_verified=bool(extraction),extractable_stems=extraction,stem_removal_record_order=stem_order,magnet_entry_extra_connector_volume_mm3=strict_guard_volume)\n put(out,r);np.savez_compressed")
p.write_text(s)
