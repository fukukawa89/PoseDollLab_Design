"""O6 front-loading cup and shortened output; physical qualification remains open."""
from pathlib import Path
import argparse, hashlib, json, itertools, math, sys
import cadquery as cq
R=Path(__file__).resolve().parents[4];H=R/'Hardware/PoseDoll44'
OLD=H/'generated/revO3/runs/o3_20260924_r3/joint'
sys.path.insert(0,str(H/'cad/revO3'))
from compact_joint import cyl,ring,box,hole_x,bounds
from thread_geometry import thread_sweep,checked,RECEIPTS,overlap_volume
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def tapered_tail(z0,z1):
 r=lambda z:2.85+.05*(z+18)
 f=lambda z:2.35+.05*(z+18)
 s=cq.Solid.makeCone(r(z0),r(z1),z1-z0,cq.Vector(0,0,z0))
 for sign in (-1,1):
  cut=cq.Workplane('XZ').polyline([(sign*f(z0),z0),(sign*8,z0),(sign*8,z1),(sign*f(z1),z1)]).close().extrude(12,both=True).val()
  s=s.cut(cut)
 return s
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--compact-bearing',action='store_true');a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 manifest=json.loads((OLD/'manifest.json').read_text());consumed={}
 for p in (OLD/'manifest.json',H/'cad/revO3/compact_joint.py'):consumed[p.relative_to(R).as_posix()]=sha(p)
 parts={};materials={};owners={};notes={}
 def add(name,s,material='al6061',owner='parent',note=''):
  assert s.isValid() and len(s.Solids())==1 and s.Volume()>0,(name,s.isValid(),len(s.Solids()))
  parts[name]=s;materials[name]=material;owners[name]=owner;notes[name]=note;return s
 replaced={'one_piece_brake_cup','measurement_shaft','front_lining_backing','rear_lining_backing','keyed_pressure_plate'}|{'cup_mount_'+str(i) for i in range(4)}
 for row in manifest['parts']:
  p=OLD/row['step_file'];assert sha(p)==row['step_sha256'];consumed[p.relative_to(R).as_posix()]=sha(p)
  if row['part_id'] not in replaced:add(row['part_id'],cq.importers.importStep(str(p)).val(),row['material'],row['owner'],row.get('note',''))
 if a.compact_bearing:
  # Preserve the original 6 mm journals and both thrust locations. Remove only
  # the 5.8 mm spacer between front thrust land and front bearing; relocate
  # the split-cartridge clamp bosses and explicitly clear the internal bores.
  for name in list(parts):
   if name.startswith('housing_'):
    side=-1 if name.endswith('L') else 1;old=parts[name]
    body=old.intersect(box(100,100,100,(0,0,-40))).fuse(old.intersect(box(100,100,100,(0,0,65.8))).translate((0,0,-5.8)))
    for y in (-6,6):
     body=body.fuse(box(15,4,3,(0,y,6.5))).cut(hole_x(1.10,-8,.1,y,6.5)).cut(hole_x(.83,-.1,8,y,6.5))
    body=body.cut(cyl(4.50,5.0,5.2)).cut(cyl(5.1,5.2,7)).cut(cyl(5.1,7.6,8.01))
    body=body.intersect(box(100,100,150,(side*50,0,0))).clean()
    assert body.isValid() and len(body.Solids())==1,name
    parts[name]=body;notes[name]+=' O6 trial: 8.2 mm support span, clamp relocated to z=6.5; bore fit/strength not qualified.'
   elif name.startswith(('front_bush','sensor_pcba','pcb_edge_clamp','pcb_clamp_screw','diametric_magnet','magnet_keeper','keeper_screw')):
    parts[name]=parts[name].translate((0,0,-5.8))
   elif name.startswith('bearing_clamp_'):parts[name]=parts[name].translate((0,0,-6))
 print('Building continuous rear thread and removable steel front',flush=True)
 cup=ring(15.6,12.35,-14.8,0).cut(cyl(13.70,-14.81,-6.10))
 female=thread_sweep([(13.68,-.24),(14.03,-(.24-.35/math.sqrt(3))),(14.03,.24-.35/math.sqrt(3)),(13.68,.24)]).translate((0,0,-1.4))
 cup=checked(cup,female,'cut','L6 female thread').clean()
 # Front-loading pockets stop before the female helix. The separate front
 # endplate is installed after the floating carrier, then retained by four bolts.
 pockets=[]
 for x in (-12.9,12.9):
  p=box(2.6,4.16,5.5,(x,0,-2.75));cup=cup.cut(p);pockets.append(p)
 for x in (-13.275,13.275):
  for sign in (-1,1):cup=cup.cut(box(1.85,1.10,.07,(x,sign*2.55,-.035)))
 mounts=[(sx*12.3,sy*7.1) for sx in (-1,1) for sy in (-1,1)]
 for x,y in mounts:cup=cup.cut(cyl(.83,-3.6,.01).translate((x,y,0)))
 cup=cup.fuse(box(4,4,4.2,(16.7,0,-10.9))).cut(hole_x(.83,13,19,0,-10.9)).clean()
 add('brake_cup_front_loading',cup)
 # Rebuild inherited cap with the independently checked helical solid.
 cap_thread=thread_sweep([(13.60,-(.03125+.34/math.sqrt(3))),(13.94,-.03125),(13.94,.03125),(13.60,.03125+.34/math.sqrt(3))],z0=-11.8,height=3.5).rotate((0,0,0),(0,0,1),(-11.8+14)/.75*360)
 cap=checked(cyl(13.63,-12.05,-8.05),cap_thread,'fuse','L6 male thread').cut(cyl(3.4,-12.1,-8.0)).cut(ring(6.55,6.04,-9.7,-8.0))
 pockets_cap=ring(12.2,6.8,-12.06,-9.65).cut(box(30,5,4,(0,0,-10.8))).cut(box(5,30,4,(0,0,-10.8)))
 cap=cap.cut(pockets_cap)
 for x in (-10.5,10.5):cap=cap.cut(cyl(.85,-12.1,-10.55).translate((x,0,0)))
 for i in range(12):cap=cap.cut(box(1.0,1.1,4.2,(13.9,0,-10.05)).rotate((0,0,0),(0,0,1),i*30))
 add('threaded_adjuster_cap',cap.translate((0,0,-1.4)),'al6061',note='O6 checked pipe thread replaces invalid inherited ruled-face Boolean; manufacturing tolerance class unqualified.')
 
 front=ring(17,4.3,0,1.5).fuse(ring(12.1,4.3,-.8,0)).fuse(ring(7.49,4.50,1.5,2.0))
 for x,y in mounts:front=front.cut(cyl(1.10,-.01,1.51).translate((x,y,0)))
 add('integral_steel_front_backing',front,'steel',note='One part: endplate and fixed backing. Four M2 bolts close the preload path. Lining bond remains unqualified.')
 for i,(x,y) in enumerate(mounts):
  add('cup_mount_'+str(i),cyl(.8,-3,3).fuse(cyl(1.8,3,5)).translate((x,y,0)),'steel',note='M2 x 6 root-core representation; 3 mm cup engagement, strength and preload pending.')
 # Integrating the rear steel backing and pressure plate removes one loose
 # interface. Retain the 12.16 mm spring-guide bore for existing 12 mm springs.
 rear=ring(12.1,4.3,-6.1,-3.5).fuse(ring(6.40,6.08,-10.7,-6.1))
 for x in (-12.9,12.9):rear=rear.fuse(box(2.4,4,1.8,(x,0,-4.4)))
 add('integral_rear_sliding_carrier',rear,'steel',note='Front-loaded sliding carrier; fitted captured guide shims, loaded sliding unqualified.')
 for x in (-12.9,12.9):
  for sign in (-1,1):
   shim=box(1.75,.06,5.44,(math.copysign(13.275,x),sign*2.05,-2.78)).fuse(box(1.75,1.04,.06,(math.copysign(13.275,x),sign*2.54,-.03)))
   add(f'guide_shim_{x}_{sign}',shim,'steel',note='0.06 nominal; select shim after actual measurement for 0.02-0.04 mm total tangential clearance. Captured by front plate and pocket floor; burr/flatness and loaded sliding test required.')
 oldshaft=cq.importers.importStep(str(OLD/'measurement_shaft.step')).val()
 if a.compact_bearing:
  oldshaft=oldshaft.intersect(box(100,100,100,(0,0,-40))).fuse(oldshaft.intersect(box(100,100,100,(0,0,65.8))).translate((0,0,-5.8))).clean()
 shaft=oldshaft.cut(box(20,20,20,(0,0,-25))).fuse(tapered_tail(-18,-14.99)).clean().cut(cyl(1.025,-18.01,-12.2))
 add('short_taper_measurement_shaft',shaft,'al7075','child','M2.5 x 0.45 blind tap represented by root bore; 2.86 degree double-D taper, not a resolved production thread.')
 hub=cyl(10,-18.4,-15.4).cut(tapered_tail(-18.41,-15.39))
 holes=[(6,0),(-6,0),(0,6),(0,-6)]
 for x,y in holes:hub=hub.cut(cyl(.83,-18.41,-15.39).translate((x,y,0)))
 add('taper_output_hub',hub,'al7075','child','Double-D positive torque path; M2.5 seats taper. Tolerance take-up/contact and preload need qualification.')
 add('output_retention_washer',ring(3.5,1.35,-18.9,-18.4),'steel','child','Custom OD7/ID2.7/t0.5 washer')
 screw=cyl(1.01,-18.9,-12.9).fuse(cyl(2.25,-21.4,-18.9))
 socket=cq.Workplane('XY').polygon(6,4/math.sqrt(3)).extrude(1.2).val().translate((0,0,-21.4))
 add('output_retention_screw',screw.cut(socket),'steel','child','M2.5 x 6 ISO4762 envelope; 5.1 mm nominal thread engagement and 0.7 mm tip clearance. Root-core model.')
 mate=ring(10,3.6,-21.4,-18.4)
 for x,y in holes:mate=mate.cut(cyl(1.10,-21.41,-18.39).translate((x,y,0)))
 add('output_yoke_interface',mate,'al7075','child','Real annular flange with four M2 interfaces; radial load-bearing links generated separately.')
 for i,(x,y) in enumerate(holes):
  add('output_yoke_screw_'+str(i),cyl(.80,-21.4,-15.4).fuse(cyl(1.8,-23.4,-21.4)).translate((x,y,0)),'steel','child','M2 x 6 envelope, 3 mm hub engagement; preload/strength and detailed threads pending.')
 density={p['material']:p['density_g_mm3'] for p in manifest['parts']};rows=[]
 for name,s in parts.items():
  cq.exporters.export(s,str(a.out/(name+'.step')))
  rows.append(dict(part_id=name,step_file=name+'.step',step_sha256=sha(a.out/(name+'.step')),owner=owners[name],material=materials[name],volume_mm3=s.Volume(),local_com_mm=list(s.Center().toTuple()),mass_g=s.Volume()*density[materials[name]],bounds_mm=bounds(s),note=notes[name]))
 print('Checking nominal part pairs',flush=True);hits=[]
 for n,m in itertools.combinations(parts,2):
  b,c=bounds(parts[n]),bounds(parts[m])
  if all(min(b[i+3],c[i+3])-max(b[i],c[i])>1e-5 for i in range(3)):
   v=overlap_volume(parts[n],parts[m])
   if v>1e-5:hits.append(dict(a=n,b=m,volume_mm3=v))
 moving=parts['integral_rear_sliding_carrier'];insertion=[]
 for shift in (0,.1,.5,1,2,4,6,10,15):
  insertion.append(dict(shift_z_mm=shift,cup_intersection_mm3=moving.translate((0,0,shift)).intersect(cup).Volume()))
 slide=[];obstacles=[cup,*[s for n,s in parts.items() if n.startswith('guide_shim_')]]
 for dz in (0,.1,.3,.6,.9):
  slide.append(dict(wear_takeup_shift_mm=dz,guide_intersection_mm3=sum(moving.translate((0,0,dz)).intersect(s).Volume() for s in obstacles)))
 section_boxes=[]
 for z0,z1 in [(-24,-15),(-15,0),(0,5),(5,20),(20,32)]:
  cutbox=box(100,100,z1-z0,(0,0,(z0+z1)/2));pieces=[]
  for shape in parts.values():
   if bounds(shape)[2]>=z1 or bounds(shape)[5]<=z0:continue
   piece=shape.intersect(cutbox)
   if piece.Volume()>1e-6:pieces.append(piece)
  section_boxes.append(bounds(cq.Compound.makeCompound(pieces)))
 compound=cq.Compound.makeCompound(list(parts.values()));cq.exporters.export(compound,str(a.out/'joint_O6.step'))
 configpath=H/'mechanical_manifest/lifecycle_states_revO3.json';consumed[configpath.relative_to(R).as_posix()]=sha(configpath);life=json.loads(configpath.read_text())
 geometry={'spring_ro_mm':6,'spring_ri_mm':3.1,'spring_t_mm':.5,'spring_hfree_mm':.85,'spring_hwork_mm':.5875,'spring_stack_top_z_mm':-6.6,'front_lining_z_mm':[-1.4,-.8],'rear_lining_z_mm':[-3.5,-2.9],'lining_ro_mm':12,'lining_ri_mm':4.2,'thread_pitch_mm':.75,'nominal_guide_gap_mm':.04,'wear_pairs_mm':life['wear_pairs_mm'],'compression_pairs_mm':life['compression_pairs_mm']}
 result=dict(geometry=geometry,schema='o6-short-joint-candidate-v1',parts=rows,section_bounds_mm=section_boxes,support_span_mm=8.2 if a.compact_bearing else 14.0,part_count=len(rows),bounds_mm=bounds(compound),modeled_mass_g=sum(p['mass_g'] for p in rows),nominal_intersections=hits,rear_insertion=insertion,rear_wear_slide=slide,female_thread_guide_pocket_intersection_mm3=sum(female.intersect(p).Volume() for p in pockets),thread_envelope_min_wall_mm=15.6-14.03,guide_pocket_min_radial_wall_mm=15.6-math.hypot(14.2,2.08),shim_capture_recess_min_radial_wall_mm=15.6-math.hypot(14.2,3.1),front_backing_relative_interface='REMOVED_BY_ONE_PIECE_STEEL_FRONT',guide_clearance_nominal_mm=.04,guide_clearance_assembly_acceptance_mm=[.02,.04],output_rear_extent_mm=23.4,O5_output_rear_extent_mm=34,output_axial_extent_saved_vs_O5_mm=10.6,output_service_sequence=['Support/remove carried segment','Remove central M2.5 and hub/yoke','Remove cap locking dog','Use hollow pin spanner','Reassemble with qualified preload and recheck zero'],manufacturing_released=False,physical_tested=False,open=['Taper contact/preload/strength','Front plate bolt strength and preload','Shim retention/flatness and torque-loaded sliding','Actual maximum spring force and lining bond','Production fillets/threads/tolerances/DFM','Full yokes/harness/assembly'],input_sha256=consumed,boolean_volume_guards=RECEIPTS,generator_sha256=sha(Path(__file__)))
 consumed[(H/'cad/revO6/thread_geometry.py').relative_to(R).as_posix()]=sha(H/'cad/revO6/thread_geometry.py');assert all(sha(R/k)==h for k,h in consumed.items());dump(a.out/'manifest.json',result)
 print(json.dumps({k:result[k] for k in ('part_count','modeled_mass_g','nominal_intersections','female_thread_guide_pocket_intersection_mm3','output_axial_extent_saved_vs_O5_mm')}),flush=True)
if __name__=='__main__':main()

