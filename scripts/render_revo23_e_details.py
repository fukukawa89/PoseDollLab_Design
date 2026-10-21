import bpy,json,sys,numpy as np
from pathlib import Path
from mathutils import Vector
B=Path(__file__).resolve().parents[1]/'Hardware/PoseDoll44/bench/revO23/design/reinforced_candidate'
mode=sys.argv[sys.argv.index('--')+1]
bpy.ops.wm.read_factory_settings(use_empty=True)
d=json.loads((B/(mode+'_render.json')).read_text());z=np.load(B/(mode+'_render.npz'))
points=[]
for r in d['items']:
    i=r['i'];v=z[i+'v']/1000;points.append(v);me=bpy.data.meshes.new(r['key'])
    me.from_pydata(v.tolist(),[],z[i+'f'].tolist());me.update()
    ob=bpy.data.objects.new(r['key'],me);bpy.context.scene.collection.objects.link(ob)
    m=bpy.data.materials.new(r['key']);m.diffuse_color=(*r['color'],1);ob.data.materials.append(m)
v=np.concatenate(points);target=(v.max(0)+v.min(0))/2;span=np.max(np.ptp(v,axis=0))
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO'
s.display.shading.color_type='MATERIAL';s.display.shading.show_shadows=True;s.display.shading.show_cavity=True
s.display.shading.cavity_type='BOTH';s.display.shading.background_type='WORLD'
s.world=bpy.data.worlds.new('Studio');s.world.color=(.8,.83,.86)
s.render.resolution_x=1200;s.render.resolution_y=1000;s.render.resolution_percentage=100
camera=bpy.data.cameras.new('Camera');ob=bpy.data.objects.new('Camera',camera)
s.collection.objects.link(ob);s.camera=ob;camera.type='ORTHO';camera.ortho_scale=span*1.35
for name,dir in [('detail',(2,-2,1)),('reverse',(-2,2,1)),('front',(2,0,0)),('top',(0,0,2))]:
    ob.location=Vector(target)+Vector(dir)
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
    s.render.filepath=str(B/(mode+'_'+name+'.png'));bpy.ops.render.render(write_still=True)
