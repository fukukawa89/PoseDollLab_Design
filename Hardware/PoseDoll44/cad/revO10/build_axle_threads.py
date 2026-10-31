"""Phase-invariant polygonal M3 reference helices, not production ISO threads.
Sweep (r,z) sections explicitly in cylindrical coordinates. Changing helix
length cannot change the phase of the existing turns. 1 degree facet spacing,
independent Pappus volume and actual helical insertion checks are recorded.
"""
from solid_ops import *
import math

def helical(points,z0,height,pitch=.5,angle_step_deg=1.):
 profile=np.array(points,float);n=int(round(height/pitch*360/angle_step_deg));theta=np.linspace(0,height/pitch*2*np.pi,n+1);r=profile[:,0]
 vertices=np.stack((np.cos(theta)[:,None]*r,np.sin(theta)[:,None]*r,np.broadcast_to(profile[:,1],(n+1,len(r)))+z0+theta[:,None]*pitch/(2*np.pi)),axis=2).reshape(-1,3)
 faces=[];k=len(r)
 for i in range(n):
  for j in range(k):
   a=i*k+j;b=i*k+(j+1)%k;c=(i+1)*k+(j+1)%k;d=(i+1)*k+j;faces.extend([[a,b,c],[a,c,d]])
 for j in range(1,k-1):faces.append([0,j+1,j]);faces.append([n*k,n*k+j,n*k+j+1])
 t=vertices[np.array(faces)];volume=np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum()/6
 if volume<0:t=t[:,::-1]
 s=from_tri(t);following=np.roll(profile,-1,axis=0);cross=profile[:,0]*following[:,1]-profile[:,1]*following[:,0];area=abs(cross.sum())/2;centroid=((profile[:,0]+np.roll(profile[:,0],-1))*cross).sum()/(3*cross.sum());expected=2*np.pi*centroid*area*height/pitch
 assert s.volume()>0 and abs(s.volume()/expected-1)<.001
 return s,{'pappus_expected_mm3':expected,'mesh_volume_mm3':s.volume(),'relative_difference':s.volume()/expected-1,'facet_angle_step_deg':angle_step_deg}

def main():
 malehelix,a=helical([(1.20,-.206),(1.5,-.033),(1.5,.033),(1.20,.206)],5.25,3)
 cutter,b=helical([(1.20,-.249),(1.55,-.048),(1.55,.048),(1.20,.249)],5.25,4)
 male=malehelix+cylinder(1.215,5,8.5);holder=cylinder(4,5,8.5)-cylinder(1.28,4.9,8.6)-cutter
 nominal=(male^holder).volume();assert nominal<1e-6,nominal
 axial=[{'axial_translation_mm':d,'intersection_mm3':(male.translate([0,0,d])^holder).volume()} for d in (-.15,.15)];assert all(r['intersection_mm3']>.05 for r in axial)
 moves=[]
 for d in np.linspace(0,3.5,29):
  moved=pose(male,rot(2,d*720),[0,0,d]);v=(moved^holder).volume();moves.append({'outward_mm':float(d),'rotation_deg':float(d*720),'intersection_mm3':v});assert v<1e-4,moves[-1]
 dest=OUT/'face_brake';np.savez_compressed(dest/'threads.npz',male=tri(male),cutter=tri(cutter));export_stl(dest/'M3_male_reference.stl',tri(male))
 save('face_brake/threads.json',{'pitch_mm':.5,'nominal_engagement_mm':3.5,'full_male_helix_height_mm':3,'female_cut_helix_height_mm':4,'nominal_intersection_mm3':nominal,'axial_escape_checks':axial,'helical_withdrawal':moves,'volume_guards':[a,b],'generator_sha256':sha(__file__),'method':'Explicit cylindrical section sweep, angle phase independent of total helix length. Female cutter continues beyond mouth. Reference mesh geometry, not thread-fit-class or manufacturing approval.','rejected_previous_method':'Frenet CAD pipe failed the newly added withdrawal/length-invariance checks; old STEP companions are diagnostic files in rejected/.','manufacturing_released':False});print('THREAD PASS',nominal,max(r['intersection_mm3'] for r in moves),axial)
if __name__=='__main__':main()

