"""Render the delivered fist directly from its indexed CAD mesh."""
import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
B=Path(__file__).resolve().parents[1]/'Hardware/PoseDoll44/bench/revO23'
bpy.ops.wm.read_factory_settings(use_empty=True)
doc=json.loads((B/'assembly.json').read_text('utf8'))
r=next(r for r in doc['items'] if r['key']=='frame/hand_l')
z=np.load(B/'assembly.npz');i=str(r['index']);v=z[i+'v']/1000;f=z[i+'f']
me=bpy.data.meshes.new('Actual left fist');me.from_pydata(v.tolist(),[],f.tolist());me.update()
ob=bpy.data.objects.new('frame/hand_l',me);bpy.context.scene.collection.objects.link(ob)
mat=bpy.data.materials.new('Printed material');mat.diffuse_color=(.79,.78,.71,1);ob.data.materials.append(mat)
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO'
s.display.shading.color_type='MATERIAL';s.display.shading.show_shadows=True;s.display.shading.show_cavity=True
s.display.shading.cavity_type='BOTH';s.display.shading.background_type='WORLD'
s.world=bpy.data.worlds.new('Studio');s.world.color=(.8,.83,.86)
s.render.resolution_x=1100;s.render.resolution_y=1000;s.render.resolution_percentage=100
target=(v.min(0)+v.max(0))/2;cam=bpy.data.cameras.new('Camera');co=bpy.data.objects.new('Camera',cam)
s.collection.objects.link(co);s.camera=co;cam.type='ORTHO';cam.ortho_scale=np.ptp(v,axis=0).max()*1.35
for name,direction in [('fist_detail',(2,-2,-.8)),('fist_front',(2,0,0))]:
    co.location=Vector(target)+Vector(direction)
    co.rotation_euler=(Vector(target)-co.location).to_track_quat('-Z','Y').to_euler()
    s.render.filepath=str(B/'images'/(name+'.png'));bpy.ops.render.render(write_still=True)
