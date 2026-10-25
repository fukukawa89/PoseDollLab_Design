"""Blender background only: exact exported geometry, editable hierarchy and poses."""
import bpy,json,sys,math,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
HERE=Path(__file__).resolve().parent;B=HERE.parents[1]/'bench/revO24'
sys.path.insert(0,str(HERE))
# Blender has numpy, but not the modelling kernel: FK is reproduced directly here.
p=json.loads((B/'profiles/arm_profile.json').read_text('utf8'))
data=json.loads((B/'assembly.json').read_text('utf8'));meshes=np.load(B/'assembly_meshes.npz')
poses=json.loads((B/'profiles/poses.json').read_text('utf8'))
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene;sc.unit_settings.system='METRIC';sc.unit_settings.length_unit='MILLIMETERS'
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL'
sc.display.shading.show_cavity=True;sc.display.shading.cavity_type='BOTH';sc.display.shading.show_shadows=True
sc.display.shading.background_type='WORLD';sc.world=bpy.data.worlds.new('Studio');sc.world.color=(.91,.93,.94)
sc.render.resolution_x=1400;sc.render.resolution_y=1600;sc.render.resolution_percentage=100
sc.view_settings.view_transform='Standard';sc.render.image_settings.file_format='PNG'
sc['revision']='O24A';sc['manufacturing_release']=False
sc['source_geometry_sha256']=hashlib.sha256((B/'assembly_meshes.npz').read_bytes()).hexdigest()
sc['scope']='UE-aligned left-arm digital layout; geometry and known limitations in verification reports'
groups={};mats={}
for item in data['parts']:
    token=item['frame']
    if token not in groups:
        ob=bpy.data.objects.new(token,None);sc.collection.objects.link(ob);groups[token]=ob
    role=item['role']
    if role not in mats:
        ma=bpy.data.materials.new(role);ma.diffuse_color=(*item['color'],1);mats[role]=ma
    i=str(item['i']);me=bpy.data.meshes.new(item['name']);me.from_pydata((meshes[i+'v']/1000).tolist(),[],meshes[i+'f'].tolist());me.update()
    ob=bpy.data.objects.new(item['name'],me);sc.collection.objects.link(ob);ob.data.materials.append(mats[role]);ob.parent=groups[token]
    ob['role']=role;ob['design_note']=item['notes']

def t(v):return Matrix.Translation(Vector(np.array(v)/1000))
def r(axis,a):return Matrix.Rotation(math.radians(a),4,Vector(axis))
def frames(q):
    a=lambda n:q.get(n,0);f={'chest':t(p['root'])}
    f['collar_z']=f['chest']@r([0,0,-1],a('clavicle_protract'));f['collar']=f['collar_z']@r([1,0,0],a('clavicle_elevate'))
    f['shoulder_base']=f['collar']@t(p['clavicle_vector']);f['shoulder_pitch']=f['shoulder_base']@r([0,-1,0],a('shoulder_flex'))
    f['shoulder_swing']=f['shoulder_pitch']@r([1,0,0],a('shoulder_abduct'));f['upper']=f['shoulder_swing']@r([0,0,-1],a('upperarm_roll'))
    f['elbow_base']=f['upper']@t([0,0,-p['upperarm_mm']]);f['elbow']=f['elbow_base']@r([0,-1,0],a('elbow_flex'))
    f['fore']=f['elbow']@r([0,0,-1],p['forearm_zero_clocking_deg']+a('forearm_roll'));f['wrist_base']=f['fore']@t([0,0,-p['forearm_mm']])
    f['wrist_flex']=f['wrist_base']@r([0,1,0],a('wrist_flex'));f['hand']=f['wrist_flex']@r([1,0,0],a('wrist_deviation'))
    return f
for index,(name,case) in enumerate(poses.items()):
    frame=1+index*24
    for key,m in frames(case['angles']).items():
        groups[key].matrix_world=m;groups[key].rotation_mode='QUATERNION'
        groups[key].keyframe_insert('location',frame=frame);groups[key].keyframe_insert('rotation_quaternion',frame=frame)
    sc.timeline_markers.new(case['label']+' / '+name,frame=frame)
sc.frame_end=1+(len(poses)-1)*24;sc.frame_set(1)
cam=bpy.data.cameras.new('O24 inspection');co=bpy.data.objects.new('O24 inspection',cam);sc.collection.objects.link(co);sc.camera=co
cam.type='ORTHO';cam.clip_start=.0005;cam.clip_end=100
(B/'images').mkdir(exist_ok=True)
def shot(name,center,span,direction=(1.6,2.5,.8)):
    cam.ortho_scale=span;co.location=Vector(center)+Vector(direction)
    co.rotation_euler=(Vector(center)-co.location).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=str(B/'images'/f'{name}.png');bpy.ops.render.render(write_still=True)
C=np.array(p['root'])/1000;S=(np.array(p['root'])+p['clavicle_vector'])/1000
shot('arm_isometric',S+[0,0,-.075],.32)
shot('arm_front',S+[0,0,-.075],.32,(3,0,.1))
shot('shoulder_detail',S+[0,-.01,-.006],.115)
W=S+[0,0,-(p['upperarm_mm']+p['forearm_mm'])/1000]
shot('wrist_detail',W+[0,0,-.005],.080)
sc.frame_set(1+4*24);shot('raised_arm',S+[0,0,.055],.30,(2.2,2.3,.5))
sc.frame_set(1);shot('arm_isometric',S+[0,0,-.075],.32)
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_distance=.34
        area.spaces.active.region_3d.view_location=Vector(S+[0,0,-.095])
bpy.ops.wm.save_as_mainfile(filepath=str(B/'O24A_left_arm.blend'))
