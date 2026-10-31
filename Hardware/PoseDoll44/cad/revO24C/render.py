"""Editable Blender C assembly and inspection images, from the audited NPZ."""
import bpy,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
HERE=Path(__file__).resolve().parent;B=HERE.parents[1]/'bench/revO24C'
load=lambda p:json.loads(p.read_text('utf8'))
data=load(B/'assembly.json');z=np.load(B/'assembly_meshes.npz');poses=load(B/'profiles/pose_frames.json')
bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene;sc.unit_settings.system='METRIC';sc.unit_settings.length_unit='MILLIMETERS'
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_cavity=True;sc.display.shading.cavity_type='BOTH'
sc.world=bpy.data.worlds.new('O24C studio');sc.world.color=(.91,.94,.89);sc.display.shading.background_type='WORLD';sc.view_settings.view_transform='Standard'
sc.render.resolution_x=1400;sc.render.resolution_y=1300;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG'
sc['revision']='O24C';sc['manufacturing_release']=False;sc['geometry_sha256']=hashlib.sha256((B/'assembly_meshes.npz').read_bytes()).hexdigest()
groups={};materials={}
for token in poses['neutral']:
    ob=bpy.data.objects.new(token,None);sc.collection.objects.link(ob);groups[token]=ob
for p in data['parts']:
    color=tuple(p['color'])
    if p['name'].startswith('C_guide_pin'):color=(.53,.39,.75)
    if color not in materials:
        mat=bpy.data.materials.new(p['role']);mat.diffuse_color=(*color,1);materials[color]=mat
    i=str(p['i']);mesh=bpy.data.meshes.new(p['name']);mesh.from_pydata((z[i+'v']/1000).tolist(),[],z[i+'f'].tolist());mesh.update()
    ob=bpy.data.objects.new(p['name'],mesh);sc.collection.objects.link(ob);ob.parent=groups[p['frame']];ob.data.materials.append(materials[color]);ob['design_note']=p['notes'];ob['changed_in_C']=p['changed']
for index,(name,frame) in enumerate(poses.items()):
    for token,ob in groups.items():
        m=np.array(frame[token]);m[:3,3]/=1000;ob.matrix_world=Matrix(m.tolist());ob.rotation_mode='QUATERNION';ob.keyframe_insert('location',frame=1+index*24);ob.keyframe_insert('rotation_quaternion',frame=1+index*24)
    sc.timeline_markers.new(name,frame=1+index*24)
for ob in groups.values():
    for layer in ob.animation_data.action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:key.interpolation='CONSTANT'
sc['animation_note']='18 discrete inspected poses. Constant keys; no claim that interpolating world frames is a valid mechanical trajectory.'
sc.frame_end=1+(len(poses)-1)*24;sc.frame_set(1)
camera=bpy.data.cameras.new('Inspection');co=bpy.data.objects.new('Inspection',camera);sc.collection.objects.link(co);sc.camera=co;camera.type='ORTHO';camera.clip_start=.001;camera.clip_end=100
(B/'images').mkdir(exist_ok=True)
def shot(name,filter):
    for ob in sc.objects:
        if ob.type=='MESH':ob.hide_render=not filter(ob.name)
    bpy.context.view_layer.update();direction=Vector((2,3,1));co.rotation_euler=(-direction).to_track_quat('-Z','Y').to_euler();R=co.rotation_euler.to_matrix();inv=R.transposed()
    points=np.array([inv@(ob.matrix_world@Vector(v)) for ob in sc.objects if ob.type=='MESH' and not ob.hide_render for v in ob.bound_box]);lo=points.min(0);hi=points.max(0);mid=R@Vector((lo+hi)/2)
    co.location=mid+direction.normalized()*.7;aspect=sc.render.resolution_x/sc.render.resolution_y;camera.ortho_scale=max(hi[0]-lo[0],(hi[1]-lo[1])*aspect)*1.25
    sc.render.filepath=str(B/'images'/name);bpy.ops.render.render(write_still=True)
shot('compact_arm.png',lambda n:True)
shot('shoulder.png',lambda n:n.startswith(('shoulder_','humeral_')))
shot('elbow.png',lambda n:n.startswith(('elbow_','forearm_')))
shot('wrist.png',lambda n:n.startswith('C_'))
sc.frame_set(1+list(poses).index('elbow_max')*24);shot('deep_fold.png',lambda n:True)
sc.frame_set(1)
for ob in sc.objects:
    if ob.type=='MESH':ob.hide_render=False
W=np.array(poses['neutral']['elbow_base'])[:3,3]/1000
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':area.spaces.active.region_3d.view_location=Vector(W);area.spaces.active.region_3d.view_distance=.35
bpy.ops.wm.save_as_mainfile(filepath=str(B/'O24C_compact_arm.blend'))
(B/'verification/blender_export.json').write_text(json.dumps(dict(status='PASS',parts=len(data['parts']),poses=len(poses),geometry_sha256=sc['geometry_sha256']),indent=2),encoding='utf8')
