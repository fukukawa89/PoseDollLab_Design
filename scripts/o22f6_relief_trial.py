"""Candidate subtractive relief at hole-adjacent first-layer tips. Never edits release body."""
import sys,json,os,shutil,numpy as np,concurrent.futures
import o22f6_holeclear as h
from o22f6_route import collect
BASE=h.WORK;SOURCE=h.OUT

def trial(pid):
 label=pid+'_micro_relief2';print('RELIEF_START',pid,flush=True);root=BASE/'relief_trials'/label;stage=root/'batch';work=root/'audit'
 for sub in ['parts','design']:
  (stage/sub).mkdir(parents=True,exist_ok=True)
  for p in (SOURCE/sub).glob('*'):
   dest=stage/sub/p.name
   if not dest.exists():os.link(p,dest)
 n=dict(np.load(SOURCE/f'parts/{pid}.npz'));d=json.loads((SOURCE/f'design/{pid}.json').read_text());gn=np.load(BASE/f'guards/{pid}.npz');guard=h.solid(gn['v'],gn['f']);old=h.solid(n['v'],n['f']);body=old;fin=h.solid(n['fin_v'],n['fin_f']);teeth=h.solid(n['teeth_v'],n['teeth_f']);reports,_=collect();q=reports[pid];cuts=[];records=[]
 p=next(p for p in json.loads((h.SRC/'manifest.json').read_text())['plates']if any(it['id']==pid for it in p['items']));lh=p['profile']['layer'];seen=[]
 for a in q['external_islands']:
  b=np.array(a['bounds_mm']);z=a['z_mm'];center=(b[:2]+b[2:])/2
  if any(abs(z-r[0])<.02 and np.linalg.norm(center-r[1])<.1 for r in seen):continue
  seen.append((z,center));lo=b[:2]-.12;hi=b[2:]+.12;bottom=z-lh*2-.02;mid=z+.02;rise=max(.3,float(min(hi-lo))/2);pts=[]
  for zz,aa,bb in [(bottom,lo,hi),(mid,lo,hi),(mid+rise,center-.06,center+.06)]:
   for x,y in [(aa[0],aa[1]),(bb[0],aa[1]),(bb[0],bb[1]),(aa[0],bb[1])]:pts.append([x,y,zz])
  cut=h.md.Manifold.hull_points(np.array(pts));removed=old^cut;v=float(removed.volume())
  if v<1e-5:continue
  if (removed ^ guard).volume() > 1e-6: raise AssertionError('body/guard overlap')
  if v>1.5:records.append(dict(z=z,skipped='exceeds_local_relief_cap',volume=v));continue
  cuts.append(cut);records.append(dict(z=z,bounds_mm=b.tolist(),rise_mm=rise,removed_body_mm3=v,reason='Small hole-adjacent first-layer tip, subtractive transition only'))
 print('CUTS',pid,len(cuts),records,flush=True);carve=h.union(cuts);body=old-carve;guard+=carve;newfin=fin-carve;newteeth=teeth-carve
 for i in range(2):
  print('CLEANUP',pid,i,flush=True)
  newteeth=h.union([c for c in h.material_components(newteeth)if(c^body).volume()>.001 and(c^newfin).volume()>.001]);newfin=h.union([c for c in h.material_components(newfin)if(c^newteeth).volume()>.001 and c.bounding_box()[2]<1e-6])
 assert len(h.material_components(body))==len(h.material_components(old));assert(body-old).volume()<1e-6;assert((newfin+newteeth)^guard).volume()<1e-6;assert len(h.material_components(body+newfin+newteeth))==len(h.material_components(body));removed=float((old-body).volume());assert removed/old.volume()<.002
 for v,f,s in [('v','f',body),('fin_v','fin_f',newfin),('teeth_v','teeth_f',newteeth)]:n[v],n[f]=h.vf(s)
 dest=stage/f'parts/{pid}.npz';dest.unlink();np.savez_compressed(dest,**n);d['f6_trial_hole_relief']=dict(records=records,removed_body_mm3=removed,removed_fraction=removed/old.volume(),permanent_geometry_changed=True,only_subtractive=True,guard_adjacency_check_pending=True,physical_tested=False);dest=stage/f'design/{pid}.json';dest.unlink();h.put(dest,d);h.save_mesh(root/f'guards/{pid}.npz',guard);h.put(root/'relief_report.json',d['f6_trial_hole_relief']);work.mkdir(parents=True,exist_ok=True);shutil.copy2(BASE/'profile_overrides.json',work/'profile_overrides.json')
 h.OUT=stage;h.WORK=work;h.TARGET_PART_IDS=[pid];h.build_plate(p);r=h.screen_plate(p);result=dict(id=pid,removed_mm3=removed,islands=r['external_island_count'],critical=r['critical_external_count']);h.put(root/'result.json',result);print('RELIEF_RESULT',result,flush=True)
if __name__=='__main__':
 with concurrent.futures.ProcessPoolExecutor(max_workers=1)as pool:
  for result in pool.map(trial,sys.argv[1:]or['P130','X046','P095']):pass