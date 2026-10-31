"""Complete F3 support-coverage re-audit. Connected overhangs are never ignored.
Geometry diagnostics, not physical print/force certification.
"""
from pathlib import Path
import sys,json,hashlib,time,concurrent.futures,traceback
import numpy as np,trimesh
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,union,polygon
from explore_revo22_f3 import surface_samples
from scipy.spatial import cKDTree
import manifold3d as md
B=R/'Hardware/PoseDoll44/bench/revO22';SOURCE=B/'O22F3_Release';O=B/'a1mini_fins_v4';AUDIT=O/'audit/baseline'
for d in [O,AUDIT,AUDIT/'figures'] : d.mkdir(parents=True,exist_ok=True)
HEIGHT=.2;ALLOWANCE=.2;AREA_TOL=.02

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def svg_section(current,previous,bad,path,title):
 from shapely.geometry import Polygon
 from shapely.ops import unary_union
 from shapely import make_valid
 def safe_polygon(cs):
  rings=cs.to_polygons();pos=[];neg=[]
  for q in rings:
   q=np.asarray(q);sgn=np.sum(q[:,0]*np.roll(q[:,1],-1)-np.roll(q[:,0],-1)*q[:,1]);p=make_valid(Polygon(q));(pos if sgn>0 else neg).append(p)
  return unary_union(pos).difference(unary_union(neg))
 shapes=[safe_polygon(g) for g in [current,previous,bad]];bounds=shapes[0].bounds
 if len(bounds)!=4:return
 x0,y0,x1,y1=bounds;pad=2;x0-=pad;y0-=pad;x1+=pad;y1+=pad;scale=min(920/(x1-x0),650/(y1-y0));ox=40-x0*scale;oy=770+y0*scale
 def paths(shape,color,opacity):
  out=[]
  for p in getattr(shape,'geoms',[shape]):
   if p.geom_type!='Polygon':continue
   d=[]
   for ring in [p.exterior,*p.interiors]:
    q=np.asarray(ring.coords);d.append('M'+' L'.join(f'{ox+x*scale:.3f},{oy-y*scale:.3f}' for x,y in q)+' Z')
   out.append(f'<path d="{" ".join(d)}" fill="{color}" fill-opacity="{opacity}" fill-rule="evenodd"/>')
  return ''.join(out)
 doc=f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="840"><rect width="100%" height="100%" fill="white"/><g font-family="Segoe UI,Microsoft YaHei,sans-serif" fill="#233c48"><text x="36" y="36" font-size="24">{title}</text><text x="36" y="69" font-size="16">灰：前层完整实体　蓝：当前本体　红：超出前层外扩 0.20 mm 的部分</text><text x="36" y="96" font-size="16">逐层局部覆盖检查；红色表示需处理或进一步核对，不等同于已模拟坍塌。</text></g>'
 doc+=paths(shapes[1],'#aab5af',.8)+paths(shapes[0],'#2a7da3',.75)+paths(shapes[2],'#d6273a',1)
 doc+='<text x="36" y="817" font-family="Segoe UI,Microsoft YaHei,sans-serif" font-size="15">模型切片截面；层高 0.20 mm。连接到侧壁不会使未承托区域免检。</text></svg>'
 path.write_text(doc,encoding='utf8')

def controls():
 # Rectangular roofs attached to one or two walls must both be flagged.
 prev=md.CrossSection.square([2,5]);one=md.CrossSection.square([20,5]);two_prev=prev+prev.translate([18,0]);bad=one-two_prev.offset(ALLOWANCE)
 self_prev=md.CrossSection.square([8,5]);self_next=self_prev.translate([.19,0])
 assert (one-prev.offset(ALLOWANCE)).area()>80
 assert bad.area()>70
 assert (self_next-self_prev.offset(ALLOWANCE)).area()<1e-6
 return {'one_sided_overhang_detected':True,'roof_connected_to_both_sides_detected':True,'self_supporting_0p19_shift_at_0p2_height_not_flagged':True,'passed':True}

