"""L6-R3: integral per-half sensor towers; steel-backed externally keyed wear faces.
Nominal CAD and conditional strength/tolerance study; supplier and physical gates remain open.
"""
from pathlib import Path
import math,sys
import cadquery as cq
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT.parents[1]/'scripts'))
from revo3_evidence import read,save,sha,run_paths
THREAD_PITCH=.75
FRONT_SHIFT=-.8
STACK_SHIFT=-1.4
PCB_DATUM=28.595
BACKING_THICKNESS=.8
EAR_RADIUS=12.9
TOTAL_WEAR_BUDGET=.6
MAX_SINGLE_FACE_WEAR=.45
MIN_REMAINING_LINING=.15
DENSITY={'al6061':.00270,'al7075':.00281,'steel':.00785,'bronze':.00880,'POM':.00141,'lining':.00180,'magnet':.00750,'FR4':.00185,'package':.00170,'connector':.00160,'ceramic':.0035,'nylon':.00114}
COLORS={'al6061':'#9eb5c8','al7075':'#7994ac','steel':'#667486','bronze':'#b4a175','POM':'#dedcc5','lining':'#b47751','magnet':'#d76765','FR4':'#338f73','package':'#37434d','connector':'#dfdecf','ceramic':'#b49665','nylon':'#d0c4ab'}
def cyl(radius,z0,z1):return cq.Solid.makeCylinder(radius,z1-z0,cq.Vector(0,0,z0))
def ring(ro,ri,z0,z1):return cyl(ro,z0,z1).cut(cyl(ri,z0-.01,z1+.01))
def box(dx,dy,dz,center):return cq.Workplane('XY').box(dx,dy,dz).translate(center).val()
def hole_x(radius,x0,x1,y,z):return cq.Solid.makeCylinder(radius,x1-x0,cq.Vector(x0,y,z),cq.Vector(1,0,0))
def bounds(s):
 b=s.BoundingBox();return [b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax]
def thread_sweep(points,z0=-14.0,height=9.0,pitch=THREAD_PITCH):
 # Explicit ruled helical faces avoid the pipe-sweep kernel's false valid solids.
 # Method reference: cq_warehouse/thread.py make_thread_faces (Gumyr, Apache-2.0).
 edges=[cq.Wire.makeHelix(pitch,height,r).translate((0,0,dz)) for r,dz in points]
 faces=[cq.Face.makeRuledSurface(a,b) for a,b in zip(edges,edges[1:]+edges[:1])]
 for t in (0,1):
  vertices=[wire.positionAt(t) for wire in edges]
  faces.append(cq.Face.makeFromWires(cq.Wire.makePolygon(vertices+[vertices[0]])))
 result=cq.Solid.makeSolid(cq.Shell.makeShell(faces))
 assert result.isValid() and result.Volume()>0
 return result.translate((0,0,z0))

def disc_spring(z,height,flipped):
 cone=height-.5
 points=[(3.1,z+cone),(6,z),(6,z+.5),(3.1,z+height)]
 if flipped:points=[(x,2*z+height-y) for x,y in points]
 return cq.Workplane('XZ').polyline(points).close().revolve(360,(0,0),(0,1)).val()
