"""Cross-slice frozen candidates using installed Bambu Studio; no printer calls."""
from optimize_revo23_print import *
from build_revo22_supports import slice_project
from audit_revo23_print import native_audit,void_audit,starting_islands,cap_audit
import copy

def run(r):
    if 'candidate_data' in r:
        c=r.pop('candidate_data');spec=read(OUT/'candidates'/(r['id']+'.json'))
        check=OUT/'trials'/r['id']/c['name']/'input.json'
        if not check.exists() or read(check)['candidate']!=c:build_candidate(spec,c)
        r['source_project']=(OUT/'trials'/r['id']/c['name']/'input.3mf').relative_to(B).as_posix()
    work=OUT/'bambu'/r['id']/r['name'];work.mkdir(parents=True,exist_ok=True)
    source=B/r['source_project'];dest=work/(r['id']+'_A1mini_PLA.3mf');report=work/'checked_result.json'
    r['guard_revision']=read(source.parent/'input.json')['candidate'].get('guard_revision',1)
    # Unselected slicer outputs may be absent after a source-only checkout.
    # A cached report is reusable only while its exact native file still exists.
    if report.exists() and dest.exists():
        cached=read(report)
        if cached.get('source_sha256')==sha(source) and cached.get('project_sha256')==sha(dest):return cached
    slice_project(source,dest,work)
    out=copy.deepcopy(r);out.update(project=dest.relative_to(B).as_posix(),source_sha256=sha(source),engine='Bambu Studio02.08.02.61')
    out.update(measure(dest));out['native']=native_audit(out);out['clearance']=void_audit(out);out['islands']=starting_islands(out)
    out['caps']=cap_audit(out)
    out['passed']=bool(out['passed'] and out['native']['passed'] and out['clearance']['passed'] and out['islands']['passed'] and out['caps']['passed'])
    put(report,out);print('BAMBU',out['id'],out['name'],out['passed'],'support',round(out['support_g'],2),'g',flush=True)
    return out

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--ids',nargs='*');ap.add_argument('--names',nargs='*');ap.add_argument('--selected',action='store_true');ap.add_argument('--candidates',action='store_true');ap.add_argument('--workers',type=int,default=2);a=ap.parse_args()
    if a.candidates:
        rows=[]
        for f in sorted((OUT/'candidates').glob('*.json')):
            s=read(f)
            for c in s['candidates']:rows.append(dict(id=s['id'],key=s['key'],name=c['name'],matrix=c['matrix'],metrics=c['metrics'],support=c['support'],candidate_data=c))
    elif a.selected:rows=[r['selected'] for r in read(OUT/'selection.json')['rows'] if r['selected']]
    else:rows=[read(p) for p in (OUT/'trials').glob('*/*/result.json') if read(p)['passed']]
    rows=[r for r in rows if (not a.ids or r['id'] in a.ids) and (not a.names or r['name'] in a.names)]
    with concurrent.futures.ProcessPoolExecutor(max_workers=a.workers) as pool:list(pool.map(run,rows))
