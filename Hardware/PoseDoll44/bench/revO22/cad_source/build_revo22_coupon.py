"""Two removable additions to the user's already validated O11 bench.
A short calibration range is intentional; it does not re-test joint friction.
"""
import numpy as np,json
import build_revo22_mechanical as b
from export_print_batch import orient
import print_io17,print_io20
D=b.B/'physical_tests/sensor_coupon';D.mkdir(exist_ok=True)
z=np.load(b.H/'bench/revO11/parts.npz');old={k:b.b.from_tri_exact(v) for k,v in z.items()}
cass=b.b.from_tri_exact(np.load(b.D/'sensor_cassettes.npz')['elbow_l.flex/sensor_cassette']).translate([0,0,14.5])
foot=b.b.box([-27,-19,8.0],[-13,-2,11.0])-b.b.cyl(2.25,8,12).translate([-20,-9,0])
post=b.b.box([-19,-19,10.9],[-13,-13,31]);holder=foot+post+cass
rotor=b.b.box([0,-4,23.4],[100,4,24.9])+b.b.box([90,-6,15.0],[105,6,24.9])
rotor-=b.b.cyl(1.7,14.9,25.1).translate([100,0,0])
rotor+=b.b.cyl(5,23.4,27.6)-b.b.cyl(3.075,24.9,27.7)
mag=b.b.cyl(3,24.9,27.4);elect={k:v.translate([0,0,14.5]) for k,v in b.electronics().items()};reports=[]
for angle in range(0,61,5):
 Q=b.b.rot(2,angle);moving={'rotor':b.g.pose(rotor,Q),'magnet':b.g.pose(mag,Q),'old_lever':b.g.pose(old['printed_lever'],Q)}
 for mk,ms in moving.items():
  for sk,ss in {**{k:v for k,v in old.items() if k!='printed_lever'},'new_holder':holder,**elect}.items():
   v=float((ms^ss).volume())
   if v>1e-4:reports.append({'angle':angle,'moving':mk,'stationary':sk,'volume_mm3':v})
rows=[]
for name,shape in [('sensor_bridge',holder),('magnet_bridge',rotor)]:
 bed,meta=orient(shape);print(name,'COMPONENTS',b.g.solid_count(shape),flush=True)
 if b.g.solid_count(shape)!=1:raise ValueError(name+' disconnected')
 print_io20.stl(D/(name+'.stl'),bed);print_io17.write_3mf(D/(name+'.3mf'),{name:bed});rows.append({'name':name,'bed':meta})
b.put(D/'fit_report.json',{'physical_test':False,'retains_original_O11_parts':True,'friction_modified':False,'sampled_angles_deg':list(range(0,61,5)),'overlaps':reports,'status':'PASS' if not reports else 'NEEDS_CORRECTION','mounting':'Fixed bridge on existing O11 (-20,-9) M4 through-hole with washer/nut; moving bridge at existing x=100 lever M3 hole. Replace fixture mounting bolts with suitable lengths, no extra joint preload.','additional_stock':'M3x25 + M3 nut + 2 washers at lever tip; existing M4 bench clamp length +3.0mm; one D6x2.5 diametric magnet; one O22 PCBA','range_is_fixture_only':[0,60],'print_parts':rows})
print('COUPON',reports,flush=True)
