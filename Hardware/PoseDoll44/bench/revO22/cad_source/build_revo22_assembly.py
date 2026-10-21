"""Actual O22 geometry and raw-axis posing, using frozen O20 mechanics."""
from pathlib import Path
import sys,json,copy,numpy as np
import build_revo22_mechanical as b
R=b.R;H=b.H;B=b.B;D=b.D;g=b.g
sys.path.insert(0,str(B/'source'));from device import forward
profile=g.read(B/'profiles/device_profile.json')

def hrot(Q):A=np.eye(4);A[:3,:3]=Q;return A

def owners(raw):
 frames=forward(profile,raw);out={}
 for j in profile['joints']:
  q=[raw[x] for x in j['raw_ids']];kind=j['kind'];mount=frames[j['parent']]@np.array(j['parent_to_mount_mm'])
  if kind in ['tut','wide_tut']:fs=b.b.L.tut.frames(q)
  elif kind=='three_axis':fs=b.b.L.three_axis.frames(q)
  elif kind=='ankle_core':fs={'C02':np.eye(3),'ring':b.b.rot(1,-q[1]),'C01':b.b.rot(1,-q[1])@b.b.rot(0,q[0])}
  elif kind=='hinge':fs={'parent':np.eye(3),'child':b.b.rot(2,q[0])}
  else:raise ValueError(kind)
  out.update({(j['id'],k):mount@hrot(v) for k,v in fs.items()})
 return frames,out

def model():
 p,m,st=b.baseline();old=p.copy();original_meta=m.copy();base_raw={raw:angle for state in st for raw,angle in zip(next(j for j in profile['joints'] if j['id']==state['id'])['raw_ids'],state['angles_deg'])}
 f0,o0=owners(base_raw);changed={};service={};e=g.read(D/'sensor_fit.json');end=g.read(D/'end_axis_fit.json')
 with np.load(D/'sensor_cassettes.npz') as z:
  for row in e['cassettes']:
   k=row['part'];A=np.array(row['service_frame']);changed[k]=g.move(b.b.from_tri_exact(z[k]),A);service[k.replace('sensor_cassette','sensor_PCB')]=(A,k)
 with np.load(D/'end_axis_parts.npz') as z:
  for k,t in z.items():changed[k]=g.move(b.b.from_tri_exact(t),np.array(m[k]['transform']))
 for row in end['axes']:service[row['pcb']]=(np.array(row['service_frame']),row['pcb'])
 assert len(service)==46
 removed=[k for k in p if k.startswith('tail/') or k.startswith('accessory/chest/') or m[k].get('sku') in ['AS5048A_MINI_PCBA','PCBA_INCLUDED']]
 for k in removed:p.pop(k);m.pop(k)
 p.update(changed)
 # Back housing: native PCB x runs down, y runs across; connectors face outward.
 C=g.homogeneous(np.c_[[0,0,-1],[0,-1,0],[-1,0,0]],[-65,47,385.3748525936461])
 floor=b.b.box([-3,-3,-.3],[83,97,2]);wall=b.b.box([-3,-3,1],[83,97,25])-b.b.box([-1,-1,.9],[81,95,25.1])
 # Accessible opposite side entries. The rear is a removable ventilated cover.
 wall-=b.b.box([8,-4,8],[32,0,22])+b.b.box([40,94,8],[77,98,23])
 # PCB holes: (3,3),(77,3),(3,91),(77,91), unchanged four M2 screws.
 posts=b.b.md.Manifold()
 for x,y in [(3,3),(77,3),(3,91),(77,91)]:
  posts+=(b.b.cyl(2.8,1.9,5)-b.b.cyl(.85,.5,10)).translate([x,y,0])
 shell=floor+wall+posts
 chest=p['frame/chest']-b.b.box([-200,-100,280],[-64.9,100,430]);chest+=g.move(shell,C)
 if g.solid_count(chest)!=1:raise ValueError(('housing frame disconnected',g.solid_count(chest)))
 changed['frame/chest']=chest;p['frame/chest']=chest
 lid=b.b.box([-3,-3,25],[83,97,27])
 for x in range(8,78,10):
  for y in range(8,93,10):lid-=b.b.cyl(2.4,24,28).translate([x,y,0])
 # Side tie-through retention is mechanical and reversible; cover has no live loading function.
 for x in [10,70]:
  for y in [-2,93]:lid-=b.b.box([x,y,24.9],[x+3,y+3,27.1])
 def add(k,s,A,owner_meta,sku=None):
  mm=copy.deepcopy(owner_meta);mm.update(sku=sku,transform=A.tolist());p[k]=g.move(s,A);m[k]=mm
 add('o22/controller_lid',lid,C,m['frame/chest']);changed['o22/controller_lid']=p['o22/controller_lid']
 for i,(x,y) in enumerate([(3,3),(77,3),(3,91),(77,91)]):add('o22/carrier_screw_'+str(i),b.b.screw(2,6,3.8,1.5,6.6).translate([x,y,0]),C,m['frame/chest'],'SELF_TAP_M2_L6')
 add('o22/carrier_pcb',b.b.box([0,0,5],[80,94,6.6]),C,m['frame/chest'],'O22_4L_CARRIER')
 comps=g.read(B/'electronics/carrier/components.json')
 for c in comps:
  ref=c['ref']
  if not c.get('fp'):continue
  x,y=c['pcb'];x-=75;y-=75
  if ref.startswith('J') and ref not in ['J1','J2','J3']:
   s=b.b.box([x-3.5,y-2.2,6.6],[x+3.5,y+2.2,11]);add('o22/'+ref,s,C,m['frame/chest'],'SH5_CONNECTOR_ENVELOPE')
  elif ref.startswith('U'):
   s=b.b.box([x-3.2,y-4.2,6.6],[x+3.2,y+4.2,7.8]);add('o22/'+ref,s,C,m['frame/chest'],'IC_ENVELOPE')
 # XIAO: actual board footprint between two 15.24mm spaced headers; module antenna extends above.
 add('o22/xiao',b.b.box([25-8.89,13-10.5,10.6],[25+8.89,13+10.5,12.2]),C,m['frame/chest'],'XIAO_ESP32S3_ENVELOPE')
 add('o22/xiao_usb',b.b.box([25-4.5,2.5,12.2],[25+4.5,10,15.66]),C,m['frame/chest'],'USB_SOCKET_ENVELOPE')
 for key,(A,anchor) in service.items():
  owner=anchor if anchor in m else key
  meta=copy.deepcopy((m if owner in m else original_meta)[owner])
  E=A.copy()
  if np.linalg.det(E[:3,:3])<0:E[:3,0]*=-1
  assert np.linalg.det(E[:3,:3])>.999999
  for name,shape in b.electronics().items():add(key+'/'+name,shape,E,meta,'MT6701_PCBA_ENVELOPE')
 # Save local replacement solids, including the revised chest and lid.
 np.savez_compressed(D/'changed_owner_parts.npz',**{k:g.tri(g.move(v,np.linalg.inv(np.array(m[k]['transform'])))) for k,v in changed.items()})
 b.put(D/'assembly_metadata.json',{'meta':m,'removed_parts':removed,'changed_parts':list(changed),'base_raw':base_raw,'controller_frame':C,'sensor_service_frames':{k:v[0] for k,v in service.items()}})
 return p,m,base_raw,changed,service,C

