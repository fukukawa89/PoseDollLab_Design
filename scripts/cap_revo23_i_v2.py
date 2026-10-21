"""Clip sacrificial contacts to explicit clearances, never scale toward the model."""
from print_revo23_i import *
from cap_revo23_print import exact_box_offset

def fix(rid,source,name):
    configure_print();file=PRINT/'candidates'/(rid+'.json');spec=read(file)
    r=read(PRINT/'bambu'/rid/source/'checked_result.json')
    c=copy.deepcopy(read(PRINT/'trials'/rid/source/'input.json')['candidate']);M=np.array(c['matrix'])
    body=solid(*audit_print.read_project(IROOT/r['project'])[0][rid])
    z=np.load(PRINT/'guards_v5'/(rid+'.npz'));guard=move(solid(z['v'],z['f']),M)
    caps=[];records=[]
    def clipped(patch):
        bb=np.array(patch.bounding_box());crop=box(bb[:3]-1,bb[3:]+1)
        patch=patch-exact_box_offset(body^crop,[.4,.4,.24])-exact_box_offset(guard^crop,[.4,.4,.16])
        return [q for q in patch.decompose()if q.volume()>.08 and q.min_gap(body,.18)>=.179]
    for i,cap in enumerate(audit_print.manual_caps(IROOT/r['project']).decompose()):
        if cap.volume()<=.08:continue
        if r['caps']['rows'][i]['passed']:caps.append(cap)
        else:
            cleaned=clipped(cap)
            caps.extend(cleaned);records.append(dict(previous_cap=i+1,reclip=True,components=len(cleaned)))
    layer=float(c.get('settings',{}).get('layer_height','.16'))
    for issue in r['islands']['external_new_islands']:
        x0,y0,x1,y1=issue['bounds_mm'];top=issue['z_mm']-layer-.24
        good=clipped(box([x0-1,y0-1,top-.36],[x1+1,y1+1,top]))
        caps.extend(good);records.append(dict(target=issue,components=len(good)))
    assert caps,(rid,'No printable clear cap geometry')
    path=PRINT/'candidates'/(rid+'_'+name+'.npz');save_s(path,move(union(caps),np.linalg.inv(M)))
    c.update(name=name,manual_caps=path.relative_to(IROOT).as_posix(),cap_design=records,shield_enforcers=True)
    trial=dict(spec,candidates=[c]);opt.build_candidate(trial,c);r=run_one(trial)
    if r['passed']:spec['candidates']=[c]+[v for v in spec['candidates']if v['name']!=name];put(file,spec)
    print('CAP I V2',rid,r['passed'],{k:r[k]['passed']for k in('native','clearance','islands','caps')},flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('id');ap.add_argument('source');ap.add_argument('name');a=ap.parse_args();fix(a.id,a.source,a.name)
