"""Editable hierarchical assembly and review renders from exported O24D meshes."""
import bpy,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
B=Path(__file__).resolve().parents[2]/'bench/revO24D'
load=lambda n:json.loads((B/n).read_text('utf8'))
data=load('assembly.json');profile=load('profiles/device_profile.json');poses=load('profiles/poses.json');z=np.load(B/'assembly_meshes.npz')
bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene
sc.unit_settings.system='METRIC';sc.unit_settings.length_unit='MILLIMETERS'
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL'
sc.display.shading.show_cavity=True;sc.display.shading.cavity_type='BOTH';sc.display.shading.show_shadows=True
sc.world=bpy.data.worlds.new('O24D review');sc.world.color=(.90,.93,.92);sc.display.shading.background_type='WORLD'
sc.view_settings.view_transform='Standard';sc.render.resolution_x=1500;sc.render.resolution_y=1500;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG';sc['revision']='O24D';sc['S1_test_pass']='DESIGN ASSUMPTION, H04 WEAK CONNECTION EXCLUDED';sc['manufacturing_release']=False
sc['geometry_sha256']=hashlib.sha256((B/'assembly_meshes.npz').read_bytes()).hexdigest()
groups={};mats={};objects={}
for n in profile['nodes']:
    ob=bpy.data.objects.new(n['id'],None);sc.collection.objects.link(ob);groups[n['id']]=ob
    if n['parent']:ob.parent=groups[n['parent']]
    ob.location=Vector(n['offset_mm'])/1000;ob.rotation_mode='QUATERNION'
    ob['physical_axis']=str(n['axis']);ob['target_UE_bone']=n['target_bone'] or ''
for p in data['parts']:
    color=tuple(p['color']);mat=mats.get(color)
    if mat is None:mat=bpy.data.materials.new(p['role']);mat.diffuse_color=(*color,1);mats[color]=mat
    mesh=bpy.data.meshes.new(p['name']);i=str(p['i']);mesh.from_pydata((z[i+'v']/1000).tolist(),[],z[i+'f'].tolist());mesh.update()
    ob=bpy.data.objects.new(p['name'],mesh);sc.collection.objects.link(ob);ob.parent=groups[p['frame']];ob.data.materials.append(mat);objects[p['name']]=ob
    ob['design_note']=p['notes'];ob['review_group']=p['group'];ob['part_id']=p['name'];ob['manufacturing_release']=False
for pi,(name,p) in enumerate(poses.items()):
    frame=1+pi*24
    for n in profile['nodes']:
        ob=groups[n['id']]
        if n['axis'] is not None:
            from mathutils import Quaternion
            import math
            ob.rotation_quaternion=Quaternion(Vector(n['axis']),math.radians(p['angles'].get(n['id'],0)+n['zero_deg']))
        ob.keyframe_insert('rotation_quaternion',frame=frame)
    sc.timeline_markers.new(name,frame=frame)
for ob in groups.values():
    if ob.animation_data:
        for layer in ob.animation_data.action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        for key in curve.keyframe_points:key.interpolation='CONSTANT'
sc.frame_end=1+(len(poses)-1)*24;sc.frame_set(1)
wiredata=load('harness/routes.json');wireobjects={}
assert wiredata['geometry_sha256']==sc['geometry_sha256']
sc['harness_sha256']=hashlib.sha256((B/'harness/routes.json').read_bytes()).hexdigest()
wirecollection=bpy.data.collections.new('Harness A pose routing guides');sc.collection.children.link(wirecollection)
bankcolors={'A':(.1,.5,.3,1),'B':(.1,.35,.82,1),'C':(.85,.4,.12,1)}
for r in wiredata['spans']:
    curve=bpy.data.curves.new('wire_guide_'+r['id'],'CURVE');curve.dimensions='3D';curve.bevel_depth=r['diameter_mm']/2000;curve.bevel_resolution=3
    spline=curve.splines.new('POLY');spline.points.add(len(r['guide_A_mm'])-1)
    for point,xyz in zip(spline.points,r['guide_A_mm']):point.co=(*[x/1000 for x in xyz],1)
    ob=bpy.data.objects.new(curve.name,curve);wirecollection.objects.link(ob);wireobjects[r['id']]=(ob,r)
    mat=bpy.data.materials.get('Harness bank '+r['cables'][0][0])
    if mat is None:mat=bpy.data.materials.new('Harness bank '+r['cables'][0][0]);mat.diffuse_color=bankcolors[r['cables'][0][0]]
    curve.materials.append(mat);ob['review_note']='A pose routing guide, not physical bending geometry. Dress reserved service loops per CABLE_CUTLIST.'
    ob.driver_add('hide_viewport').driver.expression='frame != 1'
