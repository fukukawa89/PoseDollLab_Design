"""Isolated trial: remove entire tiny disconnected slice tips until they join a larger section."""
import sys,json,os,shutil,numpy as np,concurrent.futures
import shapely
from shapely.geometry import box,Point
from o22_cross_section_geometry import polygon
import o22f6_holeclear as h
from o22f6_route import collect
BASE=h.WORK;SOURCE=h.OUT

def pieces(pg):return [x for x in getattr(pg,'geoms',[pg])if x.geom_type=='Polygon'and not x.is_empty]
def extrusion(pg,z,height):
 pg=shapely.orient_polygons(pg);rings=[]
 for pp in pieces(pg):
  rings.append(np.asarray(pp.exterior.coords)[:-1]);rings.extend(np.asarray(q.coords)[:-1]for q in pp.interiors)
 return h.md.CrossSection(rings).extrude(height).translate([0,0,z])
def trial(pid):
 label=pid+'_slice_tip1';root=BASE/'tip_trials'/label;stage=root/'batch';work=root/'audit';print('TIP_START',pid,flush=True)
 for sub in ['parts','design']:
  (stage/sub).mkdir(parents=True,exist_ok=True)
  for p in(SOURCE/sub).glob('*'):
   dest=stage/sub/p.name
   if not dest.exists():os.link(p,dest)
 n=dict(np.load(SOURCE/f'parts/{pid}.npz'));d=json.loads((SOURCE/f'design/{pid}.json').read_text());gn=np.load(BASE/f'guards/{pid}.npz');guard=h.solid(gn['v'],gn['f']);old=h.solid(n['v'],n['f']);fin=h.solid(n['fin_v'],n['fin_f']);teeth=h.solid(n['teeth_v'],n['teeth_f']);whole=old+fin+teeth;reports,_=collect();q=reports[pid];cuts=[];records=[]
 p=next(p for p in json.loads((h.SRC/'manifest.json').read_text())['plates']if any(it['id']==pid for it in p['items']));lh=p['profile']['layer'];seen=[]
 for a in q['external_islands']:
  b=np.array(a['bounds_mm']);z=a['z_mm'];center=(b[:2]+b[2:])/2
  if any(abs(z-r[0])<.02 and np.linalg.norm(center-r[1])<.1 for r in seen):continue
  seen.append((z,center));last=Point(center).buffer(.35);local=[];hist=[]
  for zz in np.arange(z-lh/2,z+3.,.1):
   pg=polygon(whole.slice(float(zz)));ps=[c for c in pieces(pg)if c.distance(last)<.1];
   if not ps:hist.append(dict(z=zz,stop='lost_component'));break
   chosen=shapely.union_all(ps)
   if chosen.area>6. or chosen.difference(last.buffer(.7)).area>1.:hist.append(dict(z=zz,stop='merged_into_large_section',area=chosen.area));break
   cut=extrusion(chosen.buffer(.12,join_style=2),zz-.06,.12);local.append(cut);hist.append(dict(z=zz,area=chosen.area));last=chosen
  if not local:continue
  carve=h.union(local);bv=float((old^carve).volume());tv=float((teeth^carve).volume());fv=float((fin^carve).volume());rec=dict(initial_z=z,bounds_mm=b.tolist(),body_mm3=bv,teeth_mm3=tv,fin_mm3=fv,track=hist)
  if bv>4. or not hist[-1].get('stop'):rec['rejected']='too_large_or_unbounded'
  else:cuts.append(carve)
  records.append(rec);print('TIP_TRACK',pid,z,round(bv,4),len(hist),hist[-1],rec.get('rejected'),flush=True)
 carve=h.union(cuts);body=old-carve;newfin=fin-carve;newteeth=teeth-carve
 for i in range(3):
  newteeth=h.union([c for c in h.material_components(newteeth)if(c^body).volume()>.001 and(c^newfin).volume()>.001]);newfin=h.union([c for c in h.material_components(newfin)if(c^newteeth).volume()>.001 and c.bounding_box()[2]<1e-6])
 removed=float((old-body).volume());checks=dict(body_components_before=len(h.material_components(old)),body_components_after=len(h.material_components(body)),whole_components=len(h.material_components(body+newfin+newteeth)),added_body_mm3=float((body-old).volume()),guard_overlap_mm3=float(((newfin+newteeth)^guard).volume()),removed_body_mm3=removed,removed_fraction=removed/old.volume());h.put(root/'geometry.json',dict(records=records,checks=checks));print('TIP_GEOMETRY',pid,checks,flush=True)
 assert checks['body_components_before']==checks['body_components_after']==checks['whole_components'];assert checks['added_body_mm3']<1e-6 and checks['guard_overlap_mm3']<1e-6 and removed/old.volume()<.005
 for v,f,s in [('v','f',body),('fin_v','fin_f',newfin),('teeth_v','teeth_f',newteeth)]:n[v],n[f]=h.vf(s)
 dest=stage/f'parts/{pid}.npz';dest.unlink();np.savez_compressed(dest,**n);d['f6_trial_tip_removal']=dict(records=records,checks=checks,permanent_geometry_changed=True,physical_tested=False);dest=stage/f'design/{pid}.json';dest.unlink();h.put(dest,d);h.save_mesh(root/f'guards/{pid}.npz',guard+carve);work.mkdir(parents=True,exist_ok=True);shutil.copy2(BASE/'profile_overrides.json',work/'profile_overrides.json');h.OUT=stage;h.WORK=work;h.TARGET_PART_IDS=[pid];h.build_plate(p);r=h.screen_plate(p);res=dict(id=pid,islands=r['external_island_count'],critical=r['critical_external_count'],removed_mm3=removed);h.put(root/'result.json',res);print('TIP_RESULT',res,flush=True)
if __name__=='__main__':
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as pool:
  for result in pool.map(trial,sys.argv[1:]or['P130','X046']):pass