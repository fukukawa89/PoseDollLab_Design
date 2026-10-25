from arm_kit import *
import printing as p
import concurrent.futures
p.OUT=OUT;p.REVISION=REVISION;p.WORK=ROOT/'output/o24ct3-slicing'

def main():
 rows=json.loads((OUT/'assembly.json').read_text('utf8'))['parts'];plates=[]
 groups=[('P0_fit',lambda r:r['station']=='C'),('P1_H_elbow',lambda r:r['station']=='H' and not r['bench_only']),('P2_R_roll',lambda r:r['station']=='R' and not r['bench_only']),('P3_W_wrist',lambda r:r['station']=='W' and not r['bench_only']),('P4_removable_test_tools',lambda r:r['bench_only'] and r['station']!='C')]
 for name,pred in groups:
  items=sorted([r for r in rows if r['printable'] and pred(r)],key=lambda r:-(r['print_bounds_mm'][1][1]));x=8;y=8;rowh=0;plate=dict(id=name,items=[],optional=name.startswith('P0'),replacement=False)
  for r in items:
   w,h,z=np.array(r['print_bounds_mm'][1])-r['print_bounds_mm'][0]
   if x+w>172:x=8;y+=rowh+9;rowh=0
   assert y+h<172,(name,r['id'],y,h)
   plate['items'].append(dict(id=r['id'],stl=r['stl'],offset_mm=[x,y,0],stl_sha256=r['stl_sha256']))
   x+=w+9;rowh=max(rowh,h)
  p.project(plate);plates.append(plate)
 put(OUT/'printing/plates.json',dict(plates=plates,profile='A1 mini / 0.4mm / PLA / .12mm / 5 walls / 100% infill / automatic supports / 3mm brim. P1-P3 are actual arm parts. P4 contains removable loading/holding tools only. P0 is an optional fit-first coupon.'))
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(p.run,plates))
 put(OUT/'verification/slicing.json',dict(passed=all(r['passed'] for r in results),geometry_sha256=sha(OUT/'assembly_meshes.npz'),plates=results,gcode_delivered=False,scope='Offline OrcaSlicer imported all objects; zero mesh repairs, unchanged placement and actual extrusion bounds. Not sent to any printer.'))
 if not all(r['passed'] for r in results):raise SystemExit(1)
if __name__=='__main__':main()
