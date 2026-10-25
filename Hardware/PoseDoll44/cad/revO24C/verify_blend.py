import bpy,json,hashlib
import numpy as np
from pathlib import Path
B=Path(__file__).resolve().parents[2]/'bench/revO24C';load=lambda p:json.loads(p.read_text('utf8'))
expected=load(B/'profiles/pose_frames.json');meta=load(B/'assembly.json');z=np.load(B/'assembly_meshes.npz');worst_p=0.;worst_r=0.;worst_v=0.
for i,(name,frames) in enumerate(expected.items()):
    bpy.context.scene.frame_set(1+i*24);bpy.context.view_layer.update()
    for token,value in frames.items():
        m=np.array(bpy.data.objects[token].matrix_world);t=np.array(value);t[:3,3]/=1000
        worst_p=max(worst_p,float(np.linalg.norm(m[:3,3]-t[:3,3]))*1000);worst_r=max(worst_r,float(np.max(abs(m[:3,:3]-t[:3,:3]))))
for p in meta['parts']:
    v=np.array([v.co[:] for v in bpy.data.objects[p['name']].data.vertices])*1000;target=z[str(p['i'])+'v'];assert v.shape==target.shape
    worst_v=max(worst_v,float(np.max(abs(v-target))))
count=sum(o.type=='MESH' for o in bpy.context.scene.objects);digest=hashlib.sha256((B/'assembly_meshes.npz').read_bytes()).hexdigest()
ok=count==len(meta['parts']) and bpy.context.scene['geometry_sha256']==digest and worst_p<.001 and worst_r<1e-5 and worst_v<.001
r=dict(status='PASS' if ok else 'FAIL',parts=count,poses=len(expected),max_position_error_mm=worst_p,max_rotation_element_error=worst_r,max_mesh_coordinate_error_mm=worst_v,geometry_sha256=digest)
(B/'verification/blender_saved_file.json').write_text(json.dumps(r,indent=2),encoding='utf8');print(r);assert ok
