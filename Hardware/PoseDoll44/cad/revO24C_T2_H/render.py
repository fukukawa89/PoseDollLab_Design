"""Actual CAD renders, editable Blender assembly; no illustrative geometry."""
import bpy,json,math,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent;OUT=HERE.parents[1]/'bench/revO24C_T2_H'
d=json.loads((OUT/'assembly.json').read_text('utf8'));z=np.load(OUT/'assembly_meshes.npz')
bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene
sc.unit_settings.system='METRIC';sc.unit_settings.length_unit='MILLIMETERS';sc.render.engine='BLENDER_WORKBENCH'
sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_cavity=True;sc.display.shading.cavity_type='BOTH'
sc.world=bpy.data.worlds.new('Paper');sc.world.color=(.94,.96,.94);sc.display.shading.background_type='WORLD';sc.view_settings.view_transform='Standard'
sc.render.resolution_x=1500;sc.render.resolution_y=1100;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG'
objects={};mats={}
for p in d['parts']:
    if p['frame']=='coupon':continue
    i=p['index'];me=bpy.data.meshes.new(p['id']);me.from_pydata((z['v'+str(i)]/1000).tolist(),[],z['f'+str(i)].tolist());me.update()
    ob=bpy.data.objects.new(p['id'],me);sc.collection.objects.link(ob)
    if p['role'] not in mats:
        mat=bpy.data.materials.new(p['role']);mat.diffuse_color=(*p['color'],1);mats[p['role']]=mat
    ob.data.materials.append(mats[p['role']]);ob['label']=p['label'];ob['spec']=p['spec'];ob['note']=p['note'];objects[p['id']]=ob
cam=bpy.data.cameras.new('Inspection');co=bpy.data.objects.new('Inspection',cam);sc.collection.objects.link(co);sc.camera=co;cam.type='ORTHO';cam.clip_start=.001;cam.clip_end=100
(OUT/'images').mkdir(exist_ok=True)
def shot(name,explode=False,detail=False,direction=(1.5,3,1.1)):
    offsets={'H2-01':0,'M03':-8,'M02':-16,'H2-03':-24,'C_N1':6,'C_N2':6,'C_S1':-35,'C_S2':-35,'C_W1':-30,'C_W2':-30,
             'F01':7,'H2-02':15,'F02':23,'SP01':30,'SP02':37,'M04':44,'AX01':52}
    for id,ob in objects.items():ob.location=(0,offsets[id]/1000 if explode else 0,0);ob.hide_render=False
    bpy.context.view_layer.update();v=Vector(direction);co.rotation_euler=(-v).to_track_quat('-Z','Y').to_euler();R=co.rotation_euler.to_matrix();inv=R.transposed()
    pts=[]
    for ob in objects.values():
        for p in ob.bound_box:
            pp=ob.matrix_world@Vector(p)
            if detail and pp.z<-.018:pp.z=-.018
            pts.append(inv@pp)
    pts=np.array(pts);lo=pts.min(0);hi=pts.max(0);mid=R@Vector((lo+hi)/2)
    co.location=mid+v.normalized()*.7;cam.ortho_scale=max(hi[0]-lo[0],(hi[1]-lo[1])*sc.render.resolution_x/sc.render.resolution_y)*1.18
    sc.render.filepath=str(OUT/'images'/name);bpy.ops.render.render(write_still=True)
shot('assembled.png');shot('exploded.png',True);shot('joint_closeup.png',detail=True);shot('rear.png',detail=True,direction=(-1.5,-3,1.1))
for ob in objects.values():ob.location=(0,0,0)
sc['revision']=d['revision'];sc['physical_status']='UNTESTED';sc['geometry_sha256']=hashlib.sha256((OUT/'assembly_meshes.npz').read_bytes()).hexdigest()
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':area.spaces.active.region_3d.view_location=Vector((0,0,-.04));area.spaces.active.region_3d.view_distance=.2
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'O24C_T2_H.blend'))
(OUT/'verification/blender.json').write_text(json.dumps(dict(passed=True,parts=len(objects),geometry_sha256=sc['geometry_sha256']),indent=2),encoding='utf8')
