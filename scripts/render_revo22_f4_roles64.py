from pathlib import Path
import bpy,numpy as np,json,sys
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4';args=sys.argv[sys.argv.index('--')+1:];pid,label=args[:2];p=O/'candidates'/pid/label;n=np.load(p/'parts'/f'{pid}.npz');it=json.loads((p/'verification/plate_manifest.json').read_text())['items'][0];M=np.array(it['rotation_matrix']);t=np.array(it['translation_mm']);bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=1400;scene.render.resolution_y=1200;scene.render.resolution_percentage=100;sh=scene.display.shading;sh.light='STUDIO';sh.color_type='OBJECT';sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH';sh.background_type='WORLD';scene.world.color=(.92,.94,.96);scene.view_settings.view_transform='Standard';scene.render.image_settings.file_format='PNG'
for role,v,f,c in [('body','v','f',(.24,.54,.78,1)),('fins','fin_v','fin_f',(1,.48,.10,1)),('teeth','teeth_v','teeth_f',(1,.85,.12,1))]:
 mesh=bpy.data.meshes.new(role);mesh.from_pydata(n[v].tolist(),[],n[f].tolist());ob=bpy.data.objects.new(role,mesh);bpy.context.collection.objects.link(ob);ob.color=c
full={'critical_external_runs':[],'external_islands':[]};marks=[]
for q in full['critical_external_runs']+full['external_islands']:
 b=q['bounds_mm'];pt=(np.array([(b[0]+b[2])/2,(b[1]+b[3])/2,q['z_mm']])-t)@M
 if any(np.linalg.norm(pt-m)<2 for m in marks):continue
 marks.append(pt);bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,radius=.8,location=pt.tolist());bpy.context.object.color=(.9,.05,.18,1)
v=n['v'];center=Vector(((v.min(0)+v.max(0))/2).tolist());camdata=bpy.data.cameras.new('camera');cam=bpy.data.objects.new('camera',camdata);bpy.context.collection.objects.link(cam);scene.camera=cam;camdata.type='ORTHO';camdata.ortho_scale=float(np.max(np.ptp(np.r_[n['v'],n['fin_v']],0)))*1.4
for name,delta in [('front',(1,-1,.6)),('back',(-1,1,.6)),('left',(-1,-1,.5))]:
 cam.location=center+Vector(delta)*200;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(p/'verification'/('render_'+name+'.png'));bpy.ops.render.render(write_still=True)
