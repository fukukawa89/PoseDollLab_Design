"""Offline, same-mesh WebGL review. No network assets or external dependencies."""
from fullbody import *
import base64
def main():
    b=OUT/'preview';b.mkdir(exist_ok=True);data=load(OUT/'assembly.json');z=np.load(OUT/'assembly_meshes.npz');packed=[];cursor=0
    for p in data['parts']:
        i=str(p['i']);verts=z[i+'v'];faces=z[i+'f'];m=trimesh.Trimesh(verts,faces,process=False)
        ar=np.concatenate([verts[faces],np.repeat(m.face_normals[:,None,:],3,axis=1)],axis=2).reshape(-1,6).astype('<f4')
        p['first']=cursor;p['count']=len(ar);cursor+=len(ar);packed.append(ar)
    motion=load(OUT/'verification/motion_named.json') if (OUT/'verification/motion_named.json').exists() else {'cases':[]}
    digest=sha(OUT/'assembly_meshes.npz')
    if motion.get('geometry_sha256')!=digest:raise RuntimeError('Stale named-pose audit')
    paths=load(OUT/'verification/motion_task_paths.json') if (OUT/'verification/motion_task_paths.json').exists() else {'cases':[]}
    if paths.get('geometry_sha256')!=digest:raise RuntimeError('Stale path audit')
    audits={r['pose']:{'count':r['count'],'pairs':r['collisions'],'advisory_count':r.get('advisory_count',0),'advisory_pairs':r.get('nonadjacent_contacts',[]),'affected':list({v[k] for v in r['collisions'] for k in ['a','b']})} for r in motion['cases']}
    rom=load(OUT/'verification/rom_examination_dense.json')
    if rom['geometry_sha256']!=digest:raise RuntimeError('Stale ROM audit')
    shown=poses();contexts={};labels={a['id']:a['label'] for a in PROFILE['axes']}
    for r in rom['cases']:
        if '/step/' in r['case']:continue
        n=r['case'];shown[n]=dict(label='范围 · '+labels[r['axis']]+' '+str(r['value_deg'])+'°',angles=r['angles'])
        audits[n]=dict(count=r['count'],pairs=r['collisions'],affected=list({v[k] for v in r['collisions'] for k in ['a','b']}))
        contexts[n]='检查体位：'+('；'.join(labels[k]+' '+str(v)+'°' for k,v in r['angles'].items() if k!=r['axis']) or '其余轴为参考角度')
    ue=[dict(id=r['bone'],parent=r['parent'],frame=r['frame'],local_point=(np.linalg.inv(F0[r['frame']])@np.r_[r['neutral_position_mm'],1])[:3].tolist()) for r in load(OUT/'reference/full_UE_N_pose.json')['bones']]
    harness=load(OUT/'harness/routes.json');assert harness['geometry_sha256']==digest
    hn={r['id']:r for r in harness['nodes']};wire=[]
    for r in harness['spans']:
        start=hn[r['start']];end=hn[r['end']];q=np.array(r['guide_A_mm']);ds=np.r_[0,np.cumsum(np.linalg.norm(np.diff(q,axis=0),axis=1))];tt=ds/max(ds[-1],1e-9)
        points=[]
        for p,t in zip(q,tt):points.append(dict(a=(np.linalg.inv(FA[start['frame']])@np.r_[p,1])[:3].tolist(),b=(np.linalg.inv(FA[end['frame']])@np.r_[p,1])[:3].tolist(),t=float(t)))
        wire.append(dict(id=r['id'],start=r['start'],end=r['end'],start_frame=start['frame'],end_frame=end['frame'],points=points,bank=r['cables'][0][0],cable_count=len(r['cables'])))
    payload=dict(profile=PROFILE,parts=data['parts'],poses=shown,contexts=contexts,audit=audits,geometry=base64.b64encode(np.vstack(packed).tobytes()).decode(),reference=REF,harness=wire,
      height=load(OUT/'verification/envelope.json') if (OUT/'verification/envelope.json').exists() else {},geometry_sha256=digest,
      ueBones=ue,paths={r['pose']:r for r in paths['cases']},expectedFrames={n:{fr:m.tolist() for fr,m in frames(p['angles']).items()} for n,p in shown.items()})
    (b/'data.js').write_text('window.O24D='+json.dumps(payload,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf8')
    for n in ['viewer.js','style.css','index.html']:(b/n).write_bytes((HERE/n).read_bytes())
    print(json.dumps(dict(parts=len(data['parts']),triangles=cursor//3,preview=b.as_posix()),ensure_ascii=False))
if __name__=='__main__':main()
