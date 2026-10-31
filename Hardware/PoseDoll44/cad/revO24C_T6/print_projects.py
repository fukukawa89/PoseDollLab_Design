from arm_kit import *
import printing as p
p.OUT=OUT;p.REVISION=REVISION;p.WORK=ROOT/'output/o24ct6-slicing'

def main():
 rows=json.loads((OUT/'assembly.json').read_text('utf8'))['parts'];plates=[]
 for name,ids in [('REPRINT_T6_three_parts',['H6-01','R6-01','W6-01']),('FIT_T6_locknut_coupon',['C6-01'])]:
  plate=dict(id=name,items=[],optional=name.startswith('FIT'),replacement=name.startswith('REPRINT'));x=12
  for id in ids:
   r=next(r for r in rows if r['id']==id);size=np.array(r['print_bounds_mm'][1])-r['print_bounds_mm'][0]
   plate['items'].append(dict(id=id,stl=r['stl'],offset_mm=[x,15,0],stl_sha256=r['stl_sha256']));x+=size[0]+12
  assert x<172
  p.project(plate);plates.append(plate)
 put(OUT/'printing/plates.json',dict(plates=plates,profile='A1 mini / .4mm / PLA / .12mm / 5 walls / 100% infill / auto support / 3mm brim. Three replacement housings; separate optional fit coupon.'))
 results=[p.run(plate) for plate in plates]
 put(OUT/'verification/slicing.json',dict(passed=all(r['passed'] for r in results),geometry_sha256=sha(OUT/'assembly_meshes.npz'),plates=results,gcode_delivered=False,scope='Offline Orca import and toolpaths; physical support removal and fit need trial print.'))
 if not all(r['passed'] for r in results):raise SystemExit(1)
if __name__=='__main__':main()
