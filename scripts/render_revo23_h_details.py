"""Actual O23G CAD, shown without diagnostic coplanar colour overlays."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'Hardware/PoseDoll44/bench/revO23/design/end_face_candidate'
if '--prepare' in sys.argv:
    from revo23_endfaces import *
    parts,p,cfg=load_h();N=frames(p,p['neutral_raw_deg']);meshes={};scenes=[];index=0
    selected=sys.argv[sys.argv.index('--prepare')+1:] or ['frame/thigh_l','frame/calf_l','frame/forearm_l','frame/forearm_r','frame/pelvis']
    if selected==['all']:selected=[k for k,v in parts.items() if v['role']=='structure']
    def add(name,items,direction):
        global index
        rows=[]
        for title,s,color in items:
            v,f=vf(s)
            if not len(v):continue
            i=str(index);index+=1;meshes[i+'v']=v;meshes[i+'f']=f
            rows.append(dict(id=i,label=title,color=color))
        scenes.append(dict(name=name,items=rows,direction=direction))
    beige=[.78,.77,.68];dark=[.19,.24,.26]
    for key in selected:
        a=parts[key];M=N[a['token']];s=move(a['s'],M);stem=key.replace('/','__')
        direction=(-2,0,.15) if key in ('frame/pelvis','frame/waist') else (-.7,-1 if not key.endswith('_r') else 1,.6)
        add(stem+'_actual',[(key,s,beige)],direction)
        if key.startswith('frame/forearm_'):
            keep=move(native_keep(key),M);skin=move(clean_skin(key),M)
            add(stem+'_material_diagnosis',[(key+' native mounts',s^keep,[.25,.4,.75]),(key+' wall',skin-keep,[.1,.6,.55]),(key+' new connections and seats',s-keep-skin,[.9,.45,.14])],direction)
            add(stem+'_native_only',[(key+' native mounts',keep,beige)],direction)
        if key.startswith('frame/thigh_'):
            side=key[-1];clip=box([-100,-100,300],[100,100,380]);objects=[]
            for k,b in parts.items():
                if k==key or k.startswith('thigh_'+side+'/'):
                    objects.append((k,move(b['s'],N[b['token']])^clip,beige if k==key else dark))
            add(stem+'_hip_front',objects,(1.6,-1 if side=='l' else 1,1.1))
            add(stem+'_hip_back',objects,(-1.5,1 if side=='l' else -1,.9))
    np.savez_compressed(ROOT/'detail_meshes.npz',**meshes);put(ROOT/'detail_scenes.json',dict(scenes=scenes,geometry_sha256=sha(HROOT/'assembly.npz')))
    raise SystemExit
import bpy,numpy as np
from mathutils import Vector
d=json.loads((ROOT/'detail_scenes.json').read_text('utf8'));z=np.load(ROOT/'detail_meshes.npz')
(ROOT/'images').mkdir(exist_ok=True)
for scene in d['scenes']:
    bpy.ops.wm.read_factory_settings(use_empty=True);allv=[]
    for item in scene['items']:
        v=z[item['id']+'v']/1000;f=z[item['id']+'f'];allv.append(v)
        me=bpy.data.meshes.new(item['label']);me.from_pydata(v.tolist(),[],f.tolist());me.update()
        ob=bpy.data.objects.new(item['label'],me);bpy.context.collection.objects.link(ob)
        mat=bpy.data.materials.new(item['label']);mat.diffuse_color=(*item['color'],1);ob.data.materials.append(mat)
    v=np.concatenate(allv);center=(v.min(0)+v.max(0))/2;span=float(max(np.ptp(v,axis=0)))
    sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO'
    sc.display.shading.color_type='MATERIAL';sc.display.shading.show_shadows=True
    sc.display.shading.show_cavity=True;sc.display.shading.cavity_type='BOTH'
    sc.display.shading.background_type='WORLD';sc.world=bpy.data.worlds.new('Studio');sc.world.color=(.82,.85,.87)
    sc.render.resolution_x=1100;sc.render.resolution_y=1000;sc.render.resolution_percentage=100
    ca=bpy.data.cameras.new('Camera');co=bpy.data.objects.new('Camera',ca);sc.collection.objects.link(co);sc.camera=co
    ca.type='ORTHO';ca.ortho_scale=span*1.3;co.location=Vector(center)+Vector(scene['direction'])
    co.rotation_euler=(Vector(center)-co.location).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=str(ROOT/'images'/(scene['name']+'.png'));bpy.ops.render.render(write_still=True)
