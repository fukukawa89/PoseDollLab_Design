"""Refresh only the changed P3 plate and new two-cup repair plate."""
from printing import *

def main():
    plans=load(OUT/'printing/plates.json');plates=plans['plates']
    rows={p['id']:p for p in load(OUT/'assembly.json')['parts']}
    affected=[]
    for plate in plates:
        if plate['id']!='P3_wrist_1':continue
        for item in plate['items']:item['stl_sha256']=sha(OUT/item['stl'])
        project(plate);affected.append(plate)
    repair=dict(id='REPRINT_S3_1',items=[],optional=False,replacement=True)
    x=8
    for id in ['W06','W07']:
        p=rows[id];m=trimesh.load(OUT/p['stl'],process=True)
        repair['items'].append(dict(id=id,stl=p['stl'],offset_mm=[x,8,0],stl_sha256=sha(OUT/p['stl'])))
        x+=m.extents[0]+12
    project(repair);affected.append(repair)
    plates[:]=[p for p in plates if p['id']!='REPRINT_S3_1']+[repair]
    put(OUT/'printing/plates.json',plans)
    report=load(OUT/'verification/slicing.json');old={p['id']:p for p in report['plates']}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for result in pool.map(run,affected):old[result['id']]=result
    report['plates']=[old[p['id']] for p in plates];report['passed']=all(p['passed'] for p in report['plates'])
    assert all(old[p['id']]['input_sha256']==sha(OUT/p['file']) for p in plates)
    put(OUT/'verification/slicing.json',report)

if __name__=='__main__':main()
