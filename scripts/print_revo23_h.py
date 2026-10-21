"""Rebuild native A1 mini projects with H meshes and re-audit every toolpath."""
from export_revo23_h import *
import optimize_revo23_print as opt
import slice_revo23_exports as slicer
import guard_revo23_print as guard
import audit_revo23_print as audit_print
import bambu_revo23_print as bambu
import concurrent.futures
import copy

PRINT=HROOT/'print';OLD=B/'print_optimization_G'
def configure_print():
    setup();PRINT.mkdir(exist_ok=True)
    for module in (opt,guard,audit_print,bambu):
        module.B=HROOT;module.OUT=PRINT;module.EXPORT_ROOT=HROOT/'export';module.BASE=HROOT/'export/slicing'
    guard.load_current=lambda:load_h()[0]
    slicer.B=HROOT;slicer.ROOT=HROOT/'export/slicing';slicer.EXPORT_ROOT=HROOT/'export'
    old_profile=opt.profile
    def profile(style,rid):
        p=old_profile(style,rid.replace('O23H','O23G'));p['print_settings_id']='O23H A1 mini PLA / seated connections';return p
    opt.profile=profile

def prepare():
    shutil.copy2(HROOT/'geometry.json',HROOT/'verification/geometry.json')
    rows=read(HROOT/'export/repair.json')['rows'];old={r['key']:r for r in read(OLD/'native_selection.json')['rows']};candidates=[]
    parts,p,cfg=load_h();N=frames(p,p['neutral_raw_deg'])
    for row in rows:
        previous=old[row['key']];source=read(B/previous['source_project'].replace('input.3mf','input.json'))
        c=copy.deepcopy(source['candidate']);rid=row['id'];c['name']='revised_connections'
        m=trimesh.load(HROOT/row['staged_stl'],process=True);M=np.array(c['matrix']);w=m.vertices@M[:3,:3].T
        M[:3,3]=np.r_[90-(w.min(0)[:2]+w.max(0)[:2])/2,-w[:,2].min()]
        c.update(matrix=M,size_mm=np.ptp(w,axis=0),guard_revision=5,protect_voids=True)
        lines=[]
        if parts[row['key']]['role']=='structure':
            T=np.linalg.inv(N[parts[row['key']]['token']])
            for rod in connection_records(row['key'])['rods']:
                pts=np.array(rod['centerline_world_mm'])@T[:3,:3].T+T[:3,3];lines.append(dict(points=pts,radius=rod['radius_mm'],mount=rod['mount']))
        c['metrics']=opt.metrics(m,M,lines)
        sources=PRINT/'support_sources'/rid;sources.mkdir(parents=True,exist_ok=True)
        for name in ('manual_caps','enforce_mesh','enforce_source'):
            if c.get(name):
                src=B/c[name];dest=sources/(name+src.suffix);shutil.copy2(src,dest);c[name]=dest.relative_to(HROOT).as_posix()
        if c.get('enforce_sources'):
            copied=[]
            for i,reference in enumerate(c['enforce_sources']):
                src=B/reference;dest=sources/f'enforce_{i}.json';shutil.copy2(src,dest);copied.append(dest.relative_to(HROOT).as_posix())
            c['enforce_sources']=copied
        record=dict(id=rid,key=row['key'],stl_sha256=row['stl_sha256'],source=row,candidates=[c],previous_G_source_sha256=sha(B/previous['source_project']))
        put(PRINT/'candidates'/(rid+'.json'),record);candidates.append(record)
    slicer.ROOT.mkdir(parents=True,exist_ok=True)
    put(slicer.ROOT/'orientation_overrides.json',[dict(id=r['id'],matrix=r['candidates'][0]['matrix']) for r in candidates])
    for row in rows:slicer.build(row)
    guard.prepare(5)
    for r in candidates:opt.build_candidate(r,r['candidates'][0]);print('H PROJECT BUILT',r['id'],flush=True)
    put(PRINT/'source_lock.json',dict(geometry_sha256=sha(HROOT/'assembly.npz'),stls={r['id']:r['stl_sha256'] for r in rows},
        policy='Retain previously verified orientation/support strategy where possible; regenerate H aperture blockers and independently audit all new native toolpaths.',physical_tested=False))

def run_one(spec):
    c=spec['candidates'][0]
    row=dict(id=spec['id'],key=spec['key'],name=c['name'],matrix=c['matrix'],metrics=c['metrics'],support=c['support'],
        source_project=(PRINT/'trials'/spec['id']/c['name']/'input.3mf').relative_to(HROOT).as_posix())
    return bambu.run(row)

def run(ids=None,workers=2):
    specs=[read(path) for path in sorted((PRINT/'candidates').glob('*.json'))]
    if ids:specs=[r for r in specs if r['id'] in ids]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:results=list(pool.map(run_one,specs))
    # Re-read all completed results so a retry never drops another checked part.
    complete=[]
    for specfile in sorted((PRINT/'candidates').glob('*.json')):
        spec=read(specfile);chosen=spec['candidates'][0]['name'];path=PRINT/'bambu'/spec['id']/chosen/'checked_result.json'
        if path.exists():complete.append(read(path))
    put(PRINT/'results.json',dict(geometry_sha256=sha(HROOT/'assembly.npz'),rows=complete,passed=len(complete)==32 and all(r['passed'] for r in complete)))
    print('H NATIVE RESULTS',len(complete),[r['id'] for r in complete if not r['passed']],flush=True)

if __name__=='__main__':
    import copy
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['prepare','slice']);ap.add_argument('--ids',nargs='*');ap.add_argument('--workers',type=int,default=2);a=ap.parse_args();configure_print()
    if a.mode=='prepare':prepare()
    else:run(a.ids,a.workers)
