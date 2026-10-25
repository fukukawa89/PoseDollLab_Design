"""Editable Blender model and assembly/exploded views of the exact export."""
import bpy, json, hashlib, math
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
HERE=Path(__file__).resolve().parent;B=HERE.parents[1]/'bench/revO24C_T1'
data=json.loads((B/'assembly.json').read_text('utf8'));z=np.load(B/'assembly_meshes.npz')
bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene
sc.unit_settings.system='METRIC';sc.unit_settings.length_unit='MILLIMETERS';sc.render.engine='BLENDER_WORKBENCH'
sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_cavity=True;sc.display.shading.cavity_type='BOTH'
sc.world=bpy.data.worlds.new('Warm paper');sc.world.color=(.92,.94,.93);sc.display.shading.background_type='WORLD';sc.view_settings.view_transform='Standard'
sc.render.resolution_x=1500;sc.render.resolution_y=1200;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG'
colors={'structure':(.43,.70,.65),'rotor':(.93,.63,.25),'metal':(.58,.64,.71),'bearing':(.18,.25,.30),'friction':(.58,.32,.16),'magnet':(.81,.25,.30)}
materials={};objects={};groups={}
for role,color in colors.items():
    mat=bpy.data.materials.new(role);mat.diffuse_color=(*color,1);materials[role]=mat
for st in ['H','R','W','C']:
    parent=bpy.data.objects.new(st+'_station',None);sc.collection.objects.link(parent);parent.location=np.array(data['station_locations'][st])/1000;groups[st]=parent
for p in data['parts']:
    i=p['index'];me=bpy.data.meshes.new(p['id']);me.from_pydata((z['v'+str(i)]/1000).tolist(),[],z['f'+str(i)].tolist());me.update()
    ob=bpy.data.objects.new(p['id'],me);sc.collection.objects.link(ob);ob.parent=groups[p['station']];ob.data.materials.append(materials[p['role']]);ob['part_label']=p['label'];ob['printable']=p['printable'];ob['note']=p['note'];objects[p['id']]=ob
cam=bpy.data.cameras.new('Inspection');co=bpy.data.objects.new('Inspection',cam);sc.collection.objects.link(co);sc.camera=co;cam.type='ORTHO';cam.clip_start=.001;cam.clip_end=100
(B/'images').mkdir(exist_ok=True)
def shot(name,station=None,explode=False,crop=False,direction=(2,-3,1.2)):
    for p in data['parts']:
        ob=objects[p['id']];ob.hide_render=p['station']=='C' or (station is not None and p['station']!=station);ob.location=(0,0,0)
        if crop and p['id']=='W09':ob.hide_render=True
        if explode and p['station']==station:
            bounds=np.array(p['bounds_mm']);centre=bounds.mean(0);off=np.zeros(3)
            if station=='W':
                if p['id'] in ['W01','W02'] or 'ball_' in p['id']:off[0]=15*np.sign(centre[0])
                elif p['id']=='W03':off[2]=18
                elif p['id']=='W09' or 'lever_' in p['id']:off[2]=-20
                elif p['id'] in ['W04','W05']:off[1]=15*np.sign(centre[1])
                elif p['id']!='W08':off[1]=28*np.sign(centre[1])
                if p['id']=='W08':off[2]=28
            else:off[1]=centre[1]*1.5
            ob.location=off/1000
    bpy.context.view_layer.update();d=Vector(direction);co.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler();R=co.rotation_euler.to_matrix();inv=R.transposed()
    pts=np.array([inv@(ob.matrix_world@Vector(v)) for ob in objects.values() if not ob.hide_render for v in ob.bound_box]);lo=pts.min(0);hi=pts.max(0);mid=R@Vector((lo+hi)/2)
    co.location=mid+d.normalized()*.7;cam.ortho_scale=max(hi[0]-lo[0],(hi[1]-lo[1])*sc.render.resolution_x/sc.render.resolution_y)*1.16
    sc.render.filepath=str(B/'images'/name);bpy.ops.render.render(write_still=True)
shot('kit.png')
shot('H_assembled.png','H');shot('H_exploded.png','H',True)
shot('R_assembled.png','R')
shot('W_assembled.png','W',crop=True);shot('W_exploded.png','W',True,crop=True,direction=(2,-3,.8))
for ob in objects.values():ob.location=(0,0,0);ob.hide_render=False
sc['geometry_sha256']=hashlib.sha256((B/'assembly_meshes.npz').read_bytes()).hexdigest();sc['stage']='PRINTABLE_BENCH_PROTOTYPE_UNTESTED'
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':area.spaces.active.region_3d.view_location=Vector((0,0,-.03));area.spaces.active.region_3d.view_distance=.5
bpy.ops.wm.save_as_mainfile(filepath=str(B/'O24C_T1_kit.blend'))
(B/'verification/blender_export.json').write_text(json.dumps(dict(passed=True,parts=len(objects),geometry_sha256=sc['geometry_sha256']),indent=2),encoding='utf8')