def pose_parts(p,m,base_raw,raw):
 f0,o0=owners(base_raw);f,o=owners(raw);out={};transforms={}
 for k,shape in p.items():
  mm=m[k]
  if mm['owner']=='rigid_frame':delta=f[mm['body']]@np.linalg.inv(f0[mm['body']])
  else:delta=o[(mm['module'],mm['owner'])]@np.linalg.inv(o0[(mm['module'],mm['owner'])])
  out[k]=g.move(shape,delta);transforms[k]=delta@np.array(mm['transform'])
 return out,transforms,f

def main():
 p,m,raw,changed,service,C=model();preset=g.read(B/'profiles/default_pose.json')['raw_deg'];posed,mat,f=pose_parts(p,m,raw,preset)
 bounds=np.array([s.bounding_box() for s in posed.values()]);lo=bounds[:,:3].min(0);hi=bounds[:,3:].max(0)
 b.put(D/'assembly_summary.json',{'parts':len(p),'changed_prints':len(changed),'height_mm':hi[2]-lo[2],'min_mm':lo,'max_mm':hi,'physical_test':False,'all_46_sensor_envelopes':True,'case_outer_mm':[86,100,27],'case_pcb_mm':[80,94,1.6]})
 for k,s in changed.items():b.stl(D/'stl'/(k.replace('/','__')+'.stl'),g.move(s,np.linalg.inv(np.array(m[k]['transform']))))
 print('ASSEMBLY',len(p),'PRINT CHANGES',len(changed),'HEIGHT',hi[2]-lo[2],flush=True)
if __name__=='__main__':main()
