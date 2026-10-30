"""Blender-only rendering of the exact extracted mechanical production bodies."""
import bpy,json,math,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
B=Path(__file__).resolve().parents[2]/'bench/revO24E_LArm_Stock_R2'
load=lambda n:json.loads((B/n).read_text('utf8'))
data=load('production_assembly.json');profile=load('profiles/arm_profile.json');poses=load('profiles/poses.json');kit=load('kit.json');z=np.load(B/'production_meshes.npz')
lookup={r['part_number']:r for r in kit['structural_parts']+kit['hardware']}
bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene
sc.unit_settings.system='METRIC';sc.unit_settings.length_unit='MILLIMETERS'
sc.render.engine='BLENDER_WORKBENCH';shade=sc.display.shading;shade.light='STUDIO';shade.color_type='MATERIAL';shade.show_cavity=True;shade.cavity_type='BOTH';shade.show_shadows=True
sc.world=bpy.data.worlds.new('Arm review');sc.world.color=(.91,.93,.94);shade.background_type='WORLD';sc.view_settings.view_transform='Standard'
sc.render.resolution_x=1300;sc.render.resolution_y=1400;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG'
sc['revision']='O24E_LArm_Stock_R2';sc['physical_tested']=False;sc['production_mesh_sha256']=hashlib.sha256((B/'production_meshes.npz').read_bytes()).hexdigest();sc['source_production_sha256']=kit['source_production_sha256']
sc['scope']='Left shoulder to palm; fixed S2-P004 input; seven physical axes; no electronics or magnets. Common hardware trial; final STL geometry.'
groups={};objects={};records={};materials={}
colors={'structure':(.66,.75,.74),'metal':(.32,.36,.40),'spring':(.15,.34,.69),'friction':(.51,.44,.31),'bearing':(.53,.57,.62)}
for n in profile['nodes']:
    ob=bpy.data.objects.new(n['id'],None);sc.collection.objects.link(ob);groups[n['id']]=ob
    if n['parent']:ob.parent=groups[n['parent']]
    ob.location=Vector(n['offset_mm'])/1000;ob.rotation_mode='QUATERNION';ob['axis']=str(n['axis']);ob['target_UE_bone']=n['target_bone'] or ''
for p in data['parts']:
    color=colors[p['role']]
    if p.get('sku')=='A8':color=colors['spring']
    if p['part_number']=='S2-P004':color=(.48,.62,.61)
    mat=materials.get(color)
    if mat is None:mat=bpy.data.materials.new(p['role']);mat.diffuse_color=(*color,1);materials[color]=mat
    i=str(p['i']);mesh=bpy.data.meshes.new(p['part_number']);mesh.from_pydata((z[i+'v']/1000).tolist(),[],z[i+'f'].tolist());mesh.update()
    ob=bpy.data.objects.new(p['part_number'],mesh);sc.collection.objects.link(ob);ob.parent=groups[p['frame']];ob.data.materials.append(mat);objects[p['part_number']]=ob;records[p['part_number']]=p
    r=lookup[p['part_number']];ob['part_number']=p['part_number'];ob['description']=r.get('kit_label',r.get('feature',''));ob['sku']=r.get('sku') or p.get('sku') or '';ob['notes']=r.get('spec',p.get('notes',''));ob['material_requirement']=p.get('material','')
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
def shot(name,direction=(2.5,3.5,1.),predicate=lambda p:True):
    for key,ob in objects.items():ob.hide_render=not predicate(records[key])
    bpy.context.view_layer.update();d=Vector(direction);co.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler();R=co.rotation_euler.to_matrix();inv=R.transposed()
    pts=np.array([inv@(ob.matrix_world@Vector(v)) for ob in objects.values() if not ob.hide_render for v in ob.bound_box]);lo=pts.min(0);hi=pts.max(0);co.location=R@Vector((lo+hi)/2)+d.normalized()*1.2;cam.ortho_scale=max((hi[0]-lo[0])*1400/1300,hi[1]-lo[1])*1.15
    sc.render.filepath=str(B/'images'/name);bpy.ops.render.render(write_still=True)
shot('arm.png');shot('front.png',(1,0,0));shot('shoulder.png',(2.5,3.5,1),lambda p:p['frame'] in ['l_clavicle_elevate','l_shoulder_flex','l_shoulder_abduct','l_upperarm_roll'])
shot('wrist.png',(3,3,1),lambda p:p['frame'] in ['l_forearm_roll','l_wrist_flex','l_wrist_deviation'])
shot('P007_R2.png',(4,2,1),lambda p:p['name']=='UPPER_ARM')
oldroot=B.parent/'revO24E_LArm_Stock';olddata=json.loads((oldroot/'production_assembly.json').read_text('utf8'));oldp=next(p for p in olddata['parts'] if p['name']=='UPPER_ARM');oldz=np.load(oldroot/'production_meshes.npz');oi=str(oldp['i']);om=bpy.data.meshes.new('R1_P007_COMPARISON');om.from_pydata((oldz[oi+'v']/1000).tolist(),[],oldz[oi+'f'].tolist());om.update();ob=bpy.data.objects.new('R1_P007_COMPARISON',om);sc.collection.objects.link(ob);ob.parent=groups[oldp['frame']];ob.data.materials.append(objects['S2-P007'].data.materials[0]);objects['R1_P007_COMPARISON']=ob;records['R1_P007_COMPARISON']={'name':'R1_OLD_P007'}
shot('P007_R1.png',(4,2,1),lambda p:p['name']=='R1_OLD_P007');objects.pop('R1_P007_COMPARISON');records.pop('R1_P007_COMPARISON');bpy.data.objects.remove(ob,do_unlink=True)
sc.frame_set(1+24*list(poses).index('arms_elbow_max'));shot('elbow_flex.png');sc.frame_set(1);shot('arm.png')
for ob in objects.values():ob.hide_render=False
bpy.context.view_layer.update()
points=np.array([ob.matrix_world@Vector(v) for ob in objects.values() for v in ob.bound_box]);center=Vector((points.min(0)+points.max(0))/2)
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':area.spaces.active.region_3d.view_location=center;area.spaces.active.region_3d.view_distance=.4
bpy.ops.wm.save_as_mainfile(filepath=str(B/'O24E_left_arm_stock_R2.blend'))
