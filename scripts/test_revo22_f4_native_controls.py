from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from verify_revo22_f4_local_extrusion import check
from o22_cross_section_geometry import polygon
from build_revo22_fins import md
D=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4/audit/controls_v2';D.mkdir(parents=True,exist_ok=True)
outer=md.CrossSection.square([10,10]);hole=md.CrossSection.square([8,8]).translate([1,1]);island=md.CrossSection.square([2,2]).translate([4,4]);cs=outer-hole+island
assert abs(polygon(cs).area-40)<1e-8
touch=md.CrossSection.square([2,2])+md.CrossSection.square([2,2]).translate([2,2])-md.CrossSection.square([1,1]).translate([.5,.5])
assert abs(polygon(touch).area-7)<1e-8
def test(name,base,top,split=False):
 lines=['G90','M83','; LAYER_CHANGE',';Z:0.2',';HEIGHT:0.2',';WIDTH:0.42',';TYPE:Outer wall']
 for x0,y0,x1,y1 in base:lines +=[f'G0 X{x0} Y{y0} Z0.2',f'G1 X{x1} Y{y1} E0.1']
 lines +=['; LAYER_CHANGE',';Z:0.4',';HEIGHT:0.2',';TYPE:Outer wall']
 for i,(x0,y0,x1,y1) in enumerate(top):
  if not i or not split:lines.append(f'G0 X{x0} Y{y0} Z0.4')
  if i and split:lines.append(';TYPE:Overhang wall')
  lines.append(f'G1 X{x1} Y{y1} Z0.4 E0.1')
 p=D/(name+'.gcode');p.write_text('\n'.join(lines),encoding='utf8');return check(p,D/(name+'.json'))
rows={}
rows['bridge']=test('bridge',[(0,0,2,0),(18,0,20,0)],[(0,0,20,0)])
rows['cantilever']=test('cantilever',[(0,0,2,0)],[(0,0,20,0)])
rows['detached']=test('detached',[(0,0,2,0)],[(10,0,12,0)])
rows['split']=test('split',[(0,0,2,0),(18,0,20,0)],[(0,0,10,0),(10,0,20,0)],True)
rows['slope']=test('slope',[(0,0,20,0)],[(0,.2,20,.2)])
rows['nested']=test('nested',[(0,0,10,0),(10,0,10,10),(10,10,0,10),(0,10,0,0),(4,5,6,5)],[(4,5,6,5)])
assert rows['bridge']['max_unresolved_span_mm']>15 and rows['cantilever']['max_unresolved_span_mm']>15
assert len(rows['detached']['detached_bead_regions'])==1
assert rows['bridge']['unresolved_count']==rows['split']['unresolved_count'] and rows['split']['max_unresolved_span_mm']>15
assert rows['slope']['unresolved_count']==rows['nested']['unresolved_count']==0
(D/'summary.json').write_text(json.dumps({'passed':True,'schema':'local-extrusion-v2-preserve-nested-islands','controls':list(rows),'nested_cross_section_exact_area_mm2':40},indent=2),encoding='utf8')
print('ALL_V2_CONTROLS_PASS',flush=True)

