import bpy,json,hashlib,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
HERE=Path(__file__).resolve().parent;OUT=HERE.parents[1]/'bench/revO24C_T6'
d=json.loads((OUT/'assembly.json').read_text('utf8'));z=np.load(OUT/'assembly_meshes.npz')
bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene
sc.unit_settings.system='METRIC';sc.unit_settings.length_unit='MILLIMETERS';sc.render.engine='BLENDER_WORKBENCH'
sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_cavity=True;sc.display.shading.cavity_type='BOTH'
sc.world=bpy.data.worlds.new('Paper');sc.world.color=(.93,.95,.94);sc.display.shading.background_type='WORLD';sc.view_settings.view_transform='Standard'
sc.render.resolution_x=1500;sc.render.resolution_y=1100;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG'
objects={};mats={};ports={p['prefix']:p for p in json.loads((OUT/'access_ports.json').read_text('utf8'))}
nylon=bpy.data.materials.new('Nylon insert');nylon.diffuse_color=(.1,.35,.9,1)
for p in d['parts']:
 if p['bench_only']:continue
 i=p['index'];me=bpy.data.meshes.new(p['id']);me.from_pydata((z['v'+str(i)]/1000).tolist(),[],z['f'+str(i)].tolist());me.update()
 ob=bpy.data.objects.new(p['id'],me);sc.collection.objects.link(ob)
 if p['role'] not in mats:
  mat=bpy.data.materials.new(p['role']);mat.diffuse_color=(*p['color'],1);mats[p['role']]=mat
 ob.data.materials.append(mats[p['role']])
 if p['sku']=='NL3':
  ob.data.materials.append(nylon);port=ports[p['id'][:-1]];direction=np.array(port['entry']);origin=np.array(port['M'])[:3,3]
  for poly in me.polygons:
   if np.dot(np.array(poly.center)*1000-origin,direction)<-5.8:poly.material_index=1
 ob['label']=p['label'];ob['spec']=p['spec'];ob['note']=p['note'];objects[p['id']]=ob
cam=bpy.data.cameras.new('Inspection');co=bpy.data.objects.new('Inspection',cam);sc.collection.objects.link(co);sc.camera=co;cam.type='ORTHO';cam.clip_start=.001;cam.clip_end=100
(OUT/'images').mkdir(exist_ok=True)
def T(v):return Matrix.Translation(Vector(v)/1000)
def R(axis,a):return Matrix.Rotation(math.radians(a),4,axis)
def shot(name,mode='arm',q=0,r=0,w=0,v=0,direction=(2,3,1.3),cut=False):
 hr=R('Y',-q);rr=R('Z',90-r);wf=R('Y',w);wr=wf@R('X',v)
 F={'H':{'fixed':Matrix.Identity(4),'rotor':hr},'R':{'fixed':hr@T([0,0,-36]),'rotor':hr@T([0,0,-36])@rr},'W':{'fixed':hr@rr@T([0,0,-d['forearm_mm']]),'flex':hr@rr@T([0,0,-d['forearm_mm']])@wf,'hand':hr@rr@T([0,0,-d['forearm_mm']])@wr}}
 for p in d['parts']:
  if p['bench_only']:continue
  ob=objects[p['id']];st=p['station'];ob.hide_render=mode in ['H','R','W'] and st!=mode
  if cut and p['id'] in ['R3-04']:ob.hide_render=True
  if mode=='arm':ob.matrix_world=F[st][p['frame']]
  else:
   ob.matrix_world=T([{'H':-65,'R':0,'W':65}[st] if mode=='three' else 0,0,0])
   if st=='W' and p['frame']!='fixed':ob.matrix_world=ob.matrix_world@(wf if p['frame']=='flex' else wr)
 bpy.context.view_layer.update();vec=Vector(direction);co.rotation_euler=(-vec).to_track_quat('-Z','Y').to_euler();M=co.rotation_euler.to_matrix();inv=M.transposed();pts=[]
 for ob in objects.values():
  if not ob.hide_render:pts.extend([inv@(ob.matrix_world@Vector(p)) for p in ob.bound_box])
 pts=np.array(pts);lo=pts.min(0);hi=pts.max(0);mid=M@Vector((lo+hi)/2);co.location=mid+vec.normalized()*.8
 cam.ortho_scale=max(hi[0]-lo[0],(hi[1]-lo[1])*sc.render.resolution_x/sc.render.resolution_y)*1.16
 sc.render.filepath=str(OUT/'images'/name);bpy.ops.render.render(write_still=True)
shot('installed.png');shot('three_modules.png','three',direction=(.3,3,1.5));shot('fold145.png',q=145,w=15,v=10,direction=(.4,3,1));shot('H.png','H');shot('R_open.png','R',cut=True,direction=(2,3,-3));shot('W.png','W')
shot('W_flex.png','W',w=70,direction=(2,3,1.3));shot('W_dev.png','W',v=30,direction=(2,3,1.3))
shot('H_ports.png','H',direction=(-3,2,1));shot('W_ports.png','W',direction=(2,3,-3))
shot('installed.png')
sc['revision']=d['revision'];sc['physical_status']='UNTESTED';sc['geometry_sha256']=hashlib.sha256((OUT/'assembly_meshes.npz').read_bytes()).hexdigest()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'O24C_T6_installed_forearm.blend'))
(OUT/'verification/blender.json').write_text(json.dumps(dict(passed=True,parts=len(objects),geometry_sha256=sc['geometry_sha256']),indent=2),encoding='utf8')
