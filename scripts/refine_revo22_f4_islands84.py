"""Classify detached bead regions by their actual footprint, not its rectangular bounds."""
from pathlib import Path
import sys,json,numpy as np,shapely,concurrent.futures,traceback
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from o22_f3_gcode import extract_paths
from o22_cross_section_geometry import polygon
from build_revo22_fins import solid,union,md
from refine_revo22_f4_full_bead import refine
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def coverage(region,previous):return float(region.intersection(previous.buffer(.015)).area/max(region.area,1e-12))
def trial(pid,label):
 p=O/'candidates'/pid/label;d=refine(pid,label);n=np.load(p/'parts'/f'{pid}.npz');it=json.loads((p/'verification/plate_manifest.json').read_text())['items'][0];whole=union([solid(n[v],n[f])for v,f in [('v','f'),('fin_v','fin_f'),('teeth_v','teeth_f')]if len(n[f])]).transform(np.c_[it['rotation_matrix'],it['translation_mm']]);project=p/'projects'/json.loads((p/'verification/local_extrusion.json').read_text())['project'];_,raw=extract_paths(project,arc_tolerance_mm=.025,max_arc_segment_mm=1);a=np.asarray(raw).reshape(-1,9);a=a[a[:,7]==0];zs=np.unique(a[:,5]);rows=[];cache={}
 for q in d['islands']:
  z=q['z_mm'];key=round(z,3)
  if key not in cache:
   ar=a[abs(a[:,5]-z)<.002];xy=np.stack([ar[:,:2],ar[:,3:5]],1);buf=shapely.orient_polygons(shapely.buffer(shapely.linestrings(xy),np.maximum(ar[:,8]/2,.001),quad_segs=3));cs=md.CrossSection([np.round(np.array(g.exterior.coords)[:-1],4)for g in buf if not g.is_empty]);prevz=zs[zs<z-.01][-1];cache[key]=(cs.decompose(),polygon(whole.slice(float(prevz-(z-prevz)/2))))
  components,prev=cache[key];cs=min(components,key=lambda g:np.max(abs(np.array(g.bounds())-np.array(q['bounds_mm']))));assert np.max(abs(np.array(cs.bounds())-q['bounds_mm']))<1e-4;poly=polygon(cs);cov=coverage(poly,prev);rows.append(dict(q,inside_previous_solid_geometry=cov>.995,previous_solid_exact_bead_coverage=cov,classification_basis='Exact deposited bead region, including any holes; rectangular bounding-box coverage is retained only as diagnostic.'))
 external=[q for q in rows if not q['inside_previous_solid_geometry']];d.update(audit_schema='full-bead-v4-exact-island-footprint',islands=rows,external_islands=external,external_island_count=len(external),native_review_resolved=not external and not d['critical_external_runs'],previous_report='full_bead_contacts_v2.json',island_refinement='Uses the actual deposited bead-region polygon rather than its bounding rectangle against the same previous solid slice and unchanged 0.995 coverage threshold / 0.015 mm boundary tolerance. All external free-run tests are unchanged.');(p/'verification/full_bead_contacts_v4.json').write_text(json.dumps(d,indent=2));print('ISLAND84',pid,label,len(external),d['critical_external_count'],[(q.get('previous_solid_bbox_coverage'),q['previous_solid_exact_bead_coverage'])for q in rows],flush=True);return d
if __name__=='__main__':
 from shapely.geometry import Point
 disk=Point(0,0).buffer(1,quad_segs=48);inside=Point(0,0).buffer(1.01,quad_segs=48);hole=inside.difference(Point(0,0).buffer(.9,quad_segs=48));assert coverage(disk,inside)>.995;assert coverage(disk,Point(3,0).buffer(1))<.005;assert coverage(disk,hole)<.995;assert coverage(shapely.box(-1,-1,1,1),inside)<.995
 (O/'island_footprint_controls84.json').write_text(json.dumps({'actual_curved_interior_pass':True,'external_floating_region_rejected':True,'nested_void_rejected':True,'bbox_not_equivalent_to_polygon_demonstrated':True,'all_controls_passed':True},indent=2))
 for s in sys.argv[1:]:trial(*s.split(':'))
