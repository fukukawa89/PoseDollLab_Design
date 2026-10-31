"""Independent Blender background rendering. Does not edit existing GUI scene."""
import bpy,numpy as np,sys
from pathlib import Path
from mathutils import Vector
def render(path,out):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    n=np.load(path);mats=[];allv=[]
    for name,color in [('PART',(.14,.48,.7,1)),('FIN',(.91,.31,.07,1)),('TEETH',(1,.72,.06,1))]:
        mat=bpy.data.materials.new(name);mat.diffuse_color=color;mat.use_nodes=True
        bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=color;bs.inputs['Roughness'].default_value=.7;mats.append(mat)
    for i,(name,vk,fk) in enumerate([('PART','v','f'),('FIN','fin_v','fin_f'),('TEETH','teeth_v','teeth_f')]):
        v=n[vk];f=n[fk]
        if not len(f):continue
        mesh=bpy.data.meshes.new(name);mesh.from_pydata(v.tolist(),[],f.tolist());mesh.update()
        ob=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(ob);ob.data.materials.append(mats[i]);allv.append(v)
    v=np.concatenate(allv);lo=v.min(0);hi=v.max(0);center=(lo+hi)/2;span=float(max(hi-lo))
    sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=24
    sc.render.resolution_x=1100;sc.render.resolution_y=900;sc.render.resolution_percentage=100
    sc.world=bpy.data.worlds.new('World');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.8,.85,.9,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.7
    for name,loc,power in [('Key',(-span,-span,span*3),span*span*2.5),('Fill',(span*2,span,span*2),span*span*1.2)]:
        ld=bpy.data.lights.new(name,'AREA');ld.energy=power;ld.shape='DISK';ld.size=span*2;ob=bpy.data.objects.new(name,ld);sc.collection.objects.link(ob);ob.location=Vector(center)+Vector(loc);ob.rotation_euler=(Vector(center)-ob.location).to_track_quat('-Z','Y').to_euler()
    cam=bpy.data.cameras.new('Camera');ob=bpy.data.objects.new('Camera',cam);sc.collection.objects.link(ob);sc.camera=ob;cam.type='ORTHO';cam.ortho_scale=span*1.6;cam.clip_end=10000
    ob.location=Vector(center)+Vector((span*1.4,-span*1.8,span*1.35));ob.rotation_euler=(Vector(center)-ob.location).to_track_quat('-Z','Y').to_euler()
    sc.view_settings.view_transform='Standard';sc.render.image_settings.file_format='PNG';sc.render.filepath=str(out)
    bpy.ops.wm.save_as_mainfile(filepath=str(Path(out).with_suffix('.blend')))
    bpy.ops.render.render(write_still=True)
if __name__=='__main__':
    a=sys.argv[sys.argv.index('--')+1:];render(a[0],a[1])

