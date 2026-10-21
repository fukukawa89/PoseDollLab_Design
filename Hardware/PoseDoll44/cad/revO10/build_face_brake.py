"""Face-brake TUT candidate: metal shoulder axles and split metal ring.
Printed small journals no longer transmit holding torque. Integral stop ears
sit outside the friction annulus and beyond the ring fastener corners.
No materials/threads/preload qualification is implied by these nominal solids.
"""
from solid_ops import *
sys.path.insert(0,str(H/'cad/revO8'))
from extend_forks import extend_section
EXTRA=1.5

def move_legs(t,axis,amount=2.3):
 t=t.copy();x=t[:,:,axis];s=np.sign(x)*amount*np.clip((np.abs(x)-4)/4,0,1);t[:,:,axis]+=s;return t

def disc_spring(z0,h=.45,t=.4,flip=False):
 # A polyline revolution: imported Raleigh A-series 8 x 4.2 x 0.4 catalogue
 # shape at h=.45, F=210 N at the cited point; not a measured force or maximum.
 profile=np.array([[2.1,z0+h-t],[4,z0],[4,z0+t],[2.1,z0+h]])
 if flip:profile[:,1]=2*z0+h-profile[:,1];profile=profile[::-1].copy()
 cs=md.CrossSection([profile])
 return cs.revolve(circular_segments=144)

