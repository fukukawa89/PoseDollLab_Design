from bambu_revo23_print import *

def prepare(left,right):
    lf=OUT/'candidates'/(left+'.json');rf=OUT/'candidates'/(right+'.json');L=read(lf);Rspec=read(rf)
    rr=[read(p) for p in (OUT/'bambu'/left).glob('*/checked_result.json') if read(p)['passed']]
    source=min(rr,key=lambda r:r['support_g']);c=copy.deepcopy(read((B/source['source_project']).parent/'input.json')['candidate'])
    p=read(B/'profiles/device_profile.json');N=frames(p,p['neutral_raw_deg']);items={x['key']:x for x in read(B/'assembly.json')['items']}
    mirror=np.diag([1.,-1,1,1]);S=np.linalg.inv(N[items[L['key']]['token']])@mirror@N[items[Rspec['key']]['token']]
    reflection=np.diag([-1.,1,1,1]);reflection[0,3]=180
    M=reflection@np.array(source['matrix'])@S;m=trimesh.load(B/Rspec['source']['staged_stl'],process=True);w=m.vertices@M[:3,:3].T+M[:3,3];M[2,3]-=w[:,2].min()
    assert np.linalg.det(M[:3,:3])>.999
    aux=[]
    with zipfile.ZipFile(B/source['source_project']) as z:
        config=ET.fromstring(z.read('Metadata/model_settings.config'));doc=ET.fromstring(z.read('3D/Objects/object_1.model'))
        for part in config.findall('object/part'):
            if part.get('subtype')!='support_enforcer':continue
            mesh=doc.find(Q+f'resources/{Q}object[@id="{part.get("id")}"]/'+Q+'mesh')
            v=np.array([[float(t.get(k)) for k in 'xyz'] for t in mesh.findall(Q+'vertices/'+Q+'vertex')]);f=np.array([[int(t.get(k)) for k in ('v1','v2','v3')] for t in mesh.findall(Q+'triangles/'+Q+'triangle')])
            aux.append(move(solid(v,f),np.linalg.inv(S)))
    for k in ('enforce_source','enforce_sources','enforce_mesh'):c.pop(k,None)
    if c.get('manual_caps'):
        n=np.load(B/c['manual_caps']);mirrored=move(solid(n['v'],n['f']),np.linalg.inv(S));path=OUT/'candidates'/(right+'_mirrored_caps.npz');v,f=vf(mirrored);np.savez_compressed(path,v=v,f=f);c['manual_caps']=path.relative_to(B).as_posix()
    if aux:
        path=OUT/'candidates'/(right+'_mirrored_contact.npz');v,f=vf(union(aux));np.savez_compressed(path,v=v,f=f);c['enforce_mesh']=path.relative_to(B).as_posix()
    c.update(name='mirrored_pass',matrix=M,size_mm=np.ptp(w,axis=0),metrics=metrics(m,M,Rspec['rod_lines']),mirrored_from=dict(id=left,name=source['name']))
    if c.get('settings',{}).get('support_angle'):c['settings']['support_angle']=str((-float(c['settings']['support_angle']))%180)
    Rspec['candidates']=[x for x in Rspec['candidates'] if x['name']!=c['name']]+[c];put(rf,Rspec)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--from-id');ap.add_argument('--to-id');a=ap.parse_args()
    if a.from_id:prepare(a.from_id,a.to_id)
    else:prepare('O23G-S07','O23G-S05');prepare('O23G-S17','O23G-S22')