cam=bpy.data.cameras.new('Review camera');co=bpy.data.objects.new('Review camera',cam);sc.collection.objects.link(co);sc.camera=co
cam.type='ORTHO';cam.clip_start=.001;cam.clip_end=10
(B/'images').mkdir(exist_ok=True)
def shot(name,direction=(2.5,3.5,1.0),selector=lambda n:True,show_wires=False):
    for n,ob in objects.items():ob.hide_render=not selector(n)
    for ob,r in wireobjects.values():ob.hide_render=not show_wires or sc.frame_current!=1 or (show_wires=='board' and not r['end'].startswith('J'))
    bpy.context.view_layer.update();d=Vector(direction);co.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler();R=co.rotation_euler.to_matrix();inv=R.transposed()
    visible=list(objects.values())+[ob for ob,r in wireobjects.values()]
    pts=np.array([inv@(ob.matrix_world@Vector(v)) for ob in visible if not ob.hide_render for v in ob.bound_box]);lo=pts.min(0);hi=pts.max(0);mid=R@Vector((lo+hi)/2)
    co.location=mid+d.normalized()*1.8;cam.ortho_scale=max(hi[0]-lo[0],hi[1]-lo[1])*1.18
    sc.render.filepath=str(B/'images'/name);bpy.ops.render.render(write_still=True)
shot('full_body.png',show_wires=True);shot('front.png',(1,0,0));shot('back_wiring.png',(-1,0,.1),show_wires=True)
shot('electronics_back.png',(-2,1,.4),lambda n:n.startswith(('electronics_','backboard_')) or 'back_wire_tab' in n,show_wires='board')
shot('pelvis.png',(-2,3,1),lambda n:'hip_' in n or n.startswith('pelvi'))
shot('neck_clavicles.png',(2,3,1),lambda n:n.startswith('neck_') or 'clavicle' in n or 'head_' in n)
shot('S1_wrist.png',(2,3,1),lambda n:n.startswith('l_W') or n.startswith('l_wrist') or n.startswith('l_palm'))
handnormal=groups['l_wrist_flex'].matrix_world.to_3x3()@Vector((0,1,0))
shot('hand_palm.png',tuple(handnormal),lambda n:n=='l_palm')
shot('hand_back.png',tuple(-handnormal),lambda n:n=='l_palm')
shot('lumbar_closure.png',(2,3,1),lambda n:n.startswith('lumbar_') or n.startswith('pelvis_lumbar_'))
shot('knee_connection.png',(2,3,1),lambda n:n.startswith('l_knee_') or n=='l_thigh_tube')
for name in ['arms_side','sit','squat','cross']:
    sc.frame_set(1+list(poses).index(name)*24);shot(name+'.png')
sc.frame_set(1)
for ob in objects.values():ob.hide_render=False
shot('full_body.png',show_wires=True)
# Independent offline UE surface, rendered at the same scale and A pose.
ref=np.load(B/'reference/UE_A_surface.npz')
mesh=bpy.data.meshes.new('UE A surface reference');mesh.from_pydata((ref['vertices_mm']/1000).tolist(),[],ref['triangles'].tolist());mesh.update()
ob=bpy.data.objects.new('UE_A_visual_reference_ONLY',mesh);sc.collection.objects.link(ob)
mat=bpy.data.materials.new('UE reference white');mat.diffuse_color=(.82,.85,.86,1);ob.data.materials.append(mat)
physical=objects;objects={'UE_A_visual_reference_ONLY':ob}
for value in physical.values():value.hide_render=True
shot('UE_A_reference.png',(1,0,0))
ob.hide_render=True;ob.hide_viewport=True;objects=physical
for value in physical.values():value.hide_render=False
shot('full_body.png',show_wires=True)
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':area.spaces.active.region_3d.view_location=Vector((0,0,.28));area.spaces.active.region_3d.view_distance=.8
bpy.ops.wm.save_as_mainfile(filepath=str(B/'O24D_full_body.blend'))
(B/'verification/blender_export.json').write_text(json.dumps(dict(status='PASS',objects=len(objects),pose_count=len(poses),hierarchical_frames=len(groups),geometry_sha256=sc['geometry_sha256']),indent=2),encoding='utf8')
