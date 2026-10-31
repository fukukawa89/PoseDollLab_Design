"""O18 one-piece hinge housing: retain removable sensor/magnet service access."""
from base import *
from layout_fullbody import libraries

def continuous_base():
 cavity=hexagon(5.8,-8.65,-6.05)+cyl(4.65,-6.15,-5.3)+cyl(1.7,-10.6,-3.5)+cyl(2.125,-4.4,-2.0)
 s=box([-14,-9,-10.5],[14,9,-2.5])-cavity
 for x in (-9,9):s-=pose(cyl(1.7,-12,14)+hexagon(5.8,-9.1,-6.59),rot(0,-90),[x,0,-6.5])
 # Bridge only the old split, never refill distant harness reliefs.
 return s^box([-20,-.02,-20],[20,.02,0])

def access_cut():
 # Preserve the original -5.3 mm washer reaction plane. Clearance is added
 # BELOW the washer, not into the load-bearing roof.
 return box([-3.5,0,-8.7],[3.5,9.2,-6.05])+box([-4.7,0,-6.25],[4.7,9.2,-5.3])

def make():
 p,m,pr,st,prov=load_o17();original=p.copy();sources={};services=[];removed=[];changes=[]
 pp,owners,sk=libraries()['hinge']
 for state in st:
  if state['kind']!='hinge' or state['id'].startswith('ball_'):continue
  name=state['id'];key=name+'/base_service_half';frame='frame/'+state['parent'];A=m[key]['transform'];I=np.linalg.inv(A)
  assert m[key]['body']==m[frame]['body']
  old=g.move(p[frame],I)+g.move(p[key],I)
  # Join across the retained bottom web only. Do not refill the
  # old harness/neighbor reliefs higher on the split plane.
  bridge=continuous_base()
  s=((old+bridge)-access_cut()).simplify(1e-4)
  assert solid_count(s)==1 and s.status()==md.Error.NoError,(name,mesh_record(s))
  p[frame]=g.move(s,A);sources.setdefault(frame,[frame]).append(key)
  p.pop(key)
  for suffix in ('case_screw_0','case_screw_1','case_nut_0','case_nut_1'):
   k=name+'/'+suffix;removed.append(k);p.pop(k)
  insertion={}
  for part in ('M3_nut','M3_reaction_washer'):
   overlaps=[max(0.,float((s^pp[part].translate([0,t,0])).volume())) for t in np.linspace(0,16,65)]
   insertion[part]={'samples':65,'travel_mm':16,'maximum_housing_overlap_mm3':max(overlaps)}
   assert max(overlaps)<1e-4,(name,part,max(overlaps))
  # Compare the actual printed material immediately above the reaction washer.
  annulus=washer(4.5,1.7,-5.3,.02)
  bearing_before=float((old^annulus).volume())/.02;bearing_after=float((s^annulus).volume())/.02
  assert bearing_after>=bearing_before-.01,(name,bearing_before,bearing_after)
  retained=[]
  for part in ('M3_nut','M3_reaction_washer'):
   bolt=pp['shoulder_D4_L8_M3_thread6']
   retained.append({'part':part,'blocking_overlap_mm3_at_3mm_slide':float((bolt^pp[part].translate([0,3,0])).volume())})
  assert min(x['blocking_overlap_mm3_at_3mm_slide'] for x in retained)>.1
  # Nut rotational restraint comes from retained negative-Y hex faces.
  stops={str(a):float((s^pose(pp['M3_nut'],rot(2,a))).volume()) for a in (-15,15)}
  assert min(stops.values())>.01
  services.append({'module':name,'frame':frame,'assembly_stage':'Bare printed carrier, before installing rotors, shoulder screws, PCBs and external electronics',
   'insert_direction_local':[0,-1,0],'entry_side':'+Y','insertions':insertion,'washer_reaction_area_before_mm2':bearing_before,'washer_reaction_area_after_mm2':bearing_after,
   'retained_by_shoulder_screw':retained,'nut_rotation_stops_at_15deg_mm3':stops,
   'nut_slot_mm':[7,9.2,2.65],'washer_slot_mm':[9.4,9.2,.95],
   'minimum_nominal_roof_mm':2.8,'minimum_nominal_bottom_mm':1.8,'physical_strength_tested':False})
  print('HOUSING',name,'one solid; nut/washer slide clear; reaction plane retained',flush=True)
 # Make a detached hinge coupon using the SAME recipe, not a cosmetic model.
 coupon=((pp['base_sensor_half']+pp['base_service_half']+continuous_base())-access_cut()).simplify(1e-4)
 assert solid_count(coupon)==1
 np.savez_compressed(OUT/'coupon.npz',Q001=tri(coupon))
 for k,oldkeys in sources.items():
  oldshape=md.Manifold.batch_boolean([original[x] for x in oldkeys],md.OpType.Add)
  changes.append({'part':k,'anchor':k,'replaces':oldkeys,'kind':'continuous_hinge_carrier',
   'old_count':len(oldkeys),'new_count':1,'added_outside_old_mm3':max(0,float((p[k]-oldshape).volume())),
   'removed_material_mm3':max(0,float((oldshape-p[k]).volume())),**mesh_record(p[k])})
 np.savez_compressed(OUT/'changed_parts.npz',**{k:tri(g.move(p[k],np.linalg.inv(m[k]['transform']))) for k in sources})
 g.write(OUT/'changes.json',{'schema':'POSEDOLL-O18-CHANGES/1','replacements':changes,'removed_stock_parts':removed,'service_checks':services,
  'merged_housings':len(services),'new_frame_solids':len(sources),'printed_pieces_removed':sum(len(v)-1 for v in sources.values()),'stock_fasteners_removed':len(removed),
  'raw_channels':46,'semantic_dof':41,'kinematics_unchanged':True,'physical_tested':False,'manufacturing_release':False,
  'deferred_housings':['ball_l.flex','ball_r.flex'],'deferred_reason':'Merged foot carriers did not retain stable geometry through manufacture mesh round-trip; preserve O17 feet unchanged in O18.',
  'coupon':'coupon/Q001','O17_commit':'5a5ac22','O17_tag':'posedoll-o17-prototype-20260930',
  'O17_zip_sha256':g.sha(H/'bench/revO17/PoseDoll_O17_Universal_Design.zip'),'generator_sha256':g.sha(__file__)})
 print('O18',len(services),'housings,',len(sources),'new solids,',len(removed),'fasteners removed',flush=True)
 return p,m

if __name__=='__main__':make()
