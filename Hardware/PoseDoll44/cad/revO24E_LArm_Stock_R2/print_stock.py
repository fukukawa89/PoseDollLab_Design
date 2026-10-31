from build_stock import *
import printing as printer
def run():
 printer.OUT=OUT;printer.REVISION='O24E_LArm_Stock_R2';printer.WORK=OUT/'verification/slicer_work'
 kit=load(OUT/'kit.json');plates=[];remaining=list(kit['structural_parts'])
 while remaining:
  plate=dict(id=f'STOCK_ARM_{len(plates)+1:02d}',items=[],optional=False,replacement=False);free=[(0.,0.,172.,172.)];left=[]
  for r in sorted(remaining,key=lambda r:-np.prod(np.ptp(r['print_bounds_mm'],axis=0)[:2])):
   w,h=np.ptp(r['print_bounds_mm'],axis=0)[:2]+8
   choices=[(min(fw-w,fh-h),max(fw-w,fh-h),x,y) for x,y,fw,fh in free if fw>=w and fh>=h]
   if not choices:left.append(r);continue
   _,_,x,y=min(choices);new=[]
   for fx,fy,fw,fh in free:
    if x>=fx+fw or x+w<=fx or y>=fy+fh or y+h<=fy:new.append((fx,fy,fw,fh));continue
    if x>fx:new.append((fx,fy,x-fx,fh))
    if x+w<fx+fw:new.append((x+w,fy,fx+fw-x-w,fh))
    if y>fy:new.append((fx,fy,fw,y-fy))
    if y+h<fy+fh:new.append((fx,y+h,fw,fy+fh-y-h))
   free=[f for i,f in enumerate(new) if not any(j!=i and f[0]>=g[0] and f[1]>=g[1] and f[0]+f[2]<=g[0]+g[2] and f[1]+f[3]<=g[1]+g[3] and (f!=g or j<i) for j,g in enumerate(new))]
   plate['items'].append(dict(id=r['part_number'],stl=r['stl'],offset_mm=[x+8,y+8,0],stl_sha256=sha(OUT/r['stl'])))
  assert plate['items'];printer.project(plate);plates.append(plate);remaining=left
 put(OUT/'printing/plates.json',dict(plates=plates,profile='A1 mini / 0.4 mm / PLA / 0.12 mm / 5 walls / 100% infill / auto support / 3 mm brim'))
 for p in plates:
  result=printer.run(p);put(OUT/'verification'/f'slice_{p["id"]}.json',result);assert result['passed']
if __name__=='__main__':run()
