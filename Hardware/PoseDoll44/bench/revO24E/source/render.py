"""Blender background: editable production assembly, exact frozen E meshes."""
import bpy,json,hashlib,math
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
B=Path(__file__).resolve().parents[2]/'bench/revO24E'
load=lambda name:json.loads((B/name).read_text('utf8'))
data=load('production_assembly.json');profile=load('profiles/device_profile.json');poses=load('profiles/poses.json');z=np.load(B/'production_meshes.npz')
inventory=load('production_parts.json');lookup={r['part_number']:r for r in inventory['structural_parts']+inventory['hardware']}
bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene;sc.unit_settings.system='METRIC';sc.unit_settings.length_unit='MILLIMETERS'
sc.render.engine='BLENDER_WORKBENCH';shade=sc.display.shading;shade.light='STUDIO';shade.color_type='MATERIAL';shade.show_cavity=True;shade.cavity_type='BOTH';shade.show_shadows=True
sc.world=bpy.data.worlds.new('E review background');sc.world.color=(.91,.93,.94);shade.background_type='WORLD';sc.view_settings.view_transform='Standard'
sc.render.resolution_x=1400;sc.render.resolution_y=1500;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG'
sc['revision']='O24E';sc['manufacturing_release']=False;sc['geometry_sha256']=hashlib.sha256((B/'assembly_meshes.npz').read_bytes()).hexdigest();sc['accepted_H_W']='User accepted T6 W and H via T5/T6 inheritance. No invented cycle count.'
sc['production_mesh_sha256']=hashlib.sha256((B/'production_meshes.npz').read_bytes()).hexdigest()
groups={};objects={};mats={};records={}
colors={'structure':(.66,.75,.74),'rotor':(.32,.57,.56),'shell':(.78,.81,.79),'metal':(.32,.36,.40),'spring':(.15,.34,.69),'friction':(.51,.44,.31),'bearing':(.53,.57,.62),'pcb':(.08,.32,.20),'connector':(.14,.16,.17),'magnet':(.16,.14,.20)}
for n in profile['nodes']:
    ob=bpy.data.objects.new(n['id'],None);sc.collection.objects.link(ob);groups[n['id']]=ob
    if n['parent']:ob.parent=groups[n['parent']]
    ob.location=Vector(n['offset_mm'])/1000;ob.rotation_mode='QUATERNION';ob['axis']=str(n['axis']);ob['target_UE_bone']=n['target_bone'] or ''
for p in data['parts']:
    matkey='metal' if p['name'].startswith('E-M') else p['role'];color=colors[matkey]
    if p.get('sku')=='A8':color=colors['spring']
    mat=mats.get(color)
    if mat is None:mat=bpy.data.materials.new(matkey);mat.diffuse_color=(*color,1);mats[color]=mat
    i=str(p['i']);mesh=bpy.data.meshes.new(p['name']);mesh.from_pydata((z[i+'v']/1000).tolist(),[],z[i+'f'].tolist());mesh.update()
    ob=bpy.data.objects.new(p['name'],mesh);sc.collection.objects.link(ob);ob.parent=groups[p['frame']];ob.data.materials.append(mat);objects[p['name']]=ob;records[p['name']]=p
    r=lookup[p['name']];ob['description']=r.get('label',r.get('feature',''));ob['source_features']=';'.join(r.get('source_features',[]));ob['part_number']=p['name'];ob['sku']=p.get('sku') or '';ob['notes']=p.get('notes','');ob['material_requirement']=p.get('material','')
for pi,(name,p) in enumerate(poses.items()):
    frame=1+24*pi
    for n in profile['nodes']:
        ob=groups[n['id']]
        if n['axis'] is not None:ob.rotation_quaternion=Quaternion(Vector(n['axis']),math.radians(p['angles'].get(n['id'],0)+n['zero_deg']))
        ob.keyframe_insert('rotation_quaternion',frame=frame)
    sc.timeline_markers.new(name,frame=frame)
for ob in groups.values():
    if ob.animation_data:
        for layer in ob.animation_data.action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        for key in curve.keyframe_points:key.interpolation='CONSTANT'
sc.frame_end=1+24*(len(poses)-1);sc.frame_set(1)
cam=bpy.data.cameras.new('Review');co=bpy.data.objects.new('Review',cam);sc.collection.objects.link(co);sc.camera=co;cam.type='ORTHO';cam.clip_start=.001;cam.clip_end=10
(B/'images').mkdir(exist_ok=True)
def shot(name,direction=(2.5,3.5,1.),predicate=lambda p:True):
    for key,ob in objects.items():ob.hide_render=not predicate(records[key])
    bpy.context.view_layer.update();d=Vector(direction);co.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler();R=co.rotation_euler.to_matrix();inv=R.transposed()
    pts=np.array([inv@(ob.matrix_world@Vector(v)) for ob in objects.values() if not ob.hide_render for v in ob.bound_box]);lo=pts.min(0);hi=pts.max(0);co.location=R@Vector((lo+hi)/2)+d.normalized()*1.8;cam.ortho_scale=max((hi[0]-lo[0])*1500/1400,hi[1]-lo[1])*1.14
    sc.render.filepath=str(B/'images'/name);bpy.ops.render.render(write_still=True)
shot('full_body.png');shot('front.png',(1,0,0));shot('side.png',(0,1,0));shot('back.png',(-1,0,0))
shot('left_arm.png',(2.5,3.5,1),lambda p:p['frame'].startswith('l_') and not any(k in p['frame'] for k in ['hip','knee','ankle','toe']))
shot('double_axis_wrist.png',(3,3,1),lambda p:p['frame'].startswith('l_wrist') or p['frame']=='l_forearm_roll')
shot('forearm_retention.png',(3,3,1),lambda p:p['frame'] in ['l_elbow_flex','l_forearm_roll'])
for name in ['arms_side','sit','squat']:
    sc.frame_set(1+24*list(poses).index(name));shot(name+'.png')
sc.frame_set(1)
for ob in objects.values():ob.hide_render=False
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':area.spaces.active.region_3d.view_location=Vector((0,0,.28));area.spaces.active.region_3d.view_distance=.8
bpy.ops.wm.save_as_mainfile(filepath=str(B/'O24E_production_assembly.blend'))
