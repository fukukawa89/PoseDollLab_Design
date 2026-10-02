"""M4 digital specimen: unscaled AS5048 PCBA/magnet, 4 mm shaft, Raleigh 8 mm springs."""
from pathlib import Path
import argparse,hashlib,itertools,json,math,sys
import cadquery as cq
R=Path(__file__).resolve().parents[4];H=R/'Hardware/PoseDoll44';OLD=H/'generated/revO3/runs/o3_20260924_r3/joint'
sys.path.insert(0,str(H/'cad/revO3'))
from compact_joint import cyl,ring,box,hole_x,bounds
from thread_geometry import thread_sweep,checked,RECEIPTS,overlap_volume
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def spring(ro,ri,t,z,h,flip):
 q=[(ri,z+h-t),(ro,z),(ro,z+t),(ri,z+h)]
 if flip:q=[(x,2*z+h-y) for x,y in q]
 return cq.Workplane('XZ').polyline(q).close().revolve(360,(0,0),(0,1)).val()
def taper(z0,z1,tail):
 r=lambda z:1.9+.04*(z-tail);f=lambda z:1.5+.04*(z-tail)
 c=cq.Solid.makeCone(r(z0),r(z1),z1-z0,cq.Vector(0,0,z0))
 for side in (-1,1):
  tool=cq.Workplane('XZ').polyline([(side*f(z0),z0),(side*6,z0),(side*6,z1),(side*f(z1),z1)]).close().extrude(10,both=True).val();c=c.cut(tool)
 return c
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--spring-series',choices=['A','B'],default='A');a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 # Catalogue points, not maximum force or an ordered/qualified spring.
 t,hfree,hwork,F=(.4,.6,.45,210) if a.spring_series=='A' else (.3,.55,.3625,118)
 rear_seat_top=-4.55-4*hwork;cap_front=rear_seat_top-.35;cap_back=cap_front-3;tail=cap_back-2.95
 parts={};meta={};inputs={(OLD/'manifest.json').relative_to(R).as_posix():sha(OLD/'manifest.json'),(H/'cad/revO3/compact_joint.py').relative_to(R).as_posix():sha(H/'cad/revO3/compact_joint.py')}
 old=json.loads((OLD/'manifest.json').read_text());density={p['material']:p['density_g_mm3'] for p in old['parts']}
 def add(n,s,material='al6061',owner='parent',note=''):
  assert s.isValid() and len(s.Solids())==1 and s.Volume()>0,(n,s.isValid(),len(s.Solids()))
  parts[n]=s;meta[n]=(material,owner,note);return s
 for row in old['parts']:
  n=row['part_id']
  if n.startswith(('sensor_pcba_','pcb_edge_clamp_','pcb_clamp_screw_','diametric_magnet','magnet_keeper','keeper_screw_')):
   p=OLD/row['step_file'];assert sha(p)==row['step_sha256'];inputs[p.relative_to(R).as_posix()]=sha(p)
   add(n,cq.importers.importStep(str(p)).val().translate((0,0,-7.2)),row['material'],row['owner'],'Unscaled imported O3 procurement geometry; translated 7.2 mm only.')
 mounts=[(sx*6.7,sy*6.7) for sx in (-1,1) for sy in (-1,1)]
 cup=ring(11,7.7,-11.2,0).cut(cyl(9.10,-11.21,-4.0))
 female=thread_sweep([(9.08,-.2),(9.4,-(.2-.32/math.sqrt(3))),(9.4,.2-.32/math.sqrt(3)),(9.08,.2)],z0=-11.7,height=7.0,pitch=.5)
 cup=checked(cup,female,'cut','M4 female thread').clean();pockets=[]
 for x in (-8.1,8.1):
  cut=box(1.8,2.56,4,(x,0,-2));cup=cup.cut(cut);pockets.append(cut)
 for x in (-8.4,8.4):
  for sign in (-1,1):cup=cup.cut(box(1.2,.96,.08,(x,sign*1.68,-.04)))
 for x,y in mounts:cup=cup.cut(cyl(.66,-2.9,.01).translate((x,y,0)))
 cup=cup.fuse(box(3.6,3.2,3.6,(12.3,0,-8.1))).cut(hole_x(.66,8.8,14.2,0,-8.1))
 add('brake_cup_front_loading',cup)
 front=ring(11.8,2.8,0,1.2).fuse(ring(7.5,2.6,-.6,0)).fuse(ring(4.4,3.01,1.2,1.7))
 for x,y in mounts:front=front.cut(cyl(.85,-.01,1.21).translate((x,y,0)))
 add('integral_steel_front_backing',front,'steel')
 body=cyl(4.5,1.2,12.8).fuse(cyl(11.8,1.2,2.7)).cut(cyl(4.41,1.19,1.7))
 for y in (-4.5,4.5):body=body.fuse(box(10,3,2.8,(0,y,8.3)))
 for x in (-6.4,6.4):body=body.fuse(box(6,2.5,1.2,(x,0,12.2)))
 body=body.cut(cyl(3,1.19,12.81)).cut(cyl(3.5,3.9,9.7))
 for lo,hi in ((5.05,5.65),(7.15,7.75)):body=body.fuse(ring(4.5,2.3,lo,hi))
 for y in (-4.5,4.5):body=body.cut(hole_x(.85,-6,.1,y,8.3)).cut(hole_x(.66,-.1,6,y,8.3))
 for x,y in mounts:body=body.cut(cyl(.85,1.19,2.71).translate((x,y,0)))
 datum=21.395
 for x in (-7.7,7.7):
  body=body.fuse(ring(1.5,.65,12.6,datum-.91).translate((x,0,0))).fuse(box(3.4,2.5,.5,(math.copysign(6.5,x),0,datum-1.16))).cut(cyl(.65,12.5,datum-.90).translate((x,0,0)))
 def split(n,s,mat):
  for side,sign in (('L',-1),('R',1)):add(n+'_'+side,s.intersect(box(80,100,100,(sign*40,0,0))),mat)
 split('housing',body.clean(),'al6061')
 for i,(x,y) in enumerate(mounts):add('cup_mount_'+str(i),cyl(.64,-2.3,2.7).fuse(cyl(1.5,2.7,4.3)).translate((x,y,0)),'steel',note='M1.6 x 5 root-core/envelope candidate; fastener supplier and tool interface pending.')
 for y in (-4.5,4.5):add('bearing_clamp_'+str(y),hole_x(.64,-5,4,y,8.3).fuse(hole_x(1.5,-6.6,-5,y,8.3)),'steel')
 for lo,hi,n in ((1.5,3.9,'rear_bush'),(9.7,12.1,'front_bush')):split(n,ring(2.99,2.01,lo,hi),'bronze')
 for lo,hi,n in ((5.65,6,'thrust_rear'),(6.8,7.15,'thrust_front')):split(n,ring(3.25,2.015,lo,hi),'POM')
 shaft=cyl(2,tail+2.5,15.4).fuse(taper(tail,tail+2.51,tail)).fuse(cyl(3.1,6.025,6.775)).fuse(cyl(5.5,13.4,17.9)).cut(cyl(3.05,15.4,18))
 for x in (-4.25,4.25):shaft=shaft.cut(cyl(.5,15.9,18).translate((x,0,0)))
 for x in (-2.05,2.05):shaft=shaft.fuse(box(1,1,3.4,(x,0,-1.1)))
 shaft=shaft.cut(cyl(.65,tail-.01,tail+4.5))
 add('short_taper_measurement_shaft',shaft,'al7075','child')
 rotor=ring(7.4,2.025,-2.2,-1).fuse(ring(2.5,2.025,-2.7,.3))
 for x in (-2.05,2.05):rotor=rotor.cut(box(1.2,1.004,3.5,(x,0,-1.1)))
 add('floating_brake_disc',rotor,'steel','child')
 add('front_friction_lining',ring(7.4,2.6,-1,-.6),'lining')
 add('rear_friction_lining',ring(7.4,2.6,-2.6,-2.2),'lining')
 rear=ring(7.5,2.6,-4.2,-2.6).fuse(ring(4.4,4.08,-7.1,-4.2))
 for x in (-8.1,8.1):rear=rear.fuse(box(1.6,2.4,1.2,(x,0,-3.2)))
 add('integral_rear_sliding_carrier',rear,'steel')
 for x in (-8.4,8.4):
  for sign in (-1,1):
   shim=box(1.1,.07,3.93,(x,sign*1.245,-2.035)).fuse(box(1.1,.90,.07,(x,sign*1.66,-.035)))
   add(f'guide_shim_{x}_{sign}',shim,'steel',note='Fitted after measurement, target total running gap 0.01-0.02 mm; capture depends on assembled carrier.')
 add('spring_front_washer',ring(4.03,2.15,-4.55,-4.2),'steel')
 for i in range(4):add('disc_spring_'+str(i+1),spring(4,2.1,t,rear_seat_top+i*hwork,hwork,i%2==1),'steel',note=f'Raleigh catalogue {a.spring_series} series 8 x 4.2 x {t}; {F} N at 0.75 cone deflection, not maximum force.')
 add('spring_rear_washer',ring(4.03,2.15,cap_front,rear_seat_top),'steel')
 zstart=cap_back+.25
 male=thread_sweep([(9.02,-(.025+.30/math.sqrt(3))),(9.32,-.025),(9.32,.025),(9.02,.025+.30/math.sqrt(3))],z0=zstart,height=2.5,pitch=.5).rotate((0,0,0),(0,0,1),(zstart+11.2)/.5*360)
 cap=checked(cyl(9.05,cap_back,cap_front),male,'fuse','M4 male thread').cut(cyl(2.4,cap_back-.01,cap_front+.01)).cut(ring(4.55,4.04,cap_front-1.2,cap_front+.01))
 for x in (-7.2,7.2):cap=cap.cut(cyl(.65,cap_back-.01,cap_back+1.2).translate((x,0,0)))
 for i in range(12):cap=cap.cut(box(.8,.9,3.2,(9.3,0,(cap_back+cap_front)/2)).rotate((0,0,0),(0,0,1),30*i))
 add('threaded_adjuster_cap',cap,'al6061',note='Custom reference 18.6 x 0.5 helical geometry; production tolerance class pending.')
 lock=hole_x(.63,11,14.1,0,-8.1).fuse(hole_x(.4,8.9,11,0,-8.1)).fuse(hole_x(1.4,14.1,15.7,0,-8.1))
 add('cap_lock_dog_screw',lock,'steel')
 hub=cyl(6.5,tail-.3,tail+2.2).cut(taper(tail-.31,tail+2.21,tail));holes=[(4,0),(-4,0),(0,4),(0,-4)]
 for x,y in holes:hub=hub.cut(cyl(.66,tail-.31,tail+2.21).translate((x,y,0)))
 add('taper_output_hub',hub,'al7075','child')
 add('output_retention_washer',ring(2.25,.90,tail-.7,tail-.3),'steel','child')
 add('output_retention_screw',cyl(.63,tail-.7,tail+3.3).fuse(cyl(1.5,tail-2.3,tail-.7)),'steel','child',note='M1.6 x 4 root-core/envelope; socket and detailed thread pending.')
 mate=ring(6.5,2.35,tail-2.3,tail-.3)
 for x,y in holes:mate=mate.cut(cyl(.85,tail-2.31,tail-.29).translate((x,y,0)))
 add('output_yoke_interface',mate,'al7075','child')
 for i,(x,y) in enumerate(holes):add('output_yoke_screw_'+str(i),cyl(.64,tail-2.3,tail+1.7).fuse(cyl(1.5,tail-3.9,tail-2.3)).translate((x,y,0)),'steel','child')
 rows=[]
 for n,s in parts.items():
  mat,owner,note=meta[n];cq.exporters.export(s,str(a.out/(n+'.step')))
  rows.append(dict(part_id=n,step_file=n+'.step',step_sha256=sha(a.out/(n+'.step')),owner=owner,material=mat,volume_mm3=s.Volume(),local_com_mm=list(s.Center().toTuple()),mass_g=s.Volume()*density[mat],bounds_mm=bounds(s),note=note))
 print('Checking M4 part pairs',flush=True);hits=[]
 for n,j in itertools.combinations(parts,2):
  b,c=bounds(parts[n]),bounds(parts[j])
  if all(min(b[k+3],c[k+3])-max(b[k],c[k])>1e-5 for k in range(3)):
   v=overlap_volume(parts[n],parts[j])
   if v>1e-5:hits.append({'a':n,'b':j,'volume_mm3':v})
 sections=[]
 for z0,z1 in [(-24,-10),(-10,0),(0,5),(5,15),(15,26)]:
  pieces=[]
  for s in parts.values():
   if bounds(s)[2]>=z1 or bounds(s)[5]<=z0:continue
   q=s.intersect(box(100,100,z1-z0,(0,0,(z0+z1)/2)))
   if q.Volume()>1e-6:pieces.append(q)
  sections.append(bounds(cq.Compound.makeCompound(pieces)))
 compound=cq.Compound.makeCompound(list(parts.values()));cq.exporters.export(compound,str(a.out/'joint_M4.step'))
 result={'schema':'o6-M4-digital-specimen-v1','parts':rows,'part_count':len(rows),'nominal_intersections':hits,'section_bounds_mm':sections,'bounds_mm':bounds(compound),'support_span_mm':8.2,'modeled_mass_g':sum(q['mass_g'] for q in rows),'spring_source':{'url':'https://www.raleigh-spring.cn/discspring/','series':a.spring_series,'OD_mm':8,'ID_mm':4.2,'thickness_mm':t,'free_height_mm':hfree,'work_height_model_mm':hwork,'force_catalog_point_N':F,'maximum_force_N':None,'actual_spring_qualification':False},'geometry':{'spring_ro_mm':4,'spring_ri_mm':2.1,'spring_t_mm':t,'spring_hfree_mm':hfree,'spring_hwork_mm':hwork,'spring_stack_top_z_mm':-4.55,'front_lining_z_mm':[-1,-.6],'rear_lining_z_mm':[-2.6,-2.2],'lining_ro_mm':7.4,'lining_ri_mm':2.6,'thread_pitch_mm':.5,'nominal_guide_gap_mm':.02,'wear_pairs_mm':[[0,0],[.1,0],[0,.1],[.25,0],[0,.25],[.2,.2],[.25,.15],[.15,.25]],'compression_pairs_mm':[[0,0],[.02,.02],[.02,0],[0,.02]]},'female_thread_guide_pocket_intersection_mm3':sum(female.intersect(p).Volume() for p in pockets),'thread_envelope_min_wall_mm':1.6,'input_sha256':inputs,'boolean_volume_guards':RECEIPTS,'generator_sha256':sha(Path(__file__)),'manufacturing_released':False,'physical_tested':False,'not_qualified':['Spring force range/torque/friction/wear/bond','Bearing fits and precision under reversing load','Taper drive and retained shims','Production threads/fillets/tool access','Complete yokes and full-body packaging']}
 inputs[(H/'cad/revO6/thread_geometry.py').relative_to(R).as_posix()]=sha(H/'cad/revO6/thread_geometry.py');assert all(sha(R/k)==h for k,h in inputs.items());(a.out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:result[k] for k in ('part_count','modeled_mass_g','bounds_mm','nominal_intersections','female_thread_guide_pocket_intersection_mm3')}),flush=True)
if __name__=='__main__':main()

