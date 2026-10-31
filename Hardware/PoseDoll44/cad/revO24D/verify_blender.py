"""Reopen the actual saved .blend and compare it with the exported reference."""
import bpy,json,hashlib
import numpy as np
from pathlib import Path
B=Path(__file__).resolve().parents[2]/'bench/revO24D'
load=lambda n:json.loads((B/n).read_text('utf8'))
data=load('assembly.json');pp=load('profiles/poses.json');expected=load('profiles/pose_frames.json');z=np.load(B/'assembly_meshes.npz')
bpy.ops.wm.open_mainfile(filepath=str(B/'O24D_full_body.blend'))
sc=bpy.context.scene;errors=[];missing=[];max_pos=max_rot=max_mesh=0
for pi,name in enumerate(pp):
    sc.frame_set(1+pi*24);bpy.context.view_layer.update()
    for fr,mat in expected[name].items():
        if fr not in bpy.data.objects:missing.append(fr);continue
        actual=np.array(bpy.data.objects[fr].matrix_world);actual[:3,3]*=1000;m=np.array(mat)
        max_pos=max(max_pos,float(np.linalg.norm(actual[:3,3]-m[:3,3])));max_rot=max(max_rot,float(np.max(abs(actual[:3,:3]-m[:3,:3]))))
for p in data['parts']:
    if p['name'] not in bpy.data.objects:missing.append(p['name']);continue
    ob=bpy.data.objects[p['name']];v=np.array([x.co[:] for x in ob.data.vertices])*1000;want=z[str(p['i'])+'v']
    if v.shape!=want.shape:errors.append(p['name']+' vertex count');continue
    max_mesh=max(max_mesh,float(np.max(abs(v-want))))
    if ob.parent.name!=p['frame']:errors.append(p['name']+' parent')
wiredata=load('harness/routes.json');max_wire_error=0.
for row in wiredata['spans']:
    name='wire_guide_'+row['id']
    if name not in bpy.data.objects:missing.append(name);continue
    ob=bpy.data.objects[name];v=np.array([p.co[:3] for p in ob.data.splines[0].points])*1000
    want=np.array(row['guide_A_mm'])
    if v.shape!=want.shape:errors.append(name+' point count');continue
    max_wire_error=max(max_wire_error,float(np.max(abs(v-want))))
    if abs(ob.data.bevel_depth*2000-row['diameter_mm'])>1e-5:errors.append(name+' bundle diameter')
wire_hash=hashlib.sha256((B/'harness/routes.json').read_bytes()).hexdigest()
digest=hashlib.sha256((B/'assembly_meshes.npz').read_bytes()).hexdigest();ok=not missing and not errors and max_pos<.001 and max_rot<1e-5 and max_mesh<.001 and max_wire_error<.001 and sc['geometry_sha256']==digest and sc['harness_sha256']==wire_hash
r=dict(status='PASS' if ok else 'FAIL',geometry_sha256=digest,blend_sha256=hashlib.sha256((B/'O24D_full_body.blend').read_bytes()).hexdigest(),poses=len(pp),parts=len(data['parts']),max_frame_position_error_mm=max_pos,max_rotation_element_error=max_rot,max_local_vertex_error_mm=max_mesh,missing=missing,errors=errors)
r.update(harness_span_count=len(wiredata['spans']),max_wire_guide_error_mm=max_wire_error,harness_sha256=wire_hash)
(B/'verification/blender_saved_file.json').write_text(json.dumps(r,indent=2),encoding='utf8');print(r,flush=True)
if not ok:raise RuntimeError('Saved Blender assembly verification failed')
