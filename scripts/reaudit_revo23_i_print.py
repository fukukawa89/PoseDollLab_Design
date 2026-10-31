"""Apply the recorded interior-path distinction to completed native trials."""
from print_revo23_i import *

configure_print()
for path in sorted((PRINT/'bambu').glob('*/*/checked_result.json')):
    r=read(path)
    if not (IROOT/r['project']).is_file() or not (IROOT/r['source_project']).is_file():continue
    r['islands']=audit_print.starting_islands(r)
    path_report,_=audit_print.paths(IROOT/r['project'])
    r['passed']=r['repairs']==0 and r['bed_violations']==0 and path_report['extrusion_moves']>10 and all(r[k]['passed']for k in('native','clearance','islands','caps'))
    put(path,r)
for file in sorted((PRINT/'candidates').glob('*.json')):
    spec=read(file);options=[]
    for path in (PRINT/'bambu'/spec['id']).glob('*/checked_result.json'):
        r=read(path)
        if not r['passed']:continue
        if not (IROOT/r['project']).is_file() or not (IROOT/r['source_project']).is_file():continue
        if sha(IROOT/r['source_project'])!=r['source_sha256']:continue
        input_record=read((IROOT/r['source_project']).parent/'input.json')
        if input_record['stl_sha256']!=spec['stl_sha256']:continue
        options.append((r['support_g'],r,input_record['candidate']))
    if not options:continue
    _,r,c=min(options,key=lambda x:x[0]);spec['candidates']=[c]+[v for v in spec['candidates']if v['name']!=c['name']];put(file,spec)
    print('SELECT I',spec['id'],c['name'],r['support_g'],flush=True)