def audit(pid,source=SOURCE,out=AUDIT):
 start=time.time();p=source/'reference/parts'/f'{pid}.npz' if (source/'reference/parts').exists() else source/'parts'/f'{pid}.npz'
 dp=source/'reference/design'/f'{pid}.json' if (source/'reference/design').exists() else source/'design'/f'{pid}.json'
 n=np.load(p);d=json.loads(dp.read_text(encoding='utf8'));s=solid(n['v'],n['f']);fin=solid(n['fin_v'],n['fin_f']) if len(n['fin_f']) else md.Manifold();teeth=solid(n['teeth_v'],n['teeth_f']) if len(n['teeth_f']) else md.Manifold();whole=s+fin+teeth
 # Use full-volume overlap, not a contact-point radius, for layer coverage.
 previous=whole.slice(.1);rows=[];worst=None;maxarea=0.;total=0.;height=whole.bounding_box()[5]
 for z in np.arange(.3,height,.2):
  z=float(z);curr=s.slice(z);excess=curr-previous.offset(ALLOWANCE,circular_segments=16);patches=[]
  for q in excess.decompose():
   area=q.area()
   if area>AREA_TOL:patches.append({'area_mm2':float(area),'bounds_mm':list(q.bounds())})
  if patches:
   area=sum(q['area_mm2'] for q in patches);rows.append({'slice_z_mm':round(z,3),'nominal_gcode_z_mm':round(z+.1,3),'excess_area_mm2':area,'patches':patches});total+=area
   if area>maxarea:worst=(curr,previous,excess,z);maxarea=area
  previous=whole.slice(z)
 # Keep inaccessible low-angle faces in the report. They were previously dropped from the score.
 pts,w,critical,face_ids=surface_samples(n['v'],n['f']);mask=critical;pts=pts[mask];w=w[mask]
 blocked=np.zeros(len(pts),bool)
 if len(pts):
  tm=trimesh.Trimesh(n['v'],n['f'],process=False)
  hit,ri,_=tm.ray.intersects_location(pts-[0,0,.04],np.tile([0,0,-1.],(len(pts),1)),multiple_hits=False);blocked[ri]=True
 cp=np.asarray([t['contact_point_mm'] for t in d['teeth']]).reshape(-1,3)
 distances=cKDTree(cp).query(pts)[0] if len(cp) and len(pts) else np.full(len(pts),999.)
 uncovered=distances>3.0
 roots=[{'minimum_z_mm':float(q.bounding_box()[2]),'bed_section_mm2':float(q.slice(.1).area())} for q in fin.decompose()]
 row={'id':pid,'part':d['part'],'npz_sha256':sha(p),'height_mm':float(height),'all_fin_components_reach_bed':all(r['minimum_z_mm']<1e-5 and r['bed_section_mm2']>0 for r in roots),'fin_part_overlap_mm3':float((fin^s).volume()),'tooth_count':len(d['teeth']),'layer_height_mm':HEIGHT,'previous_layer_xy_allowance_mm':ALLOWANCE,'patch_area_tolerance_mm2':AREA_TOL,'critical_down_surface_area_mm2':float(w.sum()),'critical_area_blocked_from_bed_mm2':float(w[blocked].sum()),'critical_area_farther_than_3mm_from_contact_mm2':float(w[uncovered].sum()),'critical_blocked_and_far_from_contact_mm2':float(w[blocked&uncovered].sum()),'contact_radius_is_diagnostic_only_not_acceptance':True,'flagged_layer_count':len(rows),'max_local_excess_area_mm2':maxarea,'sum_layer_excess_area_mm2':total,'layers':rows,'needs_support_coverage_review':bool(rows),'elapsed_s':time.time()-start}
 if worst is not None:svg_section(*worst[:3],out/'figures'/f'{pid}.svg',f'{pid} · 本体覆盖最差层 Z={worst[3]+.1:.2f} mm')
 (out/f'{pid}.json').write_text(json.dumps(row,ensure_ascii=False,indent=2),encoding='utf8')
 print(pid,'layers',len(rows),'max',round(maxarea,3),'blocked',round(row['critical_area_blocked_from_bed_mm2'],2),'s',round(row['elapsed_s'],1),flush=True)
 return row

def one(pid):
 try:return audit(pid)
 except Exception:return {'id':pid,'error':traceback.format_exc()}

def main():
 c=controls();g=json.loads((SOURCE/'verification/geometry_final.json').read_text(encoding='utf8'));ids=sorted(q['id'] for q in g['parts']);assert len(ids)==150
 rows=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=3) as pool:
  pending={pool.submit(one,p):p for p in ids}
  for f in concurrent.futures.as_completed(pending):
   rows.append(f.result());(AUDIT/'progress.json').write_text(json.dumps({'completed':len(rows),'total':len(ids),'parts':sorted(rows,key=lambda q:q['id'])},ensure_ascii=False,indent=2),encoding='utf8')
 errors=[q for q in rows if 'error' in q];assert not errors,errors
 rows.sort(key=lambda q:(-q['max_local_excess_area_mm2'],-q['critical_blocked_and_far_from_contact_mm2']))
 report={'version':'O22-F4 audit baseline of frozen F3','source_types':150,'controls':c,'method':'Every current-body cross-section is differenced against the preceding complete body+fin+tooth section expanded by 0.20 mm at 0.20 mm layer height. Partial unsupported portions are retained even when the overall cross-section touches a sidewall. Bed-inaccessible critical faces are never discarded from the report. This conservative screen requires local bridging/overhang resolution; it is not print or force certification.','parts_requiring_local_review':sum(q['needs_support_coverage_review'] for q in rows),'parts_without_excess_above_tolerance':sum(not q['needs_support_coverage_review'] for q in rows),'source_geometry_unchanged_during_audit':True,'parts':rows}
 (AUDIT/'all_parts.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print('ALL_PARTS',len(rows),'REVIEW',report['parts_requiring_local_review'],flush=True)
if __name__=='__main__':main()
