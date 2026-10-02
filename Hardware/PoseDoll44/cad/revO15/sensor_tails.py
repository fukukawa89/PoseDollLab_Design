"""Real connector-facing 20mm FFC pigtail fold, with manufacturer stiffener room.
Formed once and strain-relieved; never use this FFC as the moving joint cable.
"""
from common import *
from layout_fullbody import libraries,build,config

def pigtail(radius=3.,length=20.):
 # Axis X is 3.5mm width, Y insertion, Z outward board normal.
 y0=1.575;yb=3.2;z=.4;remaining=length-2.15-(yb-y0)-math.pi*radius
 if remaining<3.5:raise ValueError('No room for 3.5mm end stiffener')
 th=np.linspace(0,np.pi,41);center=np.c_[yb+radius*np.sin(th),z+radius*(1-np.cos(th))];normal=np.c_[-np.sin(th),np.cos(th)];upper=center+.1*normal;lower=center-.1*normal
 contour=np.r_[[[y0,z+.1]],upper,[[yb-remaining,z+2*radius-.1],[yb-remaining,z+2*radius+.1]],lower[::-1],[[y0,z-.1]]]
 # Build path offset separately at both ends to avoid the reversed normal at180deg.
 A=np.vstack(([y0,z+.1],upper,[yb-remaining,z+2*radius-.1]));B=np.vstack(([y0,z-.1],lower,[yb-remaining,z+2*radius+.1]));contour=np.r_[A,B[::-1]]
 if np.sum(contour[:,0]*np.roll(contour[:,1],-1)-contour[:,1]*np.roll(contour[:,0],-1))<0:contour=contour[::-1]
 s=md.CrossSection([contour]).extrude(3.5);F=np.c_[[0,1,0],[0,0,1],[1,0,0]];s=pose(s,F,[-1.75,0,0]);end=np.array([0,yb-remaining,z+2*radius]);patch=box([-2.5,end[1]-1.5,end[2]-.45],[2.5,end[1]+3.5,end[2]+.45]);return s,patch,end+[0,-1.5,0]

def local_ports(char):
 kinds={r['id']:r['kind'] for r in config(char)[1]};_,meta,_,_,_=build(char,{},geometry=False);ports={}
 for k,m in meta.items():
  if m['sku']!='AS5048A_MINI_PCBA':continue
  mod,key=k.split('/',1);pre=key[:-len('sensor_PCB')];pp,owners,skus=libraries()[kinds[mod]];board=pp[key];bb=np.array(board.bounding_box());center=(bb[:3]+bb[3:])/2
  cb=np.array(pp[pre+'sensor_FPC_connector'].bounding_box());cc=(cb[:3]+cb[3:])/2;n=(cc-center)/np.linalg.norm(cc-center);pb=np.array(pp[pre+'passive_3'].bounding_box());offset=(pb[:3]+pb[3:])/2-center
  ix=int(np.argmax(bb[3:]-bb[:3]));dims=np.argsort(bb[3:]-bb[:3]);iy=int(dims[1]);x=np.eye(3)[ix]*np.sign(offset[ix]);y=np.eye(3)[iy]*np.sign(offset[iy]);F=np.c_[x,y,n]
  if abs(np.linalg.det(F)-1)>1e-5:raise ValueError(('PCB basis',k,F))
  top=center+n*.5;ports[k]={'basis':F,'board_top_center':top,'module':mod,'body':m['body']}
 return ports

if __name__=='__main__':
 s,p,e=pigtail();print('FFC',mesh_record(s),'transition',mesh_record(p),'end',e)
