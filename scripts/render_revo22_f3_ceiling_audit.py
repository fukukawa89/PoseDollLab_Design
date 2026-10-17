import bpy,numpy as np,sys,json
from pathlib import Path
from mathutils import Vector
R=Path('E:/UnrealProjects/PoseDollLab_UE58_Design/PoseDoll_HW44_Plan/design');A=R/'Hardware/PoseDoll44/bench/revO22/F01_F3_audit';O=R/'Hardware/PoseDoll44/bench/revO22/O22F3_Release'
n=np.load(A/'ceiling_face.npz');d=json.loads((O/'reference/design/X046.json').read_text(encoding='utf8'));M=np.array(d['orientation']['matrix']);t=np.array(d['orientation']['source_translation_mm'])
bpy.ops.wm.read_factory_settings(use_empty=True)
colors=[('本体',(.20,.49,.66,1)),('落盘支撑',(.94,.34,.05,1)),('连接齿',(1,.75,.05,1)),('漏支撑内顶面',(.9,.04,.055,1))];mats=[]
for name,color in colors:
 mat=bpy.data.materials.new(name);mat.diffuse_color=color;mat.use_nodes=True;p=mat.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=color;p.inputs['Roughness'].default_value=.8;mats.append(mat)
for i,(vk,fk) in enumerate([('v','f'),('fin_v','fin_f'),('teeth_v','teeth_f')]):
 me=bpy.data.meshes.new(vk);me.from_pydata(n[vk].tolist(),[],n[fk].tolist());me.update();ob=bpy.data.objects.new(colors[i][0],me);bpy.context.collection.objects.link(ob);me.materials.append(mats[i])
 if i==0:
  me.materials.append(mats[3])
  for face in n['ceiling_faces']:me.polygons[int(face)].material_index=1
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=20;s.render.resolution_x=1200;s.render.resolution_y=1000;s.render.resolution_percentage=100
s.world=bpy.data.worlds.new('World');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.86,.89,.92,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.8
center=np.array([20,58,43])@M.T+t
cam=bpy.data.cameras.new('Camera');co=bpy.data.objects.new('Camera',cam);s.collection.objects.link(co);s.camera=co;co.location=Vector(np.array([-165,5,170])@M.T+t);co.rotation_euler=(Vector(center)-co.location).to_track_quat('-Z','Y').to_euler();cam.type='ORTHO';cam.ortho_scale=155;cam.clip_end=10000
for name,pos,power in [('Key',[-160,-50,160],40000),('Fill',[-120,200,80],22000)]:
 li=bpy.data.lights.new(name,'AREA');li.energy=power;li.size=150;ob=bpy.data.objects.new(name,li);s.collection.objects.link(ob);ob.location=Vector(np.array(pos)@M.T+t);ob.rotation_euler=(Vector(center)-ob.location).to_track_quat('-Z','Y').to_euler()
s.view_settings.view_transform='Standard';s.render.image_settings.file_format='PNG';s.render.filepath=str(A/'F01_unsupported_ceiling.png');bpy.ops.wm.save_as_mainfile(filepath=str(A/'F01_unsupported_ceiling.blend'));bpy.ops.render.render(write_still=True)
