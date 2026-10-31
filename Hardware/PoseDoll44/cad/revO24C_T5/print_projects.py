from arm_kit import *
import printing as p
p.OUT=OUT;p.REVISION=REVISION;p.WORK=ROOT/'output/o24ct5-slicing'

def main():
 rows=json.loads((OUT/'assembly.json').read_text('utf8'))['parts'];plates=[]
 plate=dict(id='REPRINT_T5_three_parts',items=[],optional=False,replacement=True);x=12
 for id in ['H5-01','R5-01','W5-01']:
  r=next(r for r in rows if r['id']==id);size=np.array(r['print_bounds_mm'][1])-r['print_bounds_mm'][0]
  plate['items'].append(dict(id=id,stl=r['stl'],offset_mm=[x,15,0],stl_sha256=r['stl_sha256']));x+=size[0]+12
 assert x<172
 p.project(plate);plates.append(plate)
 put(OUT/'printing/plates.json',dict(plates=plates,profile='A1 mini / 0.4mm / PLA / .12mm / 5 walls / 100% infill / automatic supports / 3mm brim. Three replacement monolithic housings. Keep print orientations; slide metal through ports only after removing support and burrs.'))
 result=p.run(plate)
 put(OUT/'verification/slicing.json',dict(passed=result['passed'],geometry_sha256=sha(OUT/'assembly_meshes.npz'),plates=[result],gcode_delivered=False,scope='Offline Orca import and extrusion bounds, zero mesh repair. Physical fit and internal support removal need actual print inspection.'))
 if not result['passed']:raise SystemExit(1)

if __name__=='__main__':main()
