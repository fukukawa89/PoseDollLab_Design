from common import *
import printing as printer
import concurrent.futures

def run():
    printer.OUT=OUT;printer.REVISION='O24E_LArm_Sensing_R5';printer.WORK=OUT/'verification/slicer_work'
    kit=load(OUT/'kit.json');plates=[]
    groups=[('R5_UPGRADE_MAIN',[r for r in kit['structural_parts'] if r.get('reprint')]),('R5_SENSORS',[r for r in kit['structural_parts'] if r['new_accessory']]+load(OUT/'tooling/R5_new_tools.json')['parts']),('OPTION_R4_REUSE',[r for r in kit['structural_parts'] if r['reuse_R4_byte_identical']])]
    for name,items in groups:
        remaining=list(items);n=0
        while remaining:
            n+=1;plate=dict(id=name+'_'+str(n),items=[],optional=name.startswith('OPTION'),replacement=name.startswith('R5_UPGRADE'));free=[(8.,8.,164.,164.)];left=[]
            for r in sorted(remaining,key=lambda r:-np.prod(np.ptp(r['print_bounds_mm'],axis=0)[:2])):
                w,h=np.ptp(r['print_bounds_mm'],axis=0)[:2]+8
                choices=[(min(fw-w,fh-h),x,y) for x,y,fw,fh in free if fw>=w and fh>=h]
                if not choices:left.append(r);continue
                _,x,y=min(choices);new=[]
                for fx,fy,fw,fh in free:
                    if x>=fx+fw or x+w<=fx or y>=fy+fh or y+h<=fy:new.append((fx,fy,fw,fh));continue
                    if x>fx:new.append((fx,fy,x-fx,fh))
                    if x+w<fx+fw:new.append((x+w,fy,fx+fw-x-w,fh))
                    if y>fy:new.append((fx,fy,fw,y-fy))
                    if y+h<fy+fh:new.append((fx,y+h,fw,fy+fh-y-h))
                free=[f for i,f in enumerate(new) if not any(j!=i and f[0]>=g[0] and f[1]>=g[1] and f[0]+f[2]<=g[0]+g[2] and f[1]+f[3]<=g[1]+g[3] and (f!=g or j<i) for j,g in enumerate(new))]
                plate['items'].append(dict(id=r['part_number'],stl=r['stl'],offset_mm=[x,y,0],stl_sha256=sha(OUT/r['stl'])))
            assert plate['items'];printer.project(plate);plates.append(plate);remaining=left
    put(OUT/'printing/plates.json',dict(plates=plates,selection='R4 upgrade: print MAIN and SENSORS only (5 replacement main + 29 accessory pieces + 2 reusable tools J003/J004 = 36 pieces). OPTION_R4_REUSE is for a new arm, not an upgrade.',profile='A1 mini / 0.4 mm / PLA / 0.12 mm / 5 walls / 100% infill / auto support / 3 mm brim',R4_tools='J001 and J002 reused; tooling/ has their original files.'))
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(printer.run,plates))
    put(OUT/'verification/slicing.json',dict(passed=all(r['passed'] for r in results),plates=results,printed_or_sent_to_printer=False))
    assert all(r['passed'] for r in results)

if __name__=='__main__':run()
