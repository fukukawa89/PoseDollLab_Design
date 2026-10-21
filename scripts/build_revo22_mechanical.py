"""O22 SOP8 cassette fit from frozen O20 CAD; no changes to friction or axis centers."""
from pathlib import Path
import sys,json,struct,numpy as np
R=Path(__file__).resolve().parents[1];H=R/'Hardware/PoseDoll44';B=H/'bench/revO22';D=B/'mechanical'
sys.path.insert(0,str(H/'cad/revO20'));import base as b
g=b.g

def plain(x):
 if isinstance(x,np.ndarray):return x.tolist()
 if isinstance(x,np.generic):return x.item()
 raise TypeError(type(x).__name__)
def put(p,o):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,ensure_ascii=False,indent=2,default=plain)+'\n',encoding='utf-8')
def stl(path,s):
 t=g.tri(s);out=bytearray(b'O22 engineering candidate'.ljust(80,b' '))+struct.pack('<I',len(t))
 for face in t:
  n=np.cross(face[1]-face[0],face[2]-face[0]);norm=np.linalg.norm(n);n=n/norm if norm else n
  out.extend(struct.pack('<12fH',*n,*face.ravel(),0))
 path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(out)
def baseline():
 cache=R/'.local/o22_o20_baseline.npz';meta=R/'.local/o22_o20_meta.json'
 if cache.exists() and meta.exists():
  d=json.loads(meta.read_text());z=np.load(cache);p={k:b.from_tri_exact(z[k]) for k in z.files};return p,d['meta'],d['states']
 p,m,pr,st,prov=b.load_o19();ch=g.read(H/'generated/revO20/changes.json')
 for k in ch['removed_stock_parts']:p.pop(k);m.pop(k)
 with np.load(H/'generated/revO20/changed_parts.npz') as z:
  for row in ch['replacements']:
   key=row['part']
   for other in row['replaces']:
    if other!=key:p.pop(other,None);m.pop(other,None)
   p[key]=g.move(b.from_tri_exact(z[key]),np.array(m[key]['transform']))
 np.savez_compressed(cache,**{k:g.tri(s) for k,s in p.items()});put(meta,{'meta':m,'states':st})
 return p,m,st

def electronics():
 face=15.95
 # Conservative package envelopes include solder stand-off. Magnet-facing components.
 out={'pcb':b.box([-6,-5,face],[6,5,face+1]),
 'SOP8_max':b.box([-3.1,-2.55,face-1.85],[3.1,2.55,face]),
 'C1':b.box([-.8,-4.3,face-1],[.8,-3.5,face]),
 'C2':b.box([4.2,-.8,face-1],[5.2,.8,face]),
 'R1':b.box([-5.05,1.3,face-.7],[-4.25,2.9,face]),
 'R2':b.box([-5.05,-3.3,face-.7],[-4.25,-1.7,face]),
 'wire_solder':b.box([-3.2,3.5,face-.7],[3.2,4.65,face])}
 return out

def revised(s):
 # Move only the PCB cradle and rail region. Preserve the O11 M3 mast datum.
 cut=b.box([-7.3,-6.2,13.54],[7.3,6.26,20]);upper=s^cut
 q=(s-cut)+upper.translate([0,0,-.545])
 # Factory bonded flexible boot at the PCB edge, plus a tie on the adjacent
 # fixed bone, replaces the projecting tray. No extra rigid collision envelope.
 q-=b.box([-8,-6.25,0],[8,6.25,13.70])
 # Relieve both outer rear corners; retain the other 8 mm of each PCB rail.
 for x0,x1 in [(5.4,7.4),(-7.4,-5.4)]:q-=b.box([x0,3.95,14.35],[x1,6.4,17.1])
 return q

