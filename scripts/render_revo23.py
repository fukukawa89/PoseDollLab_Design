"""Run with a separate Blender background process; existing GUI scenes untouched."""
import bpy,json,sys,hashlib,argparse
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix

B=Path(__file__).resolve().parents[1]/'Hardware/PoseDoll44/bench/revO23'
parser=argparse.ArgumentParser();parser.add_argument('--trial',action='store_true')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
bpy.ops.wm.read_factory_settings(use_empty=True)
data=json.loads((B/('preview/trial_scene.json' if args.trial else 'preview/render_scene.json')).read_text('utf8'))
mesh=np.load(B/('preview/trial_meshes.npz' if args.trial else 'preview/render_meshes.npz'))
image_dir=B/'design/continuous_candidate/images' if args.trial else B/'images'
materials={};groups={};bounds=[]
for p in data['items']:
    group=p['role'];i=str(p['i']);v=mesh[i+'v'];f=mesh[i+'f'];M=np.array(p['matrix']).reshape(4,4)
    v=(v@M[:3,:3].T+M[:3,3])/1000
    color=p['color'];bounds.append(v)
    if group not in groups:
        collection=bpy.data.collections.new(group);bpy.context.scene.collection.children.link(collection);groups[group]=collection
        mat=bpy.data.materials.new(group);mat.diffuse_color=(*color,1);mat.use_nodes=True
        bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=.52 if group=='structure' else .7
        materials[group]=mat
    me=bpy.data.meshes.new(p['key']);me.from_pydata(v.tolist(),[],f.tolist());me.update()
    ob=bpy.data.objects.new(p['key'],me);groups[group].objects.link(ob);ob.data.materials.append(materials[group])
    ob['assembly_key']=p['key'];ob['manufacturing_release']=False
    # Do not smooth manufactured corners; preserve the actual tessellation.
v=np.concatenate(bounds);lo=v.min(0);hi=v.max(0);center=(lo+hi)/2;span=hi[2]-lo[2]
sc=bpy.context.scene;sc.unit_settings.system='METRIC';sc.render.engine='BLENDER_WORKBENCH'
provenance=json.loads((B/'preview/provenance.json').read_text('utf8'))
if args.trial:
    provenance['geometry_sha256']=hashlib.sha256((B/'preview/trial_meshes.npz').read_bytes()).hexdigest()
    provenance['review']['revision']='O23D mixed assembly trial, not delivered'
sc['source_geometry_sha256']=provenance['geometry_sha256'];sc['assembly_revision']=provenance['review']['revision']
sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_shadows=True
sc.display.shading.show_cavity=True;sc.display.shading.cavity_type='BOTH';sc.display.shading.background_type='WORLD'
sc.render.resolution_x=1000;sc.render.resolution_y=1200;sc.render.resolution_percentage=100
sc.world=bpy.data.worlds.new('Studio');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.82,.85,.88,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.6
for name,loc,power,size in [('Key',(1.5,-1.0,1.5),140,1.5),('Fill',(.7,1.3,1),75,1.2),('Rim',(-1,0,1.2),100,1.0)]:
    light=bpy.data.lights.new(name,'AREA');light.energy=power;light.shape='DISK';light.size=size
    ob=bpy.data.objects.new(name,light);sc.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector(center)-ob.location).to_track_quat('-Z','Y').to_euler()
cam=bpy.data.cameras.new('Camera');co=bpy.data.objects.new('Camera',cam);sc.collection.objects.link(co);sc.camera=co
cam.type='ORTHO';cam.ortho_scale=span*1.14;cam.clip_end=100;sc.view_settings.view_transform='AgX'
sc.render.image_settings.file_format='PNG';image_dir.mkdir(exist_ok=True,parents=True)
for label,direction in [('three_quarter',(1.6,-2.3,.55)),('front',(2,0,0)),('side',(0,-2,0)),('back',(-2,0,0))]:
    co.location=Vector(center)+Vector(direction);co.rotation_euler=(Vector(center)-co.location).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=str(image_dir/f'{label}.png');bpy.ops.render.render(write_still=True)
if 'o22/controller_housing' in bpy.data.objects:
    selected=[bpy.data.objects[k]for k in('frame/chest','o22/controller_housing','o22/controller_lid')]
    pts=np.array([list(ob.matrix_world@Vector(v))for ob in selected for v in ob.bound_box])
    target=Vector((pts.min(0)+pts.max(0))/2);cam.ortho_scale=.27
    co.location=target+Vector((-2,-2,.8));co.rotation_euler=(target-co.location).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=str(image_dir/'backpack_detail.png');bpy.ops.render.render(write_still=True)
cam.ortho_scale=span*1.14
co.location=Vector(center)+Vector((1.6,-2.3,.55));co.rotation_euler=(Vector(center)-co.location).to_track_quat('-Z','Y').to_euler()
if not args.trial:
    tag=provenance['review']['revision'].split('-')[0]
    bpy.ops.wm.save_as_mainfile(filepath=str(B/(tag+'_assembly.blend')))
(image_dir/'provenance.json').write_text(json.dumps(dict(geometry_sha256=provenance['geometry_sha256'],revision=provenance['review']['revision'],
    images={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in image_dir.glob('*.png')}),indent=2)+'\n',encoding='utf8')
