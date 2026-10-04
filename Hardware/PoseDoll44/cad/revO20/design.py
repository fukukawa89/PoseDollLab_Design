"""O20: closed cores in free beams, vented lid and the last two hinge housings."""
from base import *
import importlib.util

def capsule(a,b,r):
 return beam(a,b,r)+md.Manifold.sphere(r,32).translate(a)+md.Manifold.sphere(r,32).translate(b)

def make():
 p,m,pr,st,prov=load_o19();original=p.copy();new={};details={};sources={};removed=[];services=[]
 rr=g.read(H/'generated/revO15/runs/o15_20260929_r1/carriers_refined/quinn_routing.json');route={r['body']:r for r in rr['frames']}
 _,mm,_,_,_=L.build('quinn',g.ASSEMBLY_POSE,geometry=False);T,A=L.fk(pr,g.ASSEMBLY_POSE);T0,_=L.fk(pr,{})
 # Joint endpoint solids and a surrounding 2 mm box are exclusion zones.
 kinds={x['id']:x['kind'] for x in st}
 for body,r in route.items():
  key='frame/'+body;outer=r['main_rod_diameter_mm']/2
  if outer<4:continue
  paths=[np.array(v) for v in r['paths_world_mm'][len(r['ports']):]]
  if body in ('thigh_l','thigh_r','calf_l','calf_r'):
   c=next(v for v in g.read(H/'generated/revO19/changes.json')['replacements'] if v['part']==key)
   M=T[body]@np.linalg.inv(T0[body]);paths=[np.array([M[:3,:3]@v+M[:3,3] for v in c['neutral_path_world_mm']])]
  if r.get('terminal_form'):
   # Hand/head terminal rods are only 7.2 mm: leave them untouched.
   if body.startswith(('foot_','ball_')):paths.append(np.array(r['terminal_form']['path_world_mm']))
  protected=[]
  for pid in r['replaces']:
   module,part=pid.split('/',1);s=g.move(L.libraries()[kinds[module]][0][part],mm[pid]['transform']);bb=np.array(s.bounding_box());protected.append(box(bb[:3]-2,bb[3:]+2))
  cuts=[];records=[]
  for path in paths:
   for segment,(aa,bb) in enumerate(zip(path,path[1:])):
    length=np.linalg.norm(bb-aa)
    if length<14:continue
    u=(bb-aa)/length;a=aa+u*(6 if segment==0 else 2);b=bb-u*(6 if segment==len(path)-2 else 2);radius=outer/2
    cut=capsule(a,b,radius);guard=capsule(a,b,radius+2)
    if float((guard-p[key]).volume())>.001:continue
    if any(float((cut^v).volume())>.0001 for v in protected):continue
    cuts.append(cut);records.append({'a_world_mm':a.tolist(),'b_world_mm':b.tolist(),'core_diameter_mm':2*radius,'nominal_outer_diameter_mm':outer*2,'minimum_guard_wall_mm':2,'capsule_axis_length_mm':float(np.linalg.norm(b-a))})
  if not cuts:continue
  cut=md.Manifold.batch_boolean(cuts,md.OpType.Add)
  # Every core is closed and strictly internal. Preserve ALL old boundary
  # triangles verbatim and append the reversed cavity surface. Avoid an
  # unnecessary Boolean retriangulation of the precision-sensitive ends.
  old_triangles=tri(p[key]);s=from_tri_exact(np.concatenate([old_triangles,tri(cut)[:,::-1,:]],axis=0))
  assert abs(float(s.volume())-float(p[key].volume()-cut.volume()))<.0001
  assert solid_count(s)==1,(key,mesh_record(s))
  p[key]=s;sources[key]=[key];details[key]={'kind':'cored_free_beams','outer_boundary_triangles_preserved':True,'cores':records,'retained_nominal_bending_torsion_section_ratio':.9375,'ratio_scope':'Uniform isotropic circular section only; not a printed part strength/deflection validation.'}
  print('CORE',body,len(cuts),'removed cm3',round((original[key].volume()-s.volume())/1000,3),flush=True)
 # The removable lid is not a kinematic carrier. Round ventilation windows
 # retain the perimeter and both regulator supports and their screw access.
 key='accessory/chest/controller_lid';entry=next(x for x in g.read(H/'generated/revO15/runs/o15_20260929_r1/equipment/quinn_search.json')['entries'] if x['kind']=='controller')
 F=np.c_[[0,1,0],[0,0,-1],[-1,0,0]];o=np.array(entry['front_center_world_mm'])-F@np.array([35,30,0]);E=g.homogeneous(F,o)
 holes=[]
 for u in (5,15,25,35,45,55,65):
  for v in (5,15,25,35,45,55):
   # Avoid existing vent slots, leaving their original four support ribs intact.
   if u>=40 and v>=30:continue
   if any(np.linalg.norm(np.array([u,v])-q)<9 for q in (np.array([12.3,34.3]),np.array([25.5,47.5]))):continue
   if np.linalg.norm(np.array([u,v])-[15,14])<7:continue
   holes.append(cyl(3.5,22.9,25.1,48).translate([u,v,0]))
 cut=g.move(md.Manifold.batch_boolean(holes,md.OpType.Add),E);p[key]-=cut
 assert solid_count(p[key])==1
 sources[key]=[key];details[key]={'kind':'vented_lid','hole_diameter_mm':7,'hole_count':len(holes),'minimum_nominal_ligament_mm':3,'buck_mounts_unchanged':True,'lid_perimeter_fasteners_unchanged':True}
 print('LID',len(holes),'removed cm3',(original[key].volume()-p[key].volume())/1000,flush=True)
 # Small open windows in the control box floor. Preserve the attachment
 # landing circles, the PCB posts, all ports and the surrounding 4 mm web.
 key='frame/chest';holes=[]
 for u in (7,21,35,49,63):
  for v in (12,26,40,54):
   if any(np.linalg.norm(np.array([u,v])-q)<10 for q in (np.array([13,30]),np.array([57,30]),np.array([11,3]),np.array([59,3]),np.array([3,57]),np.array([67,57]))):continue
   holes.append(cyl(4.5,-.05,2.05,48).translate([u,v,0]))
 cut=g.move(md.Manifold.batch_boolean(holes,md.OpType.Add),E);p[key]-=cut
 assert solid_count(p[key])==1
 sources.setdefault(key,[key]);details.setdefault(key,{'kind':'vented_box_floor'});details[key]['floor_windows']={'diameter_mm':9,'count':len(holes),'mount_landing_guard_radius_mm':10,'no_external_wiring_change':True}
 print('FLOOR',len(holes),'total chest removed cm3',(original[key].volume()-p[key].volume())/1000,flush=True)
 # Apply the established O18 side-insert hinge recipe to the two toe parents.
 spec=importlib.util.spec_from_file_location('o18_housing_recipe',H/'cad/revO18/design.py');oldrecipe=importlib.util.module_from_spec(spec);spec.loader.exec_module(oldrecipe)
 pp,own,sku=L.libraries()['hinge']
 for side in ('l','r'):
  name='ball_'+side+'.flex';key=name+'/base_service_half';frame='frame/foot_'+side;M=m[key]['transform'];I=np.linalg.inv(M)
  old=g.move(p[frame],I)+g.move(p[key],I);s=(old+oldrecipe.continuous_base())-oldrecipe.access_cut()
  assert solid_count(s)==1,(name,mesh_record(s))
  p[frame]=g.move(s,M);sources.setdefault(frame,[frame]).append(key);p.pop(key)
  for suffix in ('case_screw_0','case_screw_1','case_nut_0','case_nut_1'):
   k=name+'/'+suffix;removed.append(k);p.pop(k)
  insertion={}
  for part in ('M3_nut','M3_reaction_washer'):
   vals=[max(0.,float((s^pp[part].translate([0,t,0])).volume())) for t in np.linspace(0,16,65)]
   insertion[part]=max(vals);assert max(vals)<.0001,(name,part,max(vals))
  annulus=washer(4.5,1.7,-5.3,.02);before=float((old^annulus).volume())/.02;after=float((s^annulus).volume())/.02;assert after>=before-.01
  stops={str(a):float((s^pose(pp['M3_nut'],rot(2,a))).volume()) for a in (-15,15)};assert min(stops.values())>.01
  retained={part:float((pp['shoulder_D4_L8_M3_thread6']^pp[part].translate([0,3,0])).volume()) for part in ('M3_nut','M3_reaction_washer')};assert min(retained.values())>.1
  services.append({'module':name,'frame':frame,'insert_from':'+Y toward -Y before fitting rotor/electronics','sampled_slide_mm':16,'samples':65,'max_insert_overlap_mm3':insertion,'reaction_area_before_mm2':before,'reaction_area_after_mm2':after,'rotation_stops_15deg_mm3':stops,'retained_by_shoulder_screw_at_3mm_slide_mm3':retained})
  details.setdefault(frame,{'kind':'one_piece_toe_housing'});details[frame]['merged_toe_housing']=True
  print('MERGE',name,mesh_record(s),flush=True)
 rows=[]
 for k,source in sources.items():
  old=md.Manifold.batch_boolean([original[x] for x in source],md.OpType.Add);s=p[k];local=g.move(s,np.linalg.inv(m[k]['transform']));new[k]=local
  rows.append({'part':k,'body':m[k]['body'],'anchor':k,'replaces':source,**details[k],**mesh_record(local),'old_volume_sum_mm3':sum(original[x].volume() for x in source),'removed_material_mm3':max(0.,float((old-s).volume())),'added_outside_old_union_mm3':max(0.,float((s-old).volume()))})
 np.savez_compressed(OUT/'changed_parts.npz',**{k:tri(v) for k,v in new.items()})
 g.write(OUT/'changes.json',{'schema':'POSEDOLL-O20-CHANGES/1','replacements':rows,'removed_stock_parts':removed,'service_checks':services,'raw_channels':46,'semantic_dof':41,'kinematics_unchanged':True,'printed_pieces':186,'printed_on_doll':185,'assembly_fixture_pieces':1,'stock_fasteners_removed':len(removed),'extra_friction_parts':0,'hip_offset_per_side_mm':16,'hip_layout_status':'ACCEPTED_BY_USER_2026-09-30','nonadjacent_collision_policy':'Pose-avoidable contacts are recorded but not a design rejection. Adjacent moving mechanisms remain required to clear.','o11_fit_and_adjustable_friction':'USER_REPORTED_PASS_2026-09-30','baseline_commit':'98c084a','baseline_tag':'posedoll-o19-leg-alignment-20260930','O19_zip_sha256':g.sha(H/'bench/revO19/PoseDoll_O19_Universal_Design.zip'),'physical_tested':False,'manufacturing_release':False})
 print('CHANGED',len(rows),'TOTAL PRINT VOL REDUCTION',sum(v.volume() for k,v in original.items() if m[k]['sku'] is None)-sum(v.volume() for k,v in p.items() if m[k]['sku'] is None),flush=True)
if __name__=='__main__':make()
