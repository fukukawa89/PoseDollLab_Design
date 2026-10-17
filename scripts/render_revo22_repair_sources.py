from pathlib import Path
import bpy,numpy as np,json,sys
R=Path(__file__).resolve().parents[1];B=R/'Hardware/PoseDoll44/bench/revO22';O=B/'a1mini_fins_v4'
from mathutils import Vector
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
sh=scene.display.shading;sh.light='STUDIO';sh.color_type='OBJECT';sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH';sh.background_type='WORLD';scene.world.color=(.93,.95,.98);scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='Standard'
for k,pid in enumerate(['X046','X038','X079','H006','X001','N003']):
 n=np.load(B/'O22F3_Release/reference/parts'/f'{pid}.npz');v=n['source_v'];f=n['f'];size=np.ptp(v,0);v=(v-(v.min(0)+v.max(0))/2)/max(size)*40
 v+=np.array([((k%3)-1)*62,-(k//3)*58,0]);m=bpy.data.meshes.new(pid);m.from_pydata(v.tolist(),[],f.tolist());ob=bpy.data.objects.new(pid,m);bpy.context.collection.objects.link(ob);ob.color=(.26,.55,.75,1)
 # Bed-scale-free comparison; each part normalized independently for seeing features.
 curve=bpy.data.curves.new(pid+'label',type='FONT');curve.body=pid+'  '+str(np.round(size,1));curve.size=2.2;obj=bpy.data.objects.new(pid+'label',curve);bpy.context.collection.objects.link(obj);obj.location=(k%3*62-85,-(k//3)*58-25,0);obj.color=(.05,.09,.15,1)
camdata=bpy.data.cameras.new('camera');cam=bpy.data.objects.new('camera',camdata);bpy.context.collection.objects.link(cam);cam.location=(80,-150,170);target=Vector((0,-28,0));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();camdata.type='ORTHO';camdata.ortho_scale=210;scene.camera=cam;scene.render.filepath=str(O/'source_views.png');bpy.ops.render.render(write_still=True)
