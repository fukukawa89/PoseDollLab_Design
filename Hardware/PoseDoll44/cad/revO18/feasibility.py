from base import *
from layout_fullbody import libraries
from common import hexagon,washer
p,m,pr,st,prov=load_o17()
pp,owners,sku=libraries()['hinge']
report=[]
for state in st:
 if state['kind']!='hinge':continue
 name=state['id'];key=name+'/base_service_half';frame='frame/'+state['parent'];A=m[key]['transform'];I=np.linalg.inv(A)
 old=g.move(p[frame],I)+g.move(p[key],I)
 # A new continuous housing is inserted over the former Y=0 split. It stays
 # in the nominal 28x18x8 housing bounds and preserves the load-bearing bore.
 base=box([-14,-9,-10.5],[14,9,-2.5])
 cavity=hexagon(5.8,-8.65,-6.05)+cyl(4.65,-6.15,-5.3)+cyl(1.7,-10.6,-3.5)+cyl(2.125,-4.4,-2.0)
 base-=cavity
 for x in (-9,9):base-=pose(cyl(1.7,-12,14)+hexagon(5.8,-9.1,-6.59),rot(0,-90),[x,0,-6.5])
 s=(old+base).simplify(1e-4)
 # Assemble nut and reaction washer laterally, BEFORE the shoulder screw.
 # +Y is the former service-half side, away from the sensor post.
 cut=box([-3.5,0,-8.7],[3.5,10,-6.0])+box([-4.7,0,-6.2],[4.7,10,-5.15])
 s-=cut
 samples=[]
 for part in ('M3_nut','M3_reaction_washer'):
  samples.append(max(float((s^pp[part].translate([0,t,0])).volume()) for t in np.linspace(0,16,65)))
 oldvol=float(old.volume());add=max(0,float((s-old).volume()));removed=max(0,float((old-s).volume()))
 report.append({'module':name,'body':frame,'components':solid_count(s),'status':str(s.status()),'added':add,'removed':removed,'slide':samples,'volume':s.volume()})
 print(report[-1],flush=True)
# Test whether simple neutral-pose clearance subtraction can keep the pelvis connected.
pn,Ms=position(p,m,{})
F=pn['frame/pelvis'];colliders={k:v for k,v in pn.items() if m[k]['body'].startswith(('upperarm_','elbow_','forearm_','hand_'))}
bb=np.array(F.bounding_box());hit=[]
for k,v in colliders.items():
 b=np.array(v.bounding_box())
 if np.any(np.minimum(bb[3:],b[3:])<=np.maximum(bb[:3],b[:3])):continue
 overlap=(F^v).volume()
 if overlap>.001:hit.append(k)
for k in hit:F-=colliders[k]
print('pelvis neutral subtraction',len(hit),solid_count(F),float(F.volume()),float(pn['frame/pelvis'].volume()),flush=True)
g.write(OUT/'feasibility.json',{'hinge_housings':report,'pelvis_neutral_cut':{'colliders':hit,'components_after':solid_count(F),'remaining_volume':float(F.volume()),'original_volume':float(pn['frame/pelvis'].volume())}})