def main():
 p,m,st=baseline();rows=[];meshes={};components=electronics()
 services=[v for v in g.read(H/'generated/revO17/changes.json')['replacements'] if v['kind']=='sensor_cassette']
 for row in services:
  key=row['part'];A=np.array(row['local_service_frame']);s=g.move(p[key],np.linalg.inv(A));q=revised(s)
  pcba={k:float((q^(g.pose(v,np.diag([-1,1,1])) if np.linalg.det(A[:3,:3])<0 else v)).volume()) for k,v in components.items()}
  rec=g.mesh_record(q);rows.append({'part':key,'service_frame':A,'owner':m[key],**rec,'component_overlap_mm3':pcba,'old_volume_mm3':float(s.volume())})
  meshes[key]=g.tri(q)
  stl(D/'stl'/(key.replace('/','__')+'.stl'),q)
 # Twelve finite-twist end-axis PCBs use split cases and two existing screw clips.
 # Derive an analytic sensor-facing frame from the known PCB/magnet centerline.
 endrows=[];endmeshes={};endwork=p.copy()
 for pcbkey in [k for k in p if k.endswith(('P_sensor_PCB','D_sensor_PCB'))]:
  pre=pcbkey[:-len('sensor_PCB')];Aowner=np.array(m[pcbkey]['transform'])
  board=g.move(p[pcbkey],np.linalg.inv(Aowner));mag=g.move(p[pre+'magnet'],np.linalg.inv(Aowner))
  cb=np.mean(np.array(board.bounding_box()).reshape(2,3),axis=0);cm=np.mean(np.array(mag.bounding_box()).reshape(2,3),axis=0)
  Z=cb-cm;Z/=np.linalg.norm(Z);X=np.array([1.,0,0]);X-=Z*(X@Z);X/=np.linalg.norm(X);Y=np.cross(Z,X)
  A=Aowner@g.homogeneous(np.c_[X,Y,Z],cb-Z*(16.495+.5));I=np.linalg.inv(A)
  # Adjacent printed owner parts can include an integrated half in a body frame.
  focus={k:g.move(v,I) for k,v in endwork.items() if not m[k].get('sku') and k not in meshes}
  holdercut=b.box([-7.3,-6.2,14.9],[7.3,6.25,18.6]);changed=[];assembled={}
  for k,shape in focus.items():
   if (shape^holdercut).volume()<1e-5:continue
   if 'pcb_clip_' in k:
    # Preserve screw land; extend underside only at the PCB retaining nose.
    nose=shape^b.box([-7.3,-2,17.49],[7.3,2,20]);q=shape+nose.translate([0,0,-.545])
   else:
    region=shape^holdercut;q=(shape-holdercut)+region.translate([0,0,-.545])
    # Factory wires exit through +Y; no user soldering.
    q-=b.box([-3.4,3.5,14.8],[3.4,7,16.3])
   if g.solid_count(q)!=1:raise ValueError(('disconnected end holder',pcbkey,k))
   endmeshes[k]=g.tri(g.move(q,np.linalg.inv(np.array(m[k]['transform']))@A));changed.append(k);assembled[k]=q;endwork[k]=g.move(q,A)
   stl(D/'stl'/(k.replace('/','__')+'.stl'),g.move(q,np.linalg.inv(np.array(m[k]['transform']))@A))
  # Check electronics against all new and inherited nearby shapes.
  checks={}
  for k,shape in focus.items():
   shape=assembled.get(k,shape)
   for ek,ev in components.items():
    vol=float((shape^(g.pose(ev,np.diag([-1,1,1])) if np.linalg.det(A[:3,:3])<0 else ev)).volume())
    if vol>1e-4:checks[k+'|'+ek]=vol
  endrows.append({'pcb':pcbkey,'service_frame':A,'changed_parts':changed,'fit_overlaps_mm3':checks})
 # Recheck all axes after shared pelvis-frame edits have accumulated.
 for row in endrows:
  I=np.linalg.inv(row['service_frame']);checks={}
  for k,shape in endwork.items():
   if m[k].get('sku') or k in meshes:continue
   shape=g.move(shape,I)
   for ek,ev in components.items():
    vol=float((shape^(g.pose(ev,np.diag([-1,1,1])) if np.linalg.det(np.array(row['service_frame'])[:3,:3])<0 else ev)).volume())
    if vol>1e-4:checks[k+'|'+ek]=vol
  row['fit_overlaps_mm3']=checks
 np.savez_compressed(D/'end_axis_parts.npz',**endmeshes)
 put(D/'end_axis_fit.json',{'axes':endrows,'count':len(endrows),'failures':[r for r in endrows if r['fit_overlaps_mm3']],'physical_test':False})
 print('END AXES',len(endrows),'FAIL',[(r['pcb'],r['fit_overlaps_mm3']) for r in endrows if r['fit_overlaps_mm3']],flush=True)
 np.savez_compressed(D/'sensor_cassettes.npz',**meshes)
 for k,v in components.items():stl(D/'section'/f'{k}.stl',v)
 report={'schema':'POSEDOLL-O22-MECHANICAL/1','physical_test':False,'friction_geometry_changed':False,'axis_centers_changed':False,
 'sensor_face_mm':15.95,'board_thickness_mm':1,'magnet_top_mm':12.9,'mounted_package_height_mm':[1.50,1.85],
 'pcb_location_tolerance_mm':.10,'magnet_height_tolerance_mm':.10,'worst_gap_mm':[1.0,1.75],
 'wire_od_max_mm':.70,'strain_relief':'Factory bonded flexible boot within wire_solder envelope; external loop anchored to fixed bone with 2.5mm tie' ,'cassettes':rows,
 'fit_failures':[r['part'] for r in rows if r['components']!=1 or max(r['component_overlap_mm3'].values())>1e-4]}
 put(D/'sensor_fit.json',report);print('CASSETTES',len(rows),'FAIL',report['fit_failures'],flush=True)
if __name__=='__main__':main()
