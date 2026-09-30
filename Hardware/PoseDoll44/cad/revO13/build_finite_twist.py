"""O13 printed finite-twist envelope: shorter rear journal, integral thrust lands.
No custom 0.2 mm thrust shims. Retention geometry only; friction, wear, stiffness,
sensor placement and wire routing are not qualified by this model.
"""
from solid_ops import *
D=rot(0,180)
def housing(lo,hi):
 body=cylinder(12.5,-32.5,-18.8)
 for x in (-9.5,9.5):
  for z in (-30,-21.5):body+=box([x-1.9,-10,z-2],[x+1.9,10,z+2])
 body-=cylinder(6.12,-34,-18)
 body-=cylinder(9.82,-27.9,-24.7)
 body-=sector(9,11.48,lo-6,hi+6,-27.9,-24.7)
 screws={};nuts={};n=0
 for x in (-9.5,9.5):
  for z in (-30,-21.5):
   n+=1;M=rot(0,-90);body-=pose(cylinder(1.1,-12,13),M,[x,0,z])
   screws[f'screw{n}']=pose(cylinder(1,-12,10)+cylinder(1.9,10,12),M,[x,0,z])
   a=np.arange(6)*np.pi/3;nut=md.CrossSection([np.c_[np.cos(a),np.sin(a)]*4/np.sqrt(3)]).extrude(1.6).translate([0,0,-11.6])-cylinder(1.01,-12,-9)
   nuts[f'nut{n}']=pose(nut,M,[x,0,z])
 return {'case_minus':body^box([-30,-30,-40],[30,0,-10]),'case_plus':body^box([-30,0,-40],[30,30,-10]),**screws,**nuts}
def rotor_stub():
 return (cylinder(6,-32.3,-18.3)-cylinder(4.4,-34,-18))+(cylinder(9.6,-27.8,-24.8)-cylinder(4.4,-28,-24))+sector(9.4,11.3,-6,6,-27.8,-24.8)

