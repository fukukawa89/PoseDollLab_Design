"""Audit O20 changed geometry against frozen O19 CAD in 24 poses."""
from base import *
from connected import adjacent_pairs

def main():
 changes=g.read(OUT/'changes.json');p,m,pr,st,prov=load_o19()
 replacements={r['part']:r for r in changes['replacements']}
 new={k:from_tri_exact(v) for k,v in np.load(OUT/'changed_parts.npz').items()}
 gone=set(changes['removed_stock_parts'])|{k for r in replacements.values() for k in r['replaces']}
 keys=[k for k in p if k not in gone]+list(new)
 sources={k:[k] for k in keys if k not in new};sources.update({k:r['replaces'] for k,r in replacements.items()})
 cases={'assembly':g.ASSEMBLY_POSE,**g.read(H/'mechanical_manifest/revO_pose_cases.json')['cases']}
 rows=[];added=[];contacts=[];neutral=None;adj=adjacent_pairs('quinn')
 def related(a,b):
  ga=set(m[a].get('modules',[m[a]['module']]));gb=set(m[b].get('modules',[m[b]['module']]))
  return m[a]['body']==m[b]['body'] or bool(ga&gb) or any(frozenset((x,y)) in adj for x in ga for y in gb)
 for name,angles in cases.items():
  old,transforms,_,fail,_=position(p,m,angles)
  assert not fail
  current={k:old[k] for k in keys if k not in new}
  current.update({k:g.move(s,transforms[k]) for k,s in new.items()})
  bounds=np.array([current[k].bounding_box() for k in keys]);findings=[];tested=0
  for i,a in enumerate(keys):
   mask=np.all(np.minimum(bounds[i,3:],bounds[i+1:,3:])>np.maximum(bounds[i,:3],bounds[i+1:,:3])+1e-8,axis=1)
   for j in np.flatnonzero(mask)+i+1:
    b=keys[j]
    if a not in new and b not in new:continue
    tested+=1;v=max(0.,float((current[a]^current[b]).volume()))
    if v<.001:continue
    baseline=max(0.,sum(float((old[x]^old[y]).volume()) for x in sources[a] for y in sources[b]))
    row={'pair':[a,b],'O20_overlap_mm3':v,'O19_same_pair_overlap_mm3':baseline,'increase_mm3':v-baseline,'classification':'ADJACENT' if related(a,b) else 'POSE_CONTACT'}
    findings.append(row)
    if v-baseline>.001:
     (added if related(a,b) else contacts).append({'pose':name,**row})
  if name=='neutral':
   lo=bounds[:,:3].min(0);hi=bounds[:,3:].max(0)
   neutral={'min_mm':lo.tolist(),'max_mm':hi.tolist(),'size_mm':(hi-lo).tolist(),'height_mm':float(hi[2]-lo[2]),'model_parts':len(current)}
  rows.append({'pose':name,'bbox_pairs_tested':tested,'findings':findings})
  print('POSE',name,'inherited',len(findings),'new',len(added),flush=True)
 assert neutral['height_mm']<=600
 report={'status':'REGRESSION_PASS_WITH_INHERITED_OVERLAPS' if not added else 'NEW_COLLISIONS_FOUND',
  'scope':'All O20 changed parts vs retained physical geometry in 24 examples. Shared/serial module pairs are ADJACENT. Nonadjacent POSE_CONTACT accepted by the user. Unchanged pairs inherit O19 evidence; not continuous full-domain certification.',
  'poses':rows,'new_collisions':added,'new_nonadjacent_pose_contacts':contacts,'inherited_overlap_cases':sum(bool(r['findings']) for r in rows),
  'regression_tolerance_mm3':.001,'neutral_exact_geometry':neutral,'physical_tested':False,'continuous_collision_proof':False,'manufacturing_release':False,
  'max_added_volume_over_O19_union_mm3':None,
  'service_checks_passed':len(changes['service_checks']),'kinematics_unchanged':True,
  'source_sha256':{str(f.relative_to(H)).replace('\\','/'):g.sha(f) for f in [Path(__file__),OUT/'changes.json',OUT/'changed_parts.npz',H/'generated/revO18/changed_parts.npz']}}
 g.write(OUT/'geometry_verification.json',report)
 if added:raise SystemExit(1)

if __name__=='__main__':main()
