"""Prepare C7 manufacturing candidates without modifying released F7."""
from o22f7_animation import *
from build_revo22_assembly import b
import o22f7_native as h
import build_revo22_fins_v4 as fins
import package_revo22_fins_v4 as pack
import copy
C=WORK/'structure_revision';O=C/'print_candidate'
for q in ['parts','design','guards','verification','projects']:(O/q).mkdir(parents=True,exist_ok=True)
x=Build();x.begin(x.g['steps'][3]);mount=x.mount;I=np.linalg.inv(mount);key='frame/clavicle_l.protract_frame'
d=read(F/'design/W005.json');bed=next(q for q in read(B/'print_batch/manifest.json')['rows'] if q['id']=='W005')['bed'];H=h.H
print_to_owner=np.linalg.inv(H(d['orientation']['matrix'],d['orientation']['source_translation_mm'])@H(bed['rotation'],bed['translation_mm']))
print_to_local=I@x.mats[key]@print_to_owner;local_to_print=np.linalg.inv(print_to_local)
z=np.load(C/'W005_C7.npz');parts={k:b.b.from_tri_exact(z[k]) for k in ['root','distal']};freeze=lambda s:b.b.from_tri_exact(b.g.tri(s))
old=np.load(F/'parts/W005.npz');g=np.load(F/'verification/guards/W005.npz');oldguard=h.solid(g['v'],g['f']);localguard=b.g.move(oldguard,print_to_local)
newguard=b.b.cyl(1.4,.25,2.75).translate([17,0,0])+b.b.cyl(2.35,-1.75,.75).translate([17,0,0])
transforms={};reports=[]
pid='W005B';body=freeze(b.g.move(parts['distal'],local_to_print));guard=freeze(b.g.move(localguard+newguard,local_to_print)-body)
fin=h.solid(old['fin_v'],old['fin_f']);tooth=h.solid(old['teeth_v'],old['teeth_f']);fin=freeze(fin-guard);tooth=freeze(tooth-guard)
tooth=freeze(h.union([t for t in h.material_components(tooth) if (t^body).volume()>.001 and(t^fin).volume()>.001]));fin=freeze(h.union([s for s in h.material_components(fin) if(s^tooth).volume()>.001 and s.bounding_box()[2]<1e-5]));tooth=freeze(h.union([t for t in h.material_components(tooth) if(t^fin).volume()>.001]))
assert (fin^body).volume()<1e-6
v,f=h.vf(body);fv,ff=h.vf(fin);tv,tf=h.vf(tooth);np.savez_compressed(O/f'parts/{pid}.npz',v=v,f=f,source_v=v,fin_v=fv,fin_f=ff,teeth_v=tv,teeth_f=tf)
h.save_mesh(O/f'guards/{pid}.npz',guard);transforms[pid]=local_to_print.tolist()
d=copy.deepcopy(d);d.update(id=pid,part=key,structural_revision='C7',source_mesh_preserved=False,orientation={'matrix':np.eye(3).tolist(),'source_translation_mm':[0,0,0]},local_mount_to_print=local_to_print.tolist(),support_count=len(h.material_components(fin)),support_volume_mm3=(fin+tooth).volume(),required_layer_height_mm=.2,required_initial_layer_height_mm=.2,native_pending=True);put(O/f'design/{pid}.json',d)
newguard=b.b.cyl(1.4,2.25,7.05).translate([17,0,0])+b.b.cyl(2.75,4.45,7.05).translate([17,0,0])
pid='W005A';body0=parts['root'];T=np.eye(4);T[:3,:3]=np.diag([1.,-1.,-1.]);T[2,3]=body0.bounding_box()[5];body=b.g.move(body0,T);v,f=h.vf(body);guard=freeze(b.g.move(localguard+newguard,T)-body)
fins.O=O;fins.choose=lambda pid:{'matrix':np.eye(3).tolist(),'source_translation_mm':[0,0,0]};fins.read_mesh=lambda path:(v,f);fins.protected=lambda _:guard
rep=fins.make(pid,{'source_3mf':'C7','part':'revision/clavicle_l.root'},[]);rep.update(structural_revision='C7',local_mount_to_print=T.tolist(),required_layer_height_mm=.2,required_initial_layer_height_mm=.2,native_pending=True);put(O/f'design/{pid}.json',rep);h.save_mesh(O/f'guards/{pid}.npz',guard);transforms[pid]=T.tolist()
manifest=read(F/'manifest.json');plate=copy.deepcopy(next(p for p in manifest['plates'] if p['id']=='D05'))
for it in plate['items']:
 if it['id']=='W005':it.update(id='W005B',object_name='D05-01 W005B '+key,native_internal_object_name='D05-01 W005B '+key)
 else:shutil.copy2(F/f"parts/{it['id']}.npz",O/f"parts/{it['id']}.npz")
 n=np.load(O/f"parts/{it['id']}.npz");vv=np.concatenate([n[q] for q in ['v','fin_v','teeth_v'] if len(n[q])]);placed=vv@np.array(it['rotation_matrix']).T+it['translation_mm'];it.update(bounds_mm=np.r_[placed.min(0),placed.max(0)].tolist(),local_bounds_mm=np.r_[vv.min(0),vv.max(0)].tolist())
pack.O=O;rootplate=pack.arrange([{'id':'W005A','part':'revision/clavicle_l.root','object_name':'W005A','optional_sample':False}],'D','左锁骨根部 · 装配修订件',False,15)[0];rootplate.update(profile=copy.deepcopy(plate['profile']))
for p in [plate,rootplate]:p.update(project=f"projects/{p['id']}_O22F7_PLA_assembly.3mf",native_review_passed=False)
put(O/'changed_plates.json',{'plates':[plate,rootplate],'local_mount_to_print':transforms,'candidate_sha256':sha(C/'W005_C7.npz')})
for pid in ['W005A','W005B']:
 n=np.load(O/f'parts/{pid}.npz');body,fin,tooth=[h.solid(n[v],n[f]) for v,f in [('v','f'),('fin_v','fin_f'),('teeth_v','teeth_f')]];g=np.load(O/f'guards/{pid}.npz');guard=h.solid(g['v'],g['f']);row={'id':pid,'body_components':len(h.material_components(body)),'print_components':len(h.material_components(body+fin+tooth)),'fin_body_overlap_mm3':float((fin^body).volume()),'support_in_hole_guard_mm3':float(((fin+tooth)^guard).volume()),'body_volume_mm3':body.volume(),'support_volume_mm3':(fin+tooth).volume(),'fin_components':len(h.material_components(fin))};reports.append(row);print(row,flush=True)
put(O/'geometry_review.json',reports)
