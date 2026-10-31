"""Reuse the established A1 mini PLA project writer; all outputs are T2-only."""
from spring_hinge import *
import printing as p
import concurrent.futures
p.OUT=OUT;p.REVISION=REVISION;p.WORK=ROOT/'output/o24ct2h-slicing'

def main():
    rows={r['id']:r for r in json.loads((OUT/'assembly.json').read_text('utf8'))['parts']}
    plates=[]
    for id,layout in [('P0_H2_fit',[('H2-C01',8,8)]),('P1_H2_sample',[('H2-02',8,8),('H2-01',38,8),('H2-03',38,52)])]:
        plate=dict(id=id,items=[],optional=id.startswith('P0'),replacement=False)
        for part,x,y in layout:
            r=rows[part];plate['items'].append(dict(id=part,stl=r['stl'],offset_mm=[x,y,0],stl_sha256=r['stl_sha256']))
        p.project(plate);plates.append(plate)
    put(OUT/'printing/plates.json',dict(plates=plates,profile='A1 mini / 0.4 mm / PLA / 0.12 mm / 5 walls / 100% infill / auto supports. P0 optional first-fit coupon; P1 contains all three assembly prints.'))
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(p.run,plates))
    put(OUT/'verification/slicing.json',dict(passed=all(r['passed'] for r in results),plates=results,gcode_delivered=False,scope='OrcaSlicer offline import and slice; every object, actual extrusion bounds, placements and zero mesh repair. Print quality unmeasured.'))
    if not all(r['passed'] for r in results):raise SystemExit(1)

if __name__=='__main__':main()
