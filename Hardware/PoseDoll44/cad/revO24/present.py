"""Package the exact O24 meshes into a self-contained local review page."""
from arm import *
import base64,shutil

def main():
    B=OUT;V=B/'preview';V.mkdir(exist_ok=True)
    p=json.loads((B/'profiles/arm_profile.json').read_text('utf8'));ref=json.loads((B/'reference/target_quinn.json').read_text('utf8'))
    assembly=json.loads((B/'assembly.json').read_text('utf8'));mesh=np.load(B/'assembly_meshes.npz')
    vertices=[];items=[];offset=0
    for part in assembly['parts']:
        i=str(part['i']);tri=mesh[i+'v'][mesh[i+'f']];n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);n/=np.maximum(1e-10,np.linalg.norm(n,axis=1))[:,None]
        a=np.concatenate([tri,np.repeat(n[:,None,:],3,axis=1)],axis=2).reshape(-1,6)
        vertices.append(a);items.append({**part,'first':offset,'count':len(a)});offset+=len(a)
    audit_path=B/'verification/motion_dense.json'
    audit=json.loads(audit_path.read_text('utf8')) if audit_path.exists() else json.loads((B/'verification/motion_named.json').read_text('utf8'))
    kin=json.loads((B/'verification/kinematics.json').read_text('utf8'))
    surface=np.load(B/'reference/ue_neutral_surface.npz');geo=json.loads((H/'reference/ue58/quinn_geometry.json').read_text('utf8'))
    bones=geo['bone_info'];idx={d['name']:d['index'] for d in bones};parents={d['index']:d['parent_index'] for d in bones}
    descendants=set()
    for bone in parents:
        a=bone
        while a>=0:
            if a==idx['upperarm_l']:descendants.add(bone);break
            a=parents[a]
    dom=np.array([max(w,key=lambda pair:pair[1])[0] for w in geo['skin_weights']]);faces=surface['f'];faces=faces[~np.all(np.isin(dom[faces],list(descendants)),axis=1)]
    tri=surface['v'][faces];n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);n/=np.maximum(1e-10,np.linalg.norm(n,axis=1))[:,None]
    ghost=np.concatenate([tri,np.repeat(n[:,None,:],3,axis=1)],axis=2).reshape(-1,6);vertices.append(ghost)
    data=dict(profile=p,reference=ref,parts=items,reference_mesh=dict(first=offset,count=len(ghost)),poses=json.loads((B/'profiles/poses.json').read_text('utf8')),
        audit={r['pose']:dict(count=r['count'],affected=list({h[k] for h in r['collisions'] for k in ['a','b']})) for r in audit['cases']},
        verification=dict(samples=audit['samples'],collision_status=audit['status'],kinematics=kin['status']),
        geometry=base64.b64encode(np.concatenate(vertices).astype('<f4').tobytes()).decode())
    (V/'data.js').write_text('window.O24='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf8')
    for name in ['index.html','viewer.js','style.css','tutorial.html','tutorial.css','tutorial-content.js','tutorial.js']:
        shutil.copy2(HERE/name,V/name)
    print('preview',V)
if __name__=='__main__':main()
