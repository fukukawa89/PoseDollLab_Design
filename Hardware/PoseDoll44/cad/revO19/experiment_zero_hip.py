from base import *
from importlib.util import spec_from_file_location,module_from_spec

def cap_recipe():
 cavity=hexagon(5.8,-8.65,-6.05)+cyl(4.65,-6.15,-5.3)+cyl(1.7,-10.6,-3.5)+cyl(2.125,-4.4,-2.)
 s=box([-14,-9,-10.5],[14,9,-2.5])-cavity
 for x in (-9,9):s-=pose(cyl(1.7,-12,14)+hexagon(5.8,-9.1,-6.59),rot(0,-90),[x,0,-6.5])
 return s-box([-3.5,0,-8.7],[3.5,9.2,-6.05])-box([-4.7,0,-6.25],[4.7,9.2,-5.3])

def tube(points,r=5):
 shape=md.Manifold()
 for a,b in zip(points,points[1:]):
  shape+=beam(a,b,r)+md.Manifold.sphere(r,24).translate(a)+md.Manifold.sphere(r,24).translate(b)
 return shape

def worldpoint(M,v):return M[:3,:3]@np.asarray(v)+M[:3,3]

def make():
 p,m,pr,st,prov=load_o18();old=p.copy();oldm={k:v.copy() for k,v in m.items()}
 choices=g.read(OUT/'hip_mount_refined.json');ov=next(r['overrides'] for r in choices if r['tilt']==60 and r['phase']==90 and r['offset']==0)
 p,transforms,states,fail,pr=position(p,m,{},ov);assert not fail
 _,mm,_,_,_=L.build('quinn',{},overrides=ov,geometry=False);T,A=L.fk(pr,{})
 for k in m:m[k]={**m[k],'transform':transforms[k]}
 libs=L.libraries();byid={s['id']:s for s in states};new={};paths={}
 def part(key):
  module,local=key.split('/',1);shape=libs[byid[module]['kind']][0][local]
  return g.move(shape,mm[key]['transform'])
 def line(body,ends,polylines):
  s=md.Manifold.batch_boolean(ends,md.OpType.Add)+tube(polylines);s=s.simplify(1e-4)
  print('FRAME',body,'components',solid_count(s),'bbox',s.bounding_box(),flush=True)
  new['frame/'+body]=s;paths[body]=np.array(polylines).tolist()
 for side in ('l','r'):
  hip='thigh_'+side;knee='calf_'+side+'.flex';ankle='foot_'+side
  xy=A[knee]['origin'][:2];z=A[knee]['origin'][2]
  # Distal hip half and knee fixed housing remain their measured local geometry.
  D=part(hip+'/D_case_minus');K=g.move(cap_recipe(),mm[knee+'/base_sensor_half']['transform'])
  start=worldpoint(mm[hip+'/D_case_minus']['transform'],[0,13.4,37.9]);end=worldpoint(mm[knee+'/base_sensor_half']['transform'],[-12,-4,-8])
  line(hip,[D,K],[start,start+[0,0,-8],[*xy,201],[*xy,z+24],end+[0,0,8],end])
  # Mid-span lies on the actual knee-to-ankle line.
  C=part(ankle+'/C02');K=part(knee+'/lever_cup')
  start=worldpoint(mm[ankle+'/C02']['transform'],[0,0,33]);end=worldpoint(mm[knee+'/lever_cup']['transform'],[12.5,0,2.5])
  line('calf_'+side,[C,K],[start,[*xy,start[2]+9],[*xy,z-25],end])
 # Pelvis connects unchanged waist and new hip cases. Rear bridge avoids the leg shafts.
 ends=[part('waist/P_case_minus'),part('thigh_l/P_case_minus'),part('thigh_r/P_case_minus')]
 ports=[worldpoint(mm[k]['transform'],[0,-13.4,-38.4]) for k in ('waist/P_case_minus','thigh_l/P_case_minus','thigh_r/P_case_minus')]
 a,b,c=ports
 s=md.Manifold.batch_boolean(ends,md.OpType.Add)
 polylines=[[a,[-28,25,320],[-28,0,293],[-28,b[1],b[2]],b],[[-28,b[1],b[2]],[-28,c[1],c[2]],c]]
 for points in polylines:s+=tube(points)
 new['frame/pelvis']=s.simplify(1e-4);paths['pelvis']=[[np.asarray(v).tolist() for v in line] for line in polylines]
 for k,s in new.items():p[k]=s
 found=overlaps(p,set(new),same_body_meta=None)
 g.write(OUT/'trial_carriers.json',{'overrides':ov,'paths_neutral_world_mm':paths,'hits':found,'mesh':{k:mesh_record(v) for k,v in new.items()}})
 np.savez_compressed(OUT/'trial_carriers.npz',**{k:tri(g.move(s,np.linalg.inv(transforms[k]))) for k,s in new.items()})
 print('TRIAL',len(found),'hits',found[:15],flush=True)
 return p,m,new,ov,paths
if __name__=='__main__':make()
