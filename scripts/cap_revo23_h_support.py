"""Small removable caps only for verified exterior start footprints."""
from print_revo23_h import *
from cap_revo23_print import exact_box_offset

def fix(rid,source_name='revised_connections',shrink=.78,variant=None):
    specfile=PRINT/'candidates'/(rid+'.json');spec=read(specfile);r=read(PRINT/'bambu'/rid/source_name/'checked_result.json')
    c=copy.deepcopy(read((HROOT/r['source_project']).parent/'input.json')['candidate']);M=np.array(c['matrix'])
    body=solid(*audit_print.read_project(HROOT/r['project'])[0][rid]);oldcaps=audit_print.manual_caps(HROOT/r['project'])
    caps=[];records=[]
    for i,cap in enumerate(oldcaps.decompose()):
        state=r['caps']['rows'][i]
        if not state['passed']:
            bb=np.array(cap.bounding_box());center=(bb[:3]+bb[3:])/2
            cap=cap.translate(-center).scale([shrink,shrink,1]).translate(center)
            records.append(dict(previous_cap=i+1,xy_scale=shrink,reason='Restore actual bead clearance without altering the structural model.'))
        caps.append(cap)
    z=np.load(PRINT/'guards_v5'/(rid+'.npz'));guard=move(solid(z['v'],z['f']),M)
    layer=float(c.get('settings',{}).get('layer_height','.16'))
    for issue in r['islands']['external_new_islands']:
        x0,y0,x1,y1=issue['bounds_mm'];top=issue['z_mm']-layer-.24
        patch=box([x0-.65,y0-.65,top-.32],[x1+.65,y1+.65,top]);bb=np.array(patch.bounding_box());crop=box(bb[:3]-.6,bb[3:]+.6)
        patch=patch-exact_box_offset(body^crop,[.23,.23,.23])-exact_box_offset(guard^crop,[.35,.35,.16])
        good=[q for q in patch.decompose() if q.volume()>.08 and q.min_gap(body,.18)>=.179]
        caps.extend(good);records.append(dict(target=issue,patch_count=len(good),volume_mm3=sum(q.volume()for q in good)))
    assert caps,(rid,'No removable cap geometry')
    name=variant or 'endface_caps'+str(round(shrink*100));path=PRINT/'candidates'/(rid+'_'+name+'.npz');save_s(path,move(union(caps),np.linalg.inv(M)))
    c.update(name=name,manual_caps=path.relative_to(HROOT).as_posix(),cap_design=records,shield_enforcers=True)
    trial=dict(spec,candidates=[c]);opt.build_candidate(trial,c);result=run_one(trial)
    if result['passed']:
        spec['candidates']=[c]+[x for x in spec['candidates'] if x['name']!=name];put(specfile,spec)
    print('H CAP RESULT',rid,result['passed'],'caps',result['caps'],flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('id');ap.add_argument('--source',default='revised_connections');ap.add_argument('--shrink',type=float,default=.78);ap.add_argument('--name');a=ap.parse_args();configure_print();fix(a.id,a.source,a.shrink,a.name)
