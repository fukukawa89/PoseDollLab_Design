"""I native projects start from H's checked orientation and removable supports."""
from export_revo23_i import *
import optimize_revo23_print as opt
import slice_revo23_exports as slicer
import guard_revo23_print as guard
import audit_revo23_print as audit_print
import bambu_revo23_print as bambu
import concurrent.futures

PRINT=IROOT/'print'

def configure_print():
    setup();PRINT.mkdir(exist_ok=True)
    for module in (opt,guard,audit_print,bambu):module.B=IROOT;module.OUT=PRINT;module.EXPORT_ROOT=IROOT/'export';module.BASE=IROOT/'export/slicing'
    guard.load_current=lambda:load_i()[0]
    slicer.B=IROOT;slicer.ROOT=IROOT/'export/slicing';slicer.EXPORT_ROOT=IROOT/'export'
    original_profile=opt.profile
    def profile(style,rid):
        out=original_profile(style,rid.replace('O23I','O23G'));out['print_settings_id']='O23I A1 mini PLA / unified mount contours';return out
    opt.profile=profile

def prepare(ids=None):
    geometry=read(IROOT/'geometry.json');assert geometry['geometry_sha256']==sha(IROOT/'assembly.npz')
    shutil.copy2(IROOT/'geometry.json',IROOT/'verification/geometry.json')
    allrows=read(IROOT/'export/repair.json')['rows'];rows=[r for r in allrows if not ids or r['id']in ids];old={r['key']:r for r in read(HROOT/'print/results.json')['rows']};candidates=[]
    parts,p,cfg=load_i();N=frames(p,p['neutral_raw_deg'])
    for row in rows:
        previous=old[row['key']];source=read((HROOT/previous['source_project']).parent/'input.json');c=copy.deepcopy(source['candidate']);rid=row['id'];c['name']='unified_contours'
        m=trimesh.load(IROOT/row['staged_stl'],process=True);M=np.array(c['matrix']);w=m.vertices@M[:3,:3].T
        M[:3,3]=np.r_[90-(w.min(0)[:2]+w.max(0)[:2])/2,-w[:,2].min()];size=np.ptp(w,axis=0)
        assert max(size[:2])<172 and size[2]<179,(rid,size)
        c.update(matrix=M,size_mm=size,guard_revision=5,protect_voids=True)
        lines=[]
        if parts[row['key']]['role']=='structure':
            T=np.linalg.inv(N[parts[row['key']]['token']])
            for rod in i_records(row['key'])['rods']:
                pts=np.array(rod['centerline_world_mm'])@T[:3,:3].T+T[:3,3];lines.append(dict(points=pts,radius=rod['radius_mm'],mount=rod['mount']))
        c['metrics']=opt.metrics(m,M,lines)
        sources=PRINT/'support_sources'/rid;sources.mkdir(parents=True,exist_ok=True)
        for name in ('manual_caps','enforce_mesh','enforce_source'):
            if c.get(name):
                src=HROOT/c[name];dest=sources/(name+src.suffix);shutil.copy2(src,dest);c[name]=dest.relative_to(IROOT).as_posix()
        if c.get('enforce_sources'):
            copied=[]
            for i,reference in enumerate(c['enforce_sources']):
                src=HROOT/reference;dest=sources/f'enforce_{i}.json';shutil.copy2(src,dest);copied.append(dest.relative_to(IROOT).as_posix())
            c['enforce_sources']=copied
        if c.get('manual_caps'):
            z=np.load(IROOT/c['manual_caps']);caps=solid(z['v'],z['f']);body=solid(m.vertices,m.faces)
            kept=[cap for cap in caps.decompose()if cap.min_gap(body,.18)>=.179]
            c['obsolete_H_caps_removed']=len(caps.decompose())-len(kept)
            if kept:save_s(IROOT/c['manual_caps'],union(kept))
            else:c.pop('manual_caps')
        spec=dict(id=rid,key=row['key'],stl_sha256=row['stl_sha256'],source=row,candidates=[c],previous_H_source_sha256=sha(HROOT/previous['source_project']))
        put(PRINT/'candidates'/(rid+'.json'),spec);candidates.append(spec)
    slicer.ROOT.mkdir(parents=True,exist_ok=True)
    allspecs=[read(f)for f in sorted((PRINT/'candidates').glob('*.json'))]
    put(slicer.ROOT/'orientation_overrides.json',[dict(id=r['id'],matrix=r['candidates'][0]['matrix'])for r in allspecs])
    for row in rows:slicer.build(row)
    guard.prepare(5)
    for spec in candidates:opt.build_candidate(spec,spec['candidates'][0]);print('I PROJECT BUILT',spec['id'],flush=True)
    put(PRINT/'source_lock.json',dict(geometry_sha256=sha(IROOT/'assembly.npz'),stls={r['id']:r['stl_sha256']for r in allrows},physical_tested=False))

def run_one(spec):
    c=spec['candidates'][0]
    return bambu.run(dict(id=spec['id'],key=spec['key'],name=c['name'],matrix=c['matrix'],metrics=c['metrics'],support=c['support'],source_project=(PRINT/'trials'/spec['id']/c['name']/'input.3mf').relative_to(IROOT).as_posix()))

def run(ids=None,workers=4):
    specs=[read(f)for f in sorted((PRINT/'candidates').glob('*.json'))]
    if ids:specs=[s for s in specs if s['id']in ids]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers)as pool:list(pool.map(run_one,specs))
    rows=[]
    for f in sorted((PRINT/'candidates').glob('*.json')):
        s=read(f);report=PRINT/'bambu'/s['id']/s['candidates'][0]['name']/'checked_result.json'
        if report.exists():rows.append(read(report))
    put(PRINT/'results.json',dict(geometry_sha256=sha(IROOT/'assembly.npz'),rows=rows,passed=len(rows)==32 and all(r['passed']for r in rows)))
    print('I NATIVE RESULTS',len(rows),[r['id']for r in rows if not r['passed']],flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['prepare','slice']);ap.add_argument('--ids',nargs='*');ap.add_argument('--workers',type=int,default=4);a=ap.parse_args();configure_print()
    prepare(a.ids)if a.mode=='prepare'else run(a.ids,a.workers)