def main():
 thread_file=OUT/'face_brake/threads.npz';thread_mesh=np.load(thread_file);male_thread=from_tri(thread_mesh['male']);female_tool=from_tri(thread_mesh['cutter']);raw=dict(np.load(CORE));forks={};ring=from_tri(raw['C14'])+from_tri(raw['C15']);parts={};records=[]
 for name,ax,limit in [('C01',0,28),('C02',1,98)]:
  extended=tri(from_tri(raw[name]));direction=-1 if name=='C01' else 1;extended[:,:,2]+=direction*EXTRA*np.clip((direction*extended[:,:,2]-6)/3,0,1);s=from_tri(extended)
  # Remove all original molded bearing pins before extending the outer legs.
  for side in (-1,1):
   lo,hi=sorted((side*4.99,side*9.27));s-=along(cylinder(2.6,lo,hi),ax)
  s=from_tri(move_legs(tri(s),ax))
  for side in (-1,1):
   label=f'{name}_{side:+d}'
   def oriented(x):
    if side<0:x=pose(x,rot(0,180))
    return along(x,ax)
   # Clear old molded-pin remnants; the central magnet has its own support.
   s-=oriented(cylinder(4.25,4.7,11.49))
   # Rebuild a solid metal threaded boss instead of trying to tap an old
   # oversized plastic-bearing bore. This supplies real engagement material.
   ring+=oriented(cylinder(4.0,5.0,8.8))
   # Ring face and remote stop track, deliberately outside x/y=7 screw axes.
   boss=cylinder(8.0,8.8,11.0)-cylinder(2.06,8.7,11.1)
   ring+=oriented(boss)
   ring-=oriented(cylinder(2.06,8.48,11.1))
   # M3 tapped engagement envelope, 3.5 mm. Actual thread and tolerance class pending.
   ring-=oriented(cylinder(1.28,4.99,8.51)+female_tool)
   track=sector(6.4,7.8,-limit-6,limit+6,8.9,11.1);ring-=oriented(track)
   # Printed fork faces are broad annuli; steel axle journals run in the bore.
   bossfork=(cylinder(8,11.5,12.5)+cylinder(6,12.5,14.5))-cylinder(2.08,11.4,14.6)
   ear=sector(6.6,7.6,-6,6,9.0,11.6)
   s+=oriented(bossfork+ear)
   s-=oriented(cylinder(2.08,4.8,14.6))
   for lab,z0,z1 in [('inner_plate',11,11.5),('outer_plate',14.5,15)]:parts[label+'_'+lab]=oriented(cylinder(6,z0,z1)-cylinder(2.12,z0-.1,z1+.1))
   # Two A-series discs in series retain 210 N nominal catalogue force while
   # giving 0.9 mm compressed stack height. Final force is a test variable.
   for j in range(2):parts[label+f'_spring{j}']=oriented(disc_spring(15+j*.45,flip=bool(j%2)))
   parts[label+'_load_washer']=oriented(cylinder(4.5,15.9,16.2)-cylinder(2.12,15.8,16.3))
   # The shoulder length is custom; it is not silently called a catalog screw.
   # Reference neck/core envelopes leave positive thread engagement in the ring.
   bolt=male_thread+cylinder(2,8.5,16.2)+cylinder(3,16.2,19.2)
   # Custom axle head: 2.5 mm across-flats straight hex socket, 1.5 mm deep.
   theta=np.arange(6)*np.pi/3;hexagon=np.c_[np.cos(theta),np.sin(theta)]*(2.5/np.sqrt(3))
   bolt-=md.CrossSection([hexagon]).extrude(1.6).translate([0,0,17.7])
   parts[label+'_shoulder_axle']=oriented(bolt)
   records.append({'label':label,'axis':ax,'side':side,'nominal_stop_deg':[-limit,limit],'friction_annulus_mm':[2.12,6.0],'steel_shoulder_diameter_mm':4.0,'fork_journal_bore_mm':4.16,'thread':'M3 matching reference helices; production tolerance/tapping not qualified','thread_engagement_mm':3.5,'compressed_series_spring_count':2,'spring_catalog_force_point_N':210,'spring_catalog_h_mm':.45,'axial_stack_nominal_mm':{'ring_face':11.0,'inner_plate_end':11.5,'fork_face_end':14.5,'outer_plate_end':15.0,'spring_end':15.9,'load_washer_end':16.2,'bolt_head_end':19.2}})
  if name=='C01':
   # Dedicated unloaded magnet support, since removing molded pins also removes
   # the paper model's pin-supported magnet bridge.
   s+=cylinder(1.2,-17.2-EXTRA,-2.4)+box([-6,-1,-18.3-EXTRA],[6,1,-16.8-EXTRA])
  forks[name]=s
 # Preserve the original nut seats; relieve only their radial clearance where
 # new bosses touched the nut corners. Axial bearing planes do not move.
 for key,t in np.load(G8/'fastened_core/fasteners.npz').items():
  if 'nut' in key:
   nut=from_tri(t);bb=np.array(nut.bounding_box());center=(bb[:3]+bb[3:])/2
   pocket=nut.translate(-center).scale([1.07,1.07,1.0]).translate(center);ring-=pocket
 halves={'C14':ring^box([-40,-40,-30],[40,40,0]),'C15':ring^box([-40,-40,0],[40,40,30])}
 parts={**forks,**halves,**parts};dest=OUT/'face_brake';dest.mkdir(exist_ok=True)
 assert all(s.volume()>0 and s.num_tri()>0 and s.status()==md.Error.NoError for s in parts.values()), 'Empty or invalid modeled part'
 np.savez_compressed(dest/'parts.npz',**{k:tri(s) for k,s in parts.items()})
 for k,s in parts.items():export_stl(dest/(k+'.stl'),tri(s))
 report={'reference_thread_mesh_sha256':sha(thread_file),'extra_fork_extension_each_mm':EXTRA,'source_sha256':sha(CORE),'source_weld_grid_mm':.00001,'generator_sha256':sha(__file__),'records':records,'parts':{k:record(s) for k,s in parts.items()},'ring_material_intent':'machined aluminium, grade/process pending','fork_material_intent':'PA12 candidate; section loads/creep not qualified','pins_material_intent':'steel custom shoulder axles, grade/retention pending','spring_source':'https://www.raleigh-spring.cn/discspring/','force_model':'Two identical discs in series; F does not double. Effective friction interfaces must be measured; free steel plates are not counted as two independent full-torque faces.','physical_tested':False,'manufacturing_released':False,'open':['Thread retention under reversing friction torque','Split-ring preload and loaded distortion','Friction/hand-force window','Assembly and tool paths','Production tolerances','Bend-axis wiring','Full torso and arm']}
 save('face_brake/build.json',report);print(json.dumps({k:record(s) for k,s in forks.items()},indent=2));print('parts',len(parts),'ring solids',[(k,len(s.decompose())) for k,s in halves.items()],flush=True)
if __name__=='__main__':main()






