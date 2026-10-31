"""Reopen the saved Blender artifact and compare all seven keyed poses."""
import bpy,json,hashlib
import numpy as np
from pathlib import Path
B=Path(__file__).resolve().parents[2]/'bench/revO24B'
expected=json.loads((B/'profiles/presentation_poses.json').read_text('utf8'))
worst_p=0.;worst_r=0.
for i,(name,case) in enumerate(expected.items()):
    bpy.context.scene.frame_set(1+i*30);bpy.context.view_layer.update()
    for key,value in case['frames'].items():
        if key not in bpy.data.objects:continue
        matrix=np.array(bpy.data.objects[key].matrix_world);target=np.array(value);target[:3,3]/=1000
        worst_p=max(worst_p,float(np.linalg.norm(matrix[:3,3]-target[:3,3]))*1000)
        worst_r=max(worst_r,float(np.max(abs(matrix[:3,:3]-target[:3,:3]))))
for i,(name,case) in enumerate(list(expected.items())[:-1]):
    bpy.context.scene.frame_set(16+i*30);bpy.context.view_layer.update()
    for key,value in case['frames'].items():
        if key not in bpy.data.objects:continue
        target=np.array(value);target[:3,3]/=1000
        assert np.max(abs(np.array(bpy.data.objects[key].matrix_world)-target))<1e-5,'Intermediate inspection pose drift'
meshes=sum(o.type=='MESH' for o in bpy.context.scene.objects)
geometry=hashlib.sha256((B/'assembly_meshes.npz').read_bytes()).hexdigest()
same=bpy.context.scene.get('geometry_sha256')==geometry
meta=json.loads((B/'assembly.json').read_text('utf8'));z=np.load(B/'assembly_meshes.npz');max_vertex=0.
for part in meta['parts']:
    actual=np.array([v.co for v in bpy.data.objects[part['name']].data.vertices])*1000
    target=z[str(part['i'])+'v'];assert actual.shape==target.shape
    max_vertex=max(max_vertex,float(np.max(abs(actual-target))))
result=dict(status='PASS' if meshes==113 and same and worst_p<.001 and worst_r<1e-5 and max_vertex<.001 else 'FAIL',
    mesh_objects=meshes,poses=len(expected),discrete_pose_holds_checked=6,geometry_sha256=geometry,geometry_sha256_matches=same,
    max_position_error_mm=worst_p,max_rotation_matrix_element_error=worst_r,max_mesh_vertex_error_mm=max_vertex)
(B/'verification/blender_saved_file.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(result)
if result['status']!='PASS':raise RuntimeError('Saved Blender mismatch')
