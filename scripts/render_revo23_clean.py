"""Prepare with the venv; render with Blender --background --python this file."""
import sys,json
from pathlib import Path

if '--prepare' in sys.argv:
    from revo23_clean import *
    from present_revo23 import COLORS
    parts,p,cfg=load_f();F=frames(p,read(EHISTORY/'profiles/default_pose.json')['raw_deg'])
    out={};items=[]
    for key,item in parts.items():
        i=str(item['index'])
        if item['role']=='structure' and not (FROOT/(key.replace('/','__')+'.npz')).exists():
            kz=np.load(EHISTORY/'source/retained_interfaces.npz')
            z=np.load(FROOT/(key.replace('/','__')+'_skin.npz'))
            item['s']=solid(kz[key+'|v'],kz[key+'|f'])+solid(z['v'],z['f'])
        v,f=vf(item['s']);M=F[item['token']]
        out[i+'v']=v@M[:3,:3].T+M[:3,3];out[i+'f']=f
        items.append(dict(i=i,key=key,role=item['role'],color=COLORS.get(item['role'],COLORS['other'])))
    np.savez_compressed(FROOT/'render.npz',**out)
    put(FROOT/'render.json',dict(items=items))
    raise SystemExit

import bpy,numpy as np
from mathutils import Vector
root=Path(__file__).resolve().parents[1]/'Hardware/PoseDoll44/bench/revO23/design/clean_candidate'
bpy.ops.wm.read_factory_settings(use_empty=True)
d=json.loads((root/'render.json').read_text());z=np.load(root/'render.npz');points=[];mats={}
for r in d['items']:
    i=r['i'];v=z[i+'v']/1000
    if not len(v):continue
    points.append(v);me=bpy.data.meshes.new(r['key']);me.from_pydata(v.tolist(),[],z[i+'f'].tolist());me.update()
    ob=bpy.data.objects.new(r['key'],me);bpy.context.scene.collection.objects.link(ob)
    role=r['role']
    if role not in mats:
        m=bpy.data.materials.new(role);m.diffuse_color=(*r['color'],1);mats[role]=m
    ob.data.materials.append(mats[role])
v=np.concatenate(points);target=(v.max(0)+v.min(0))/2;span=np.ptp(v[:,2])
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO'
s.display.shading.color_type='MATERIAL';s.display.shading.show_shadows=True;s.display.shading.show_cavity=True
s.display.shading.cavity_type='BOTH';s.display.shading.background_type='WORLD'
s.world=bpy.data.worlds.new('Studio');s.world.color=(.8,.83,.86)
s.render.resolution_x=1000;s.render.resolution_y=1200;s.render.resolution_percentage=100
camera=bpy.data.cameras.new('Camera');ob=bpy.data.objects.new('Camera',camera)
s.collection.objects.link(ob);s.camera=ob;camera.type='ORTHO';camera.ortho_scale=span*1.14
(root/'images').mkdir(exist_ok=True)
for name,dr in [('front',(2,0,0)),('three_quarter',(1.6,-2.3,.55)),('back',(-2,0,0))]:
    ob.location=Vector(target)+Vector(dr)
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
    s.render.filepath=str(root/'images'/(name+'.png'));bpy.ops.render.render(write_still=True)
