"""Read-only audit of the saved Blender file against exported pose transforms."""
import bpy,json,hashlib
import numpy as np
from pathlib import Path
B=Path(__file__).resolve().parents[2]/'bench/revO24'
expected=json.loads((B/'profiles/pose_frames.json').read_text('utf8'))
worst_p=0.;worst_r=0.
for i,(name,frames) in enumerate(expected.items()):
    bpy.context.scene.frame_set(1+i*24)
    bpy.context.view_layer.update()
    for key,value in frames.items():
        matrix=np.array(bpy.data.objects[key].matrix_world);target=np.array(value);target[:3,3]/=1000
        worst_p=max(worst_p,float(np.linalg.norm(matrix[:3,3]-target[:3,3]))*1000)
        worst_r=max(worst_r,float(np.max(abs(matrix[:3,:3]-target[:3,:3]))))
meshes=sum(o.type=='MESH' for o in bpy.context.scene.objects)
geometry=hashlib.sha256((B/'assembly_meshes.npz').read_bytes()).hexdigest()
same=bpy.context.scene.get('source_geometry_sha256')==geometry
result=dict(status='PASS' if meshes==124 and same and worst_p<.001 and worst_r<1e-5 else 'FAIL',mesh_objects=meshes,poses=len(expected),geometry_sha256_matches=same,max_position_error_mm=worst_p,max_rotation_matrix_element_error=worst_r)
(B/'verification/blender_saved_file.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(result)
if result['status']!='PASS':raise RuntimeError('Saved Blender mismatch')
