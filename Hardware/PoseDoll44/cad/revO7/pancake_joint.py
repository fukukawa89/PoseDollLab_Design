"""LP6: two friction faces, three peripheral disc-spring stacks, independent journal shaft.
Research specimen only. No physical force, material, tolerance or motion rating.
"""
from pathlib import Path
import argparse,hashlib,itertools,json,math,sys
import cadquery as cq
R=Path(__file__).resolve().parents[4];H=R/'Hardware/PoseDoll44';OLD=H/'generated/revO6/runs/o6_20260924_r1/joint_L6_validated'
sys.path.insert(0,str(H/'cad/revO3'));from compact_joint import cyl,ring,box,bounds,hole_x
sys.path.insert(0,str(H/'cad/revO6'));from small_joint import spring
from thread_geometry import thread_sweep,checked,RECEIPTS,overlap_volume

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
def at(s,r,angle):return s.translate((r,0,0)).rotate((0,0,0),(0,0,1),angle)
def dshaft(ro,flat,z0,z1):return cyl(ro,z0,z1).intersect(box(2*flat,2*ro+2,z1-z0,(0,0,(z0+z1)/2)))
def hexagon(af,z0,z1):return cq.Workplane('XY').polygon(6,2*af/math.sqrt(3)).extrude(z1-z0).val().translate((0,0,z0))
def lining(z0,z1,clearance=0):
 s=ring(14,6,z0,z1)
 for a in (0,120,240):s=s.fuse(at(box(1.4+clearance,2+clearance,z1-z0,(0,0,(z0+z1)/2)),14.6,a))
 return s.clean()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 sources=[Path(__file__),OLD/'manifest.json',H/'cad/revO3/compact_joint.py',H/'cad/revO6/small_joint.py',H/'cad/revO6/thread_geometry.py'];parts={};meta={};dens={'al7075':.00281,'steel':.00785,'bronze':.0088,'POM':.00142,'PEEK':.00131};old=json.loads((OLD/'manifest.json').read_text());dens.update({p['material']:p['mass_g']/p['volume_mm3'] for p in old['parts']})
 def add(n,s,material='al7075',owner='parent',note=''):
  assert s.isValid() and len(s.Solids())==1 and s.Volume()>0,(n,s.isValid(),len(s.Solids()))
  parts[n]=s;meta[n]=(material,owner,note)
 def split(n,s,material='al7075',owner='parent',note=''):
  for suffix,sign in [('L',-1),('R',1)]:add(n+'_'+suffix,s.intersect(box(80,100,100,(sign*40,0,0))),material,owner,note)
 # Original sensor package, board, connector, magnet and keeper are not scaled.
 for row in old['parts']:
  n=row['part_id']
  if n.startswith(('sensor_pcba_','diametric_magnet','magnet_keeper','keeper_screw_','pcb_edge_clamp_','pcb_clamp_screw_')):
   p=OLD/row['step_file'];assert sha(p)==row['step_sha256'];sources.append(p);add(n,cq.importers.importStep(str(p)).val().translate((0,0,-4.5)),row['material'],row['owner'],'Unscaled O6 procurement/reference solid, translated -4.5 mm only.')
 stations=(90,210,330);guides=(30,150,270);RSPR=11.4;RG=17.8
 # Front seat closes radially; monolithic rear plate slides axially over the preassembled bearing and collar.
 front=ring(20,5.10,-3,0).fuse(ring(6.6,3.2,-4.3,-3))
 front=front.cut(cyl(5.0,-3.9,-.9)).cut(cyl(4.99,-.9,-.5)).cut(cyl(5.1,-.5,.01))
 front=front.fuse(ring(15.6,14.04,0,.6).cut(lining(-.01,.61,.02)))
 rear=ring(20,5.0,7,10).fuse(ring(6.6,4.91,6,7)).cut(cyl(5.0,6.9,9.9)).cut(cyl(4.99,6.5,6.9))
 cutter=thread_sweep([(2.72,-.23),(3.07,-(.23-.35/math.sqrt(3))),(3.07,.23-.35/math.sqrt(3)),(2.72,.23)],z0=6.5,height=4,pitch=.5)
 for i,theta in enumerate(stations):
  v_before=rear.Volume()
  # Cutting the helix before the bore avoids an OCC false-empty common on this small radius.
  rear=checked(rear,at(cutter,RSPR,theta),'cut','LP6 preload socket '+str(i));rear=rear.cut(at(cyl(2.73,6.9,10.1),RSPR,theta),tol=1e-5)
  groove_removed=v_before-rear.Volume()-math.pi*2.73**2*3
  assert 9.10<groove_removed<9.36,('Female groove not actually removed',i,groove_removed)
  RECEIPTS.append({'operation':'female_actual_material_removed_after_bore','station':i,'groove_mm3':groove_removed,'independent_whole_turn_reference_mm3':9.2299,'allowed_range_mm3':[9.10,9.36],'pass':True})
  rear=rear.cut(at(cyl(3.15,9.65,10.01),RSPR,theta),tol=1e-5)
  # Radial locking dog reaches a crown notch, not an assumed nut friction lock.
  lug=box(4.6,3.2,2.4,(16.8,0,11.2));rear=rear.fuse(lug.rotate((0,0,0),(0,0,1),theta))
  rear=rear.cut(hole_x(.83,13.5,19.3,0,11.2).rotate((0,0,0),(0,0,1),theta))
 for theta in guides:
  front=front.cut(at(cyl(1.1,-3.1,.7),RG,theta));rear=rear.cut(at(cyl(1.1,6.9,10.1),RG,theta))
 # Two explicit M2 cross bolts retain each split bearing plate.
 for body,z in [('front',-1.5)]:
  s=front if body=='front' else rear
  for y in (-16.2,16.2):s=s.cut(hole_x(1.1,-14,.1,y,z)).cut(hole_x(.83,-.1,7,y,z)).cut(hole_x(1.85,-14,-6.7,y,z))
  if body=='front':front=s
  else:rear=s
 for x in (-7.7,7.7):
  rear=rear.fuse(ring(1.5,.65,9.9,17.385).translate((x,0,0)))
  rear=rear.fuse(box(3.4,5.0,.5,(math.copysign(6.5,x),0,17.135)))
  rear=rear.cut(cyl(.65,9.8,17.40).translate((x,0,0)))
 rear=rear.cut(cyl(5.65,16.88,17.40))
 support=[]
 for sign in (-1,1):
  half=rear.intersect(box(80,100,100,(sign*40,0,0)))
  area=half.intersect(parts['sensor_pcba_6'].translate((0,0,-.01)),tol=1e-5).Volume()/.01
  assert area>2.5,('PCB pad lost contact area',sign,area)
  support.append({'side':sign,'nominal_contact_area_mm2':area,'clamp_strength_verified':False})
 # Removable steel bearing keeper traps the bush axially. It is installed before the sensor cup.
 keeper=ring(8.2,3.05,10,10.8)
 for x in (-7.7,7.7):keeper=keeper.cut(cyl(1.55,9.9,10.9).translate((x,0,0)))
 for i,theta in enumerate((45,135,225,315)):
  rear=rear.cut(at(cyl(.65,7.7,10.1),7.2,theta));keeper=keeper.cut(at(cyl(.85,9.9,10.9),7.2,theta))
  screw=at(cyl(.63,7.8,10.8).fuse(cyl(1.5,10.8,12.4)),7.2,theta)
  add('rear_keeper_M1p6x3_'+str(i),screw,'steel',note='Root-core reference of M1.6 x3; exact head/tool and thread class pending.')
 for sign in (-1,1):add('rear_bearing_keeper_'+str(sign),keeper.intersect(box(100,80,100,(0,sign*40,0))),'steel',note='Split along Y: closes radially below integrated PCB ledges; two axial bolts per half.')
 split('front_reaction_and_bearing',front.clean());add('rear_reaction_and_bearing',rear.clean())
 for label,z in [('front',-1.5)]:
  for y in (-16.2,16.2):add(label+'_split_bolt_'+str(y),hole_x(.80,-6.7,5.3,y,z).fuse(hole_x(1.8,-8.7,-6.7,y,z)),'steel',note='M2 x12 reference, pilot/root core; socket and supplier qualification required.')
 # Three fixed sleeves locate the pressure plate radially/tangentially; bolts carry separation force.
 for i,theta in enumerate(guides):
  add('guide_sleeve_'+str(i),at(ring(1.5,1.1,0,7),RG,theta),'steel',note='Custom ground OD3/ID2.2/length7 sleeve; bore fit remains to be qualified.')
  add('cage_M2x15_'+str(i),at(cyl(.8,-5,10).fuse(cyl(1.8,10,12)),RG,theta),'steel')
  add('cage_nut_M2_'+str(i),at(hexagon(4,-4.6,-3).cut(cyl(.81,-4.7,-2.9)),RG,theta),'steel')
 # Split bushes and two thrust lands have their own shaft datum; brake force
 # travels between face plates and outer bolts, never intentionally through these washers.
 split('front_bush',ring(4.99,3.01,-3.9,-.9),'bronze')
 split('rear_bush',ring(4.99,3.01,6.9,9.9),'bronze')
 split('front_thrust',ring(4.9,3.015,-.9,-.55),'POM')
 split('rear_thrust',ring(4.9,3.015,6.5,6.9),'POM')
 shaft=cyl(3,-4.4,10.9).fuse(cyl(9,-7.4,-4.4)).fuse(cyl(4.8,-.5,-.05)).fuse(dshaft(2,1.7,10.9,11.8))
 shaft=shaft.cut(ring(3.1,2.7,5.97,6.48)).cut(hole_x(.65,1.0,3.1,0,11.55).rotate((0,0,0),(0,0,1),67.5))
 for x,y in [(6,0),(-6,0),(0,6),(0,-6)]:shaft=shaft.cut(cyl(.83,-7.41,-4.39).translate((x,y,0)))
 for x in (-3.15,3.15):shaft=shaft.fuse(box(1.2,2,2.6,(x,0,1.4)))
 add('integral_output_measurement_shaft',shaft.clean(),'al7075','child','Integral output flange; removable sensor cup and radial split rear thrust collar permit real assembly. Journal/straightness needs production drawing.')
 split('rear_shaft_collar',ring(4.8,2.71,6,6.45),'steel','child','Captive halves fit shaft groove; rear seat restrains radial escape. Geometric retention audit required.')
 rotor=ring(14,3.03,.6,2.1)
 for x in (-3.15,3.15):rotor=rotor.cut(box(1.24,2.004,2,(x,0,1.35)))
 add('floating_rotor',rotor,'steel','child','Ground stainless candidate; actual alloy/surface/magnetic behavior and torque-loaded sliding unqualified.')
 add('front_lining',lining(0,.6),'PEEK',note='Unfilled PEEK first coupon candidate, mechanically keyed ears. Material does not establish friction or creep rating.')
 add('rear_lining',lining(2.1,2.7),'PEEK')
 pressure=ring(15.5,5.2,2.7,4.2).fuse(ring(15.6,14.04,2.1,2.7).cut(lining(2.09,2.71,.02)))
 for theta in guides:pressure=pressure.fuse(at(box(3.0,4.0,1.5,(0,0,3.45)),16.5,theta)).fuse(at(cyl(2.0,2.7,4.2),RG,theta)).cut(at(cyl(1.51,2.69,4.21),RG,theta))
 for theta in stations:pressure=pressure.fuse(at(cyl(2.0,4.2,6.3),RSPR,theta))
 add('floating_pressure_carrier',pressure.clean(),note='3 pin guided; pads and spring stems integral. Loaded tilt/flatness/guide friction must be measured.')
 male=thread_sweep([(2.70,-(.025+.30/math.sqrt(3))),(3.0,-.025),(3.0,.025),(2.70,.025+.30/math.sqrt(3))],z0=6.5,height=3.5,pitch=.5)
 plug=checked(cyl(2.71,5.675,10.4),male,'fuse','LP6 preload plug').fuse(cyl(3.1,10.2,12.2),tol=1e-5).cut(cyl(2.06,5.6,7.2),tol=1e-5)
 plug=plug.cut(hexagon(2,9.8,12.6),tol=1e-5)
 for k in range(12):plug=plug.cut(box(.90,.90,1.5,(3.2,0,11.35)).rotate((0,0,0),(0,0,1),k*30),tol=1e-5)
 for i,theta in enumerate(stations):
  add('spring_lower_seat_'+str(i),at(ring(4.1,2.06,4.2,4.45),RSPR,theta),'steel')
  for j in range(2):add(f'B8_spring_{i}_{j}',at(spring(4,2.1,.3,4.45+j*.3625,.3625,j%2==1),RSPR,theta),'steel',note='Raleigh B 8 x4.2 x0.3, two opposed discs per station;118N catalog point per stack, not max force.')
  add('spring_upper_seat_'+str(i),at(ring(4.1,2.06,5.175,5.675),RSPR,theta),'steel')
  add('M6p5_preload_plug_'+str(i),at(plug,RSPR,theta),'steel',note='Custom 6 mm x0.5 reference helix; selected production thread class/lead-in/runout remain to be detailed.')
  dog=hole_x(.4,14.25,15.0,0,11.2).fuse(hole_x(.80,15.0,19.2,0,11.2)).cut(hexagon(1.0,18.2,19.3).rotate((0,0,0),(0,1,0),90).translate((0,0,11.2)))
  add('preload_lock_dog_'+str(i),dog.rotate((0,0,0),(0,0,1),theta),'steel',note='Custom headless M2 reduced-tip radial dog, AF1 hex socket; thread and strength unqualified.')
 # Unloaded, positive D sensor cup; radial screw mechanically retains it.
 cup=cyl(5.5,10.9,14.8).cut(dshaft(2.04,1.74,10.89,11.85)).cut(cyl(3.05,12.3,14.81)).cut(hole_x(.65,1.5,5.6,0,11.55).rotate((0,0,0),(0,0,1),67.5))
 for x in (-4.25,4.25):cup=cup.cut(cyl(.5,12.9,14.81).translate((x,0,0)))
 add('removable_sensor_cup',cup,'al7075','child')
 add('sensor_cup_radial_screw',hole_x(.63,1.5,5.5,0,11.55).rotate((0,0,0),(0,0,1),67.5),'steel','child','M1.6 headless root-core reference; positive radial retention, supplier/tool details pending.')
 mate=ring(9,3.2,-9.4,-7.4)
 for i,(x,y) in enumerate([(6,0),(-6,0),(0,6),(0,-6)]):
  mate=mate.cut(cyl(1.10,-9.41,-7.39).translate((x,y,0)));add('output_M2x5_'+str(i),cyl(.8,-9.4,-4.4).fuse(cyl(1.8,-11.4,-9.4)).translate((x,y,0)),'steel','child')
 add('output_yoke_interface',mate,'al7075','child','Four-hole annular interface. Real inter-axis yoke is not yet implied by this ring.')
 print('LP6 export and nominal audit',len(parts),flush=True);rows=[]
 for n,s in parts.items():
  p=a.out/(n+'.step');cq.exporters.export(s,str(p));mat,owner,note=meta[n];rows.append({'part_id':n,'owner':owner,'material':mat,'density_g_mm3':dens[mat],'volume_mm3':s.Volume(),'mass_g':s.Volume()*dens[mat],'bounds_mm':bounds(s),'local_com_mm':list(s.Center().toTuple()),'step_file':p.name,'step_sha256':sha(p),'note':note})
 hits=[]
 for n,j in itertools.combinations(parts,2):
  v=overlap_volume(parts[n],parts[j])
  if v>1e-4:hits.append({'a':n,'b':j,'volume_mm3':v})
 compound=cq.Compound.makeCompound(list(parts.values()));cq.exporters.export(compound,str(a.out/'LP6.step'))
 sections=[]
 for lo,hi in [(-12,-3),(-3,0),(0,7),(7,14),(14,22)]:
  sl=box(60,60,hi-lo,(0,0,(hi+lo)/2));pieces=[]
  for shape in parts.values():
   b=bounds(shape)
   if b[5]<=lo+1e-6 or b[2]>=hi-1e-6:continue
   q=shape.intersect(sl,tol=1e-5)
   if q.Volume()>1e-5:pieces.append(q)
  sections.append(bounds(cq.Compound.makeCompound(pieces)))
 inputs={p.relative_to(R).as_posix():sha(p) for p in sources}
 save(a.out/'manifest.json',{'schema':'o7-LP6-specimen-v1','parts':rows,'pcb_support_contact':support,'central_board_ledge_access_diameter_mm':11.3,'section_bounds_mm':sections,'part_count':len(parts),'bounds_mm':bounds(compound),'modeled_mass_g':sum(r['mass_g'] for r in rows),'nominal_intersections':hits,'support_span_mm':10.8,'geometry':{'sensor_cup_access_angle_deg':67.5,'spring_radius_mm':RSPR,'spring_angles_deg':list(stations),'guide_radius_mm':RG,'guide_angles_deg':list(guides),'spring_work_height_mm':.3625,'spring_free_height_mm':.55,'springs_series_per_station':2,'stations_parallel':3,'catalog_point_total_N':354,'lining_ri_mm':6,'lining_ro_mm':14,'lining_thickness_mm':.6,'preload_thread_pitch_mm':.5,'preload_index_positions':12},'boolean_volume_guards':RECEIPTS,'input_sha256':inputs,'generator_sha256':sha(Path(__file__)),'status':'FAIL_NOMINAL' if hits else 'PASS_NOMINAL_ONLY','physical_tested':False,'manufacturing_released':False,'open':['Assembly and tool paths','Nominal and tolerance wear states, spring mismatch and pressure plate tilt','Mechanical retention of split collars, cup and liners','Fixture/material tests and real force curves','Full multi-axis carrier, PCBA/harness/body integration']})
 print(json.dumps({'parts':len(parts),'mass_g':sum(r['mass_g'] for r in rows),'bounds':bounds(compound),'hits':hits}),flush=True)
if __name__=='__main__':main()
