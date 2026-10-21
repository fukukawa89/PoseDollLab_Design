"""Root print-orientation trials; no permanent body edits."""
from o22f7_animation import *
from build_revo22_assembly import b
import o22f7_native as h,build_revo22_fins_v4 as fins,package_revo22_fins_v4 as pack
C=WORK/'structure_revision';O=C/'print_candidate';data=read(O/'changed_plates.json');z=np.load(C/'W005_C7.npz');body0=b.b.from_tri_exact(z['root']);oldg=np.load(F/'verification/guards/W005.npz');localguard=b.g.move(h.solid(oldg['v'],oldg['f']),np.linalg.inv(data['local_mount_to_print']['W005B']));newguard=b.b.cyl(1.4,2.25,7.05).translate([17,0,0])+b.b.cyl(2.75,4.45,7.05).translate([17,0,0])
T=np.eye(4);T[:3,:3]=np.array([[0,0,1],[0,1,0],[-1,0,0]]);temp=b.g.move(body0,T);T[2,3]=-temp.bounding_box()[2];body=b.g.move(body0,T);v,f=h.vf(body);guard=b.g.move(localguard+newguard,T)-body
fins.O=O;fins.choose=lambda pid:{'matrix':np.eye(3).tolist(),'source_translation_mm':[0,0,0]};fins.read_mesh=lambda path:(v,f);fins.protected=lambda _:guard
rep=fins.make('W005A',{'source_3mf':'C7','part':'revision/clavicle_l.root'},[]);rep.update(structural_revision='C7',local_mount_to_print=T.tolist(),required_layer_height_mm=.2,required_initial_layer_height_mm=.2,native_pending=True);put(O/'design/W005A.json',rep);h.save_mesh(O/'guards/W005A.npz',guard);data['local_mount_to_print']['W005A']=T.tolist()
pack.O=O;p=pack.arrange([{'id':'W005A','part':'revision/clavicle_l.root','object_name':'W005A','optional_sample':False}],'D','左锁骨根部 · 装配修订件',False,15)[0];p.update(profile=data['plates'][1]['profile'],project=data['plates'][1]['project'],native_review_passed=False);data['plates'][1]=p;put(O/'changed_plates.json',data);print('ROOT',rep['support_count'],rep['support_volume_mm3'],flush=True)
