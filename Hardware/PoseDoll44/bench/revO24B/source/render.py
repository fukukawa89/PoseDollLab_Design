"""Blender background export from the verified B mesh archive."""
import bpy,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
HERE=Path(__file__).resolve().parent;B=HERE.parents[1]/'bench/revO24B'
data=json.loads((B/'assembly.json').read_text('utf8'));z=np.load(B/'assembly_meshes.npz');poses=json.loads((B/'profiles/presentation_poses.json').read_text('utf8'))
bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene;sc.unit_settings.system='METRIC';sc.unit_settings.length_unit='MILLIMETERS'
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_cavity=True;sc.display.shading.cavity_type='BOTH'
sc.world=bpy.data.worlds.new('O24B studio');sc.world.color=(.91,.94,.89);sc.display.shading.background_type='WORLD';sc.view_settings.view_transform='Standard'
sc.render.resolution_x=1440;sc.render.resolution_y=1200;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG'
sc['revision']='O24B';sc['manufacturing_release']=False;sc['geometry_sha256']=hashlib.sha256((B/'assembly_meshes.npz').read_bytes()).hexdigest();sc['mechanism']='Constrained 2DoF spherical wrist, R=Rx(deviation)Ry(flexion); proximal O24A unchanged'
groups={};materials={}
for p in data['parts']:
    token=p['frame']
    if token not in groups:
        ob=bpy.data.objects.new(token,None);sc.collection.objects.link(ob);groups[token]=ob
    color=tuple(p['color'])
    if p['name'].startswith('B_guide_pin'):color=(.53,.39,.75)
    if color not in materials:
        ma=bpy.data.materials.new(p['role']);ma.diffuse_color=(*color,1);materials[color]=ma
    i=str(p['i']);mesh=bpy.data.meshes.new(p['name']);mesh.from_pydata((z[i+'v']/1000).tolist(),[],z[i+'f'].tolist());mesh.update()
    ob=bpy.data.objects.new(p['name'],mesh);sc.collection.objects.link(ob);ob.parent=groups[token];ob.data.materials.append(materials[color]);ob['design_note']=p['notes'];ob['new_in_O24B']=p['new']
for index,(name,case) in enumerate(poses.items()):
    for token,ob in groups.items():
        m=np.array(case['frames'][token]);m[:3,3]/=1000;ob.matrix_world=Matrix(m.tolist());ob.rotation_mode='QUATERNION';ob.keyframe_insert('location',frame=1+index*30);ob.keyframe_insert('rotation_quaternion',frame=1+index*30)
    sc.timeline_markers.new(name,frame=1+index*30)
constant_curves=0
for ob in groups.values():
    action=ob.animation_data.action
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:key.interpolation='CONSTANT'
                    constant_curves+=1
assert constant_curves>0
sc['animation_note']='Seven discrete inspection poses; smooth FK animation is in preview/index.html. Independent world transforms must not be interpolated between poses.'
sc.frame_end=1+(len(poses)-1)*30;sc.frame_set(1)
camera=bpy.data.cameras.new('Inspection');co=bpy.data.objects.new('Inspection',camera);sc.collection.objects.link(co);sc.camera=co;camera.type='ORTHO';camera.clip_start=.001;camera.clip_end=100
(B/'images').mkdir(exist_ok=True)
W=np.array(poses['neutral']['frames']['wrist_base'])[:3,3]/1000
def shot(name,center,span,direction):
    bpy.context.view_layer.update()
    co.location=Vector(center)+Vector(direction);co.rotation_euler=(Vector(center)-co.location).to_track_quat('-Z','Y').to_euler()
    rot=co.rotation_euler.to_matrix();inv=rot.transposed()
    points=np.array([inv@(ob.matrix_world@Vector(v)) for ob in sc.objects if ob.type=='MESH' and not ob.hide_render for v in ob.bound_box])
    lo=points.min(0);hi=points.max(0);mid=rot@Vector((lo+hi)/2)
    co.location=mid+Vector(direction).normalized()*.7
    aspect=sc.render.resolution_x/sc.render.resolution_y
    camera.ortho_scale=max(hi[0]-lo[0],(hi[1]-lo[1])*aspect)*1.22
    sc.render.filepath=str(B/'images'/name);bpy.ops.render.render(write_still=True)
for ob in sc.objects:
    if ob.type=='MESH' and not ob.get('new_in_O24B',False):ob.hide_render=True
shot('wrist_solid.png',W+[0,0,-.004],.10,(2,3,1))
for ob in sc.objects:
    if ob.type=='MESH':ob.hide_render=False
shot('hybrid_arm.png',W+[0,0,.075],.31,(2,3,1))
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':area.spaces.active.region_3d.view_distance=.115;area.spaces.active.region_3d.view_location=Vector(W)
bpy.ops.wm.save_as_mainfile(filepath=str(B/'O24B_spherical_wrist.blend'))
verification=dict(status='PASS',mesh_objects=sum(1 for o in sc.objects if o.type=='MESH'),pose_count=len(poses),geometry_sha256=sc['geometry_sha256'])
(B/'verification/blender_export.json').write_text(json.dumps(verification,indent=2),encoding='utf8')
