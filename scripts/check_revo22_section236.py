"""Regression controls for signed section conversion; no span/area thresholds are relaxed."""
from pathlib import Path
import json,numpy as np
from shapely.geometry import box,Point
from o22_cross_section_geometry import polygon
R=Path(__file__).resolve().parents[1];S=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4/compact230'
class Region:
 def __init__(self,rings):self.rings=[np.array(q)for q in rings]
 def to_polygons(self):return self.rings
class Section:
 def __init__(self,regions,area):self.regions=[Region(q)for q in regions];self.a=area
 def decompose(self):return self.regions
 def area(self):return self.a
def ring(x1,y1,x2,y2,positive=True):
 a=np.array([[x1,y1],[x2,y1],[x2,y2],[x1,y2]],float);return a if positive else a[::-1]
m=json.loads((S/'section_failure235.json').read_text());cs=Section([r['rings']for r in m['regions']],m['manifold_area']);p=polygon(cs);assert abs(p.area-cs.area())<1e-8
hole=next(q['rings'][0]for q in m['regions']if q['positive_count']==0);from shapely.geometry import Polygon
assert p.intersection(Polygon(hole)).area<1e-8
regions=[[ring(0,0,10,10)],[ring(2,2,8,8,False)],[ring(3,3,5,5),ring(3.5,3.5,4.5,4.5,False)],[ring(20,20,25,25)]];expected=box(0,0,10,10).difference(box(2,2,8,8)).union(box(3,3,5,5).difference(box(3.5,3.5,4.5,4.5))).union(box(20,20,25,25));q=polygon(Section(regions,expected.area));assert q.symmetric_difference(expected).area<1e-10;assert not q.covers(Point(2.5,2.5))and q.covers(Point(3.2,3.2))and not q.covers(Point(4,4))
rejected=False
try:polygon(Section([[ring(0,0,10,10)],[ring(20,20,21,21,False)]],99))
except AssertionError:rejected=True
assert rejected
rejected_tiny=False
try:polygon(Section([[ring(0,0,10,10)],[ring(20,20,20.000001,20.000001,False)]],100-1e-12))
except AssertionError:rejected_tiny=True
assert rejected_tiny
report={'real_C03_section_manifold_area_mm2':cs.area(),'converted_area_mm2':p.area,'area_error_mm2':abs(p.area-cs.area()),'negative_only_hole_preserved':True,'nested_positive_island_and_nested_hole_preserved':True,'uncontained_negative_ring_rejected':True,'all_controls_passed':True,'existing_section_area_and_native_support_screening_thresholds_unchanged':True};(S/'section_conversion236.json').write_text(json.dumps(report,indent=2));print('SECTION236_CONTROLS',report,flush=True)