def module(lighten=True):
 rows=[]
 def add(name,shape,material,owner='parent',group=None,note=''):
  if not shape.isValid() or len(shape.Solids())!=1 or shape.Volume()<=0:raise ValueError('Invalid/disconnected/nonpositive physical part '+name)
  rows.append(dict(name=name,shape=shape,material=material,owner=owner,group=group or name,note=note));return shape
 def split(name,shape,material,owner='parent',group=None,thread_cut=None):
  for side,sign in [('L',-1),('R',1)]:
   half=shape.intersect(box(80,120,140,(sign*40,0,0)))
   assert half.Volume()>0 and len(half.Solids())==1, 'Half-shell must contain connected material'
   if thread_cut is not None:
    before=half.Volume();half=half.cut(thread_cut,tol=1e-6).clean()
    assert 0<half.Volume()<before, 'Female thread must subtract material'
   add(name+'_'+side,half,material,owner,group or name+'_'+side)
 # Real helical material, not two abutting cylinders called a threaded pair.
 print('Building matched thread solids',flush=True)
 male=thread_sweep([(13.60,-(.03125+.34/math.sqrt(3))),(13.94,-.03125),(13.94,.03125),(13.60,.03125+.34/math.sqrt(3))])
 female=thread_sweep([(13.68,-.24),(14.03,-(.24-.35/math.sqrt(3))),(14.03,.24-.35/math.sqrt(3)),(13.68,.24)])
 # One-piece brake cup closes the metal preload loop. The precision bearing
 # cartridge alone splits radially; the cup slides over the bare keyed tail.
 # This also avoids machining an interrupted female thread across split halves.
 cup=ring(15,12.35,-13.4+STACK_SHIFT,1.5).fuse(ring(15,4.3,0,1.5))
 cup=cup.cut(cyl(13.70,-13.5+STACK_SHIFT,-4.7+STACK_SHIFT))
 cup=cup.fuse(ring(7.49,4.50,1.5,2.0))
 mounts=[(sx*12.3,sy*7.1) for sx in (-1,1) for sy in (-1,1)]
 for x,y in mounts:
  cup=cup.fuse(cyl(1.5,-2.5,1.5).translate((x,y,0)))
  cup=cup.cut(cyl(.83,-2.0,1.6).translate((x,y,0)))
 cup=cup.fuse(box(4.0,4.0,4.2,(16.7,0,-9.5+STACK_SHIFT))).cut(hole_x(.83,13.0,19,0,-9.5+STACK_SHIFT))
 # No lining locating pins in the rotating annulus. Steel carrier ears react torque outside r=12 mm.
 assert male.isValid() and female.isValid(), 'Helical tools must not self-intersect'
 before=cup.Volume();cup=cup.cut(female.translate((0,0,STACK_SHIFT)))
 assert 0<cup.Volume()<before and cup.isValid() and len(cup.Solids())==1, ('Thread subtraction continuity/volume',before,cup.Volume(),cup.isValid(),len(cup.Solids()))
 for x in (-EAR_RADIUS,EAR_RADIUS):cup=cup.cut(box(2.6,4.16,14.81,(x,0,-7.405)))
 add('one_piece_brake_cup',cup,'al6061')
 # Two bearing bands, 14 mm apart; cup register and planar flange locate the
 # matched cartridge halves while four axial screws retain the flange.
 outer=6.5 if lighten else 7.5
 body=ring(outer,4.50,1.5,20).cut(cyl(5.1,5.2,15.8))
 body=body.fuse(ring(outer,3.3,7,7.6)).fuse(ring(outer,3.3,9.4,10))
 body=body.fuse(ring(17,4.5,1.5,3.0)).cut(cyl(7.50,1.49,2.0))
 for x,y in mounts:body=body.cut(cyl(1.10,1.4,3.1).translate((x,y,0)))
 for y in (-6,6):
  body=body.fuse(box(15,4,4,(0,y,12.5)))
  body=body.cut(hole_x(1.10,-8,.1,y,12.5)).cut(hole_x(.83,-.1,8,y,12.5))
 for x in (-7.7,7.7):body=body.fuse(box(3.4,3,1.2,(x,0,19.4)))
 for x in (-7.7,7.7):
  post=ring(1.5,.65,19.8,PCB_DATUM-.91).translate((x,0,0))
  shelf=box(3.4,2.5,.5,(x/abs(x)*6.5,0,PCB_DATUM-1.16))
  body=body.fuse(post).fuse(shelf).cut(cyl(.65,19.7,PCB_DATUM-.90).translate((x,0,0)))
 split('housing',body,'al6061')
 for i,(x,y) in enumerate(mounts):
  screw=cyl(.80,-1.8,3.0).fuse(cyl(1.8,3.0,5.0)).translate((x,y,0))
  add('cup_mount_'+str(i),screw,'steel',note='M2 axial mounting core; 3.3 mm nominal cup engagement. Precision cup register locates the matched split cartridge.')
 # Closed bearing sleeves and thrust rings are also split, so every collar is assemblable.
 for z0,z1,name in [(1.8,5.2,'rear_bush'),(15.8,19.2,'front_bush')]:split(name,ring(4.49,3.01,z0,z1),'bronze')
 for z0,z1,name in [(7.6,8.0,'thrust_rear'),(9.0,9.4,'thrust_front')]:split(name,ring(4.8,3.015,z0,z1),'POM')
 shaft=cyl(3,-18,22.6).fuse(cyl(4.6,8.025,8.975)).fuse(cyl(5.5,20.6,25.1))
 shaft=shaft.cut(cyl(3.05,22.6,25.2)).cut(box(5,8,5,(5,0,-15.5)))
 for x in (-4.25,4.25):shaft=shaft.cut(cyl(.5,23.1,25.3).translate((x,0,0)))
 for sign in (-1,1):shaft=shaft.fuse(box(1.52,2.00,4.9,(sign*3.05,0,-1.0)))
 add('measurement_shaft',shaft,'al7075','child')
 # The brake disc transmits torque through integral sliding drive ribs, not an axial shaft clamp.
 rotor=ring(12,3.025,-2.1,-.6).fuse(ring(4.05,3.025,-3.3,1.0))
 for sign in (-1,1):rotor=rotor.cut(box(1.8,2.008,5.0,(sign*3.05,0,-1.0)))
 add('floating_brake_disc',rotor.translate((0,0,FRONT_SHIFT)),'steel','child',note='Axial motion tied to individual front lining wear/compression, checked in lifecycle report.')
 # Bonded replaceable friction layers on steel carriers. No bond strength is
 # credited as qualified: supplier torsional/peel/temperature tests remain mandatory.
 front=ring(12,4.2,-.6+FRONT_SHIFT,FRONT_SHIFT)
 rear=ring(12,4.2,-2.7+FRONT_SHIFT,-2.1+FRONT_SHIFT)
 def carrier(z0,z1):
  part=ring(12.1,4.3,z0,z1)
  for x in (-EAR_RADIUS,EAR_RADIUS):part=part.fuse(box(2.4,4.0,z1-z0,(x,0,(z0+z1)/2)))
  return part
 add('front_lining_backing',carrier(FRONT_SHIFT,0),'steel',note='Two external torque ears; friction-layer bond unqualified, no free strength credit.')
 add('rear_lining_backing',carrier(-2.9+STACK_SHIFT,-2.7+FRONT_SHIFT),'steel',note='Slides axially in cup tracks. No retention feature projects into wear face.')
 plate=ring(12,4.3,-4.7,-2.9)
 for x in (-EAR_RADIUS,EAR_RADIUS):plate=plate.fuse(box(2.4,4.0,1.8,(x,0,-3.8)))
 # Spring OD guide is positive metal geometry. Its lower end enters a relief in the cap.
 guide=ring(6.40,6.08,-9.3,-4.7)
 plate=plate.fuse(guide)
 add('front_friction_lining',front,'lining');add('rear_friction_lining',rear,'lining');add('keyed_pressure_plate',plate.translate((0,0,STACK_SHIFT)),'al6061')
 add('spring_front_washer',ring(6.03,3.15,-5.2+STACK_SHIFT,-4.7+STACK_SHIFT),'steel')
 for i in range(4):add('disc_spring_'+str(i+1),disc_spring(-7.55+STACK_SHIFT+i*.5875,.5875,i%2==1),'steel',note='SCHNORR 002100 geometry at catalog 0.75 h0; force/tolerance curve not qualified.')
 add('spring_rear_washer',ring(6.03,3.15,-8.05+STACK_SHIFT,-7.55+STACK_SHIFT),'steel')
 # Generate a finite thread directly: clipping a long swept helix can leave
 # a topologically valid but incorrectly classified OCC cap near its end.
 cap_thread=thread_sweep([(13.60,-(.03125+.34/math.sqrt(3))),(13.94,-.03125),(13.94,.03125),(13.60,.03125+.34/math.sqrt(3))],z0=-11.8,height=3.5).rotate((0,0,0),(0,0,1),(-11.8+14)/THREAD_PITCH*360)
 assert cap_thread.isValid() and len(cap_thread.Solids())==1
 cap=cyl(13.63,-12.05,-8.05).fuse(cap_thread).cut(cyl(3.4,-12.1,-8.0))
 cap=cap.cut(ring(6.55,6.04,-9.7,-8.0))
 if lighten:
  pockets=ring(12.2,6.8,-12.06,-9.65).cut(box(30,5,4,(0,0,-10.8))).cut(box(5,30,4,(0,0,-10.8)))
  cap=cap.cut(pockets) # Four 5-mm-wide full-thickness radial ribs retained.
 for x in (-10.5,10.5):cap=cap.cut(cyl(.85,-12.1,-10.55).translate((x,0,0)))
 for i in range(12):cap=cap.cut(box(1.0,1.1,4.2,(13.9,0,-10.05)).rotate((0,0,0),(0,0,1),i*30))
 add('threaded_adjuster_cap',cap.translate((0,0,STACK_SHIFT)),'al6061',note='Diameter 28 x 0.75 custom 60-degree reference 60-degree thread; 4.0 mm axial overlap, production tolerance class pending supplier.')
 lock=hole_x(.79,15.0,18.7,0,-9.5).fuse(hole_x(.48,13.41,15.0,0,-9.5)).fuse(hole_x(1.7,18.7,20.3,0,-9.5))
 add('cap_lock_dog_screw',lock.translate((0,0,STACK_SHIFT)),'steel',note='Positive slot dog, not friction-only cap lock. Small fastener threads represented by root core plus reference engagement.')
 for y in (-6,6):add('bearing_clamp_'+str(y),hole_x(.8,-7.5,5.5,y,12.5).fuse(hole_x(1.8,-9.5,-7.5,y,12.5)),'steel')
 add('diametric_magnet',cyl(3,22.6,25.1),'magnet','child')
 keeper=ring(5.5,2.8,25.1,25.65)
 for x in (-4.25,4.25):keeper=keeper.cut(cyl(.65,25.09,25.66).translate((x,0,0)))
 add('magnet_keeper',keeper,'nylon','child')
 for x in (-4.25,4.25):add('keeper_screw_'+str(x),cyl(.48,23.65,25.65).fuse(cyl(1.1,25.65,26.15)).translate((x,0,0)),'steel','child')
 pcbdatum=PCB_DATUM
 actual=cq.importers.importStep(str(ROOT/'electronics/sensor_revM_side/sensor_revM_side.step')).val().translate((-100,100,0)).rotate((0,0,0),(1,0,0),180).translate((0,0,pcbdatum))
 mats=['ceramic','ceramic','ceramic','ceramic','package','connector','FR4']
 for i,shape in enumerate(actual.Solids()):add('sensor_pcba_'+str(i),shape,mats[i],group='sensor_pcba',note='Unscaled reference STEP; material-class density estimate, not supplier mass or weighing.')
 for x in (-7.7,7.7):
  clamp=box(3.7,2.5,.7,(x/abs(x)*7.2,0,pcbdatum+.35)).cut(cyl(.85,pcbdatum-.01,pcbdatum+.71).translate((x,0,0)))
  add('pcb_edge_clamp_'+str(x),clamp,'al6061')
  add('pcb_clamp_screw_'+str(x),cyl(.62,pcbdatum-2.3,pcbdatum+.7).fuse(cyl(1.4,pcbdatum+.7,pcbdatum+1.9)).translate((x,0,0)),'steel')
 tool=ring(12.5,4.2,-23,-12.45)
 for x in (-10.5,10.5):tool=tool.fuse(cyl(.8,-12.45,-11.05).translate((x,0,0)))
 tools={'hollow_pin_spanner':tool.translate((0,0,.4+STACK_SHIFT))}
 return rows,tools
