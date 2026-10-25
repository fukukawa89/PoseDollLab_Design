"""Package actual B/C exported meshes into a file-openable comparison viewer."""
from compact_arm import *
import base64,shutil

V=OUT/'preview';V.mkdir(exist_ok=True);arrays=[];offset=0
def encode(folder,selection=None):
    global offset
    data=load(folder/'assembly.json')['parts'];z=np.load(folder/'assembly_meshes.npz');result=[]
    for p in data:
        if selection and not selection(p):continue
        tri=z[str(p['i'])+'v'][z[str(p['i'])+'f']];n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);n/=np.maximum(1e-10,np.linalg.norm(n,axis=1))[:,None]
        v=np.concatenate([tri,np.repeat(n[:,None,:],3,axis=1)],axis=2).reshape(-1,6)
        arrays.append(v);result.append({**p,'first':offset,'count':len(v)});offset+=len(v)
    return result
parts=encode(OUT);baseline=encode(BASE_B)
surface=np.load(OLD/'reference/ue_neutral_surface.npz');geo=load(H/'reference/ue58/quinn_geometry.json')
idx={b['name']:b['index'] for b in geo['bone_info']};parents={b['index']:b['parent_index'] for b in geo['bone_info']};desc=set()
for bone in parents:
    v=bone
    while v>=0:
        if v==idx['upperarm_l']:desc.add(bone);break
        v=parents[v]
dom=np.array([max(w,key=lambda t:t[1])[0] for w in geo['skin_weights']]);f=surface['f'];f=f[~np.all(np.isin(dom[f],list(desc)),axis=1)]
tri=surface['v'][f];n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);n/=np.maximum(1e-10,np.linalg.norm(n,axis=1))[:,None]
ghost=np.concatenate([tri,np.repeat(n[:,None,:],3,axis=1)],axis=2).reshape(-1,6);arrays.append(ghost)
motion=load(OUT/'verification/motion_dense.json')
assert motion['status']=='PASS' and motion['geometry_sha256']==sha(OUT/'assembly_meshes.npz')
data=dict(profile=load(OUT/'profiles/arm_profile.json'),reference=load(OUT/'reference/target_quinn.json'),parts=parts,revisions=dict(O24C=parts,O24B=baseline),
    reference_mesh=dict(first=offset,count=len(ghost)),poses=load(OUT/'profiles/poses.json'),comparison=load(OUT/'verification/comparison.json'),
    audit={r['pose']:dict(count=r['count'],affected=list({h[k] for h in r['collisions'] for k in ['a','b']})) for r in motion['cases']},
    verification=dict(samples=motion['samples'],collision_status=motion['status']),geometry_sha256=sha(OUT/'assembly_meshes.npz'),
    geometry=base64.b64encode(np.concatenate(arrays).astype('<f4').tobytes()).decode())
(V/'data.js').write_text('window.O24='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf8')
for file in ['index.html','viewer.js','style.css']:shutil.copy2(HERE/file,V/file)
(OUT/'StartPreview.cmd').write_text('@echo off\r\nstart "" "%~dp0preview\\index.html"\r\n',encoding='ascii')
print('Self-contained B/C preview:',V)
