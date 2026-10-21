"""Remove slicer-omitted sacrificial caps while keeping their support requests."""
from print_revo23_h import *

def prune(rid,source):
    specfile=PRINT/'candidates'/(rid+'.json');spec=read(specfile)
    old=PRINT/'bambu'/rid/source;project=old/(rid+'_A1mini_PLA.3mf')
    c=copy.deepcopy(read(PRINT/'trials'/rid/source/'input.json')['candidate']);M=np.array(c['matrix'])
    report,a=audit_print.paths(project);caps=audit_print.manual_caps(project);retained=[];removed=[]
    for i,cap in enumerate(caps.decompose()):
        (retained if np.any(a[:,9]==i+1) else removed).append(cap)
    assert removed and retained,(len(removed),len(retained))
    name=source+'_pruned';path=PRINT/'candidates'/(rid+'_'+name+'.npz')
    save_s(path,move(union(retained),np.linalg.inv(M)))
    extra=union(removed)
    if c.get('enforce_mesh'):
        z=np.load(HROOT/c['enforce_mesh']);extra+=move(solid(z['v'],z['f']),M)
    request=path.with_name(path.stem+'_enforcer.npz');save_s(request,move(extra,np.linalg.inv(M)))
    c.update(name=name,manual_caps=path.relative_to(HROOT).as_posix(),enforce_mesh=request.relative_to(HROOT).as_posix(),omitted_caps_removed=len(removed))
    trial=dict(spec,candidates=[c]);opt.build_candidate(trial,c);result=run_one(trial)
    if result['passed']:
        spec['candidates']=[c]+[x for x in spec['candidates'] if x['name']!=name];put(specfile,spec)
    print('H CAP PRUNE',rid,len(removed),result['passed'],flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('id');ap.add_argument('source');a=ap.parse_args();configure_print();prune(a.id,a.source)
