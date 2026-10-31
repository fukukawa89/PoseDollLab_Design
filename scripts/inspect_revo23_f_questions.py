"""Read-only geometry diagnosis for the user's O23F connector/skin questions."""
import sys,json
from pathlib import Path

OUT=Path(__file__).resolve().parents[1]/'Hardware/PoseDoll44/bench/revO23/verification/user_review_F'

if '--prepare' in sys.argv:
    from revo23_clean import *
    from present_revo23 import load_current
    parts=load_current();p=read(B/'profiles/device_profile.json')
    poses={'A':read(B/'profiles/default_pose.json')['raw_deg'],'N':p['neutral_raw_deg']}
    keys=['frame/thigh_l','frame/thigh_r','frame/forearm_l','frame/forearm_r','frame/pelvis']
    OUT.mkdir(parents=True,exist_ok=True)
    report={'geometry_sha256':sha(B/'assembly.npz'),'contacts':[],'symmetry':{}}
    for label,q in poses.items():
        F=frames(p,q)
        for key in keys:
            a=parts[key];bb=np.array(a['s'].bounding_box());I=np.linalg.inv(F[a['token']]);hits=[];maximum=0
            for other,b in parts.items():
                if other==key:continue
                M=I@F[b['token']];s=move(b['s'],M);ob=np.array(s.bounding_box())
                if np.any(np.minimum(bb[3:],ob[3:])-np.maximum(bb[:3],ob[:3])<=0):continue
                volume=max(0.,(a['s']^s).volume());maximum=max(maximum,volume)
                if volume>1e-5:hits.append({'other':other,'overlap_mm3':volume})
            row={'pose':label,'part':key,'maximum_overlap_mm3':maximum,'hits':hits}
            report['contacts'].append(row);print('CONTACT',json.dumps(row),flush=True)
    F=frames(p,p['neutral_raw_deg']);A=frames(p,poses['A'])
    skinz=np.load(FROOT/'frame__pelvis_skin.npz');N=F[parts['frame/pelvis']['token']]
    world=skinz['v']@N[:3,:3].T+N[:3,3];mirror=world*np.array([1,-1,1])
    report['symmetry']['pelvis_skin_max_mirrored_vertex_distance_mm']=float(cKDTree(world).query(mirror)[0].max())
    report['symmetry']['pelvis_A_vs_N_transform_max_difference']=float(np.max(abs(A[parts['frame/pelvis']['token']]-N)))
    v,f=vf(parts['frame/pelvis']['s']);world=v@N[:3,:3].T+N[:3,3]
    mesh=trimesh.Trimesh(world,f,process=False)
    sample=world[np.linspace(0,len(world)-1,min(4000,len(world)),dtype=int)]*np.array([1,-1,1])
    _,distance,_=trimesh.proximity.closest_point(mesh,sample)
    report['symmetry']['pelvis_complete_sampled_max_mirror_surface_distance_mm']=float(max(distance))
    report['symmetry']['pelvis_complete_sampled_p95_mirror_surface_distance_mm']=float(np.percentile(distance,95))
    report['symmetry']['sampled_vertex_count']=len(sample)
    print('SYMMETRY',report['symmetry'],flush=True)
    put(OUT/'diagnosis.json',report)
    kz=np.load(EHISTORY/'source/retained_interfaces.npz')
    scenes=[];meshes={};index=0
    def add_scene(name,objects,direction):
        global index
        entries=[]
        for title,s,M,color in objects:
            v,f=vf(s)
            if not len(v):continue
            k=str(index);index+=1;meshes[k+'v']=v@M[:3,:3].T+M[:3,3];meshes[k+'f']=f
            entries.append(dict(id=k,label=title,color=color))
        scenes.append(dict(name=name,items=entries,direction=direction))
    beige=[.78,.77,.68];teal=[.13,.57,.58];orange=[.89,.43,.17];blue=[.28,.43,.75];dark=[.19,.24,.26]
    for key in ('frame/pelvis','frame/forearm_l','frame/forearm_r'):
        a=parts[key];M=F[a['token']];stem=key.replace('/','__')
        z=np.load(FROOT/(stem+'_skin.npz'));skin=solid(z['v'],z['f'])
        keep=solid(kz[key+'|v'],kz[key+'|f']);remainder=a['s']-skin-keep
        direction=(-2,0,0) if key=='frame/pelvis' else (-.7,-1 if key.endswith('_l') else 1,.6)
        add_scene(stem+'_classified', [('exterior skin',skin,M,teal),('retained mounts',keep,M,blue),('connections bosses and wire fixtures',remainder,M,orange)],direction)
        add_scene(stem+'_actual',[(key,a['s'],M,beige)],direction)
        if key=='frame/pelvis':
            add_scene('pelvis_skin_only_back',[('skin',skin,M,teal)],direction)
    for side in ('l','r'):
        key='frame/thigh_'+side;a=parts[key];M=A[a['token']]
        clip=move(box([-90,-90,-65],[90,90,35]),M);items=[]
        for k,b in parts.items():
            if not (k==key or k=='frame/pelvis' or k.startswith('thigh_'+side+'/')):continue
            s=move(b['s'],A[b['token']])^clip
            items.append((k,s,np.eye(4),beige if k==key else dark))
        add_scene('thigh_'+side+'_hip_connection',items,(1.6,-1 if side=='l' else 1,1.1))
        add_scene('thigh_'+side+'_hip_connection_back',items,(-1.5,1 if side=='l' else -1,.9))
    np.savez_compressed(OUT/'detail_meshes.npz',**meshes)
    put(OUT/'detail_scenes.json',dict(geometry_sha256=report['geometry_sha256'],scenes=scenes))
    print('PREPARED',len(scenes),'scenes',flush=True)
    raise SystemExit

import bpy,numpy as np
from mathutils import Vector
d=json.loads((OUT/'detail_scenes.json').read_text('utf8'));z=np.load(OUT/'detail_meshes.npz')
for scene in d['scenes']:
    bpy.ops.wm.read_factory_settings(use_empty=True);allv=[]
    for item in scene['items']:
        v=z[item['id']+'v']/1000;f=z[item['id']+'f'];allv.append(v)
        me=bpy.data.meshes.new(item['label']);me.from_pydata(v.tolist(),[],f.tolist());me.update()
        ob=bpy.data.objects.new(item['label'],me);bpy.context.collection.objects.link(ob)
        mat=bpy.data.materials.new(item['label']);mat.diffuse_color=(*item['color'],1);ob.data.materials.append(mat)
    v=np.concatenate(allv);center=(v.min(0)+v.max(0))/2;span=float(max(np.ptp(v,axis=0)))
    sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH'
    sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL'
    sc.display.shading.show_shadows=True;sc.display.shading.show_cavity=True;sc.display.shading.cavity_type='BOTH'
    sc.display.shading.background_type='WORLD';sc.world=bpy.data.worlds.new('Studio');sc.world.color=(.82,.85,.87)
    sc.render.resolution_x=1100;sc.render.resolution_y=1000;sc.render.resolution_percentage=100
    ca=bpy.data.cameras.new('Camera');co=bpy.data.objects.new('Camera',ca);sc.collection.objects.link(co);sc.camera=co
    ca.type='ORTHO';ca.ortho_scale=span*1.3
    co.location=Vector(center)+Vector(scene['direction']);co.rotation_euler=(Vector(center)-co.location).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=str(OUT/(scene['name']+'.png'));bpy.ops.render.render(write_still=True)
