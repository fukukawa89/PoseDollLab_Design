"""One plate containing every T5 printable item, with unchanged contact faces."""
from arm_kit import *
import printing as p
import random,zipfile,xml.etree.ElementTree as ET
p.OUT=OUT;p.REVISION=REVISION;p.WORK=ROOT/'output/o24ct5-combined-slicing'

def pack(rows):
 gap=8.;rng=random.Random(241024)
 for attempt in range(600):
  seq=sorted(rows,key=lambda r:-(max(r['size'][:2]) if attempt==0 else np.prod(r['size'][:2]) if attempt==1 else np.prod(r['size'][:2])*rng.uniform(.4,2.5)))
  free=[(0.,0.,172.,172.)];placed=[]
  for row in seq:
   choices=[]
   for x,y,w,h in free:
    for angle in [0,90]:
     ww,hh=row['size'][:2] if angle==0 else row['size'][:2][::-1];ww+=gap;hh+=gap
     if ww<=w+1e-6 and hh<=h+1e-6:choices.append(((min(w-ww,h-hh),max(w-ww,h-hh),y,x),x,y,ww,hh,angle))
   if not choices:break
   _,x,y,w,h,angle=min(choices);placed.append((row,x+8,y+8,angle))
   rect=[]
   for fx,fy,fw,fh in free:
    if x>=fx+fw-1e-6 or x+w<=fx+1e-6 or y>=fy+fh-1e-6 or y+h<=fy+1e-6:rect.append((fx,fy,fw,fh));continue
    if x>fx:rect.append((fx,fy,x-fx,fh))
    if x+w<fx+fw:rect.append((x+w,fy,fx+fw-x-w,fh))
    if y>fy:rect.append((fx,fy,fw,y-fy))
    if y+h<fy+fh:rect.append((fx,y+h,fw,fy+fh-y-h))
   free=[a for i,a in enumerate(rect) if not any(i!=j and b[0]<=a[0]+1e-6 and b[1]<=a[1]+1e-6 and b[0]+b[2]>=a[0]+a[2]-1e-6 and b[1]+b[3]>=a[1]+a[3]-1e-6 and (b!=a or j<i) for j,b in enumerate(rect))]
  if len(placed)==len(rows):return placed
 raise RuntimeError('No single-plate layout found')

def main():
 rows=[dict(r,size=(np.array(r['print_bounds_mm'][1])-r['print_bounds_mm'][0]).tolist()) for r in json.loads((OUT/'assembly.json').read_text('utf8'))['parts'] if r['printable']]
 placed=pack(rows);plate=dict(id='ALL_H_R_W_T5',items=[],optional=False,replacement=False)
 for r,x,y,angle in placed:plate['items'].append(dict(id=r['id'],stl=r['stl'],offset_mm=[x,y,0],stl_sha256=r['stl_sha256'],z_rotation_deg=angle))
 path=p.project(plate)
 with zipfile.ZipFile(path) as z:files={name:z.read(name) for name in z.namelist()}
 root=ET.fromstring(files['3D/3dmodel.model'])
 for item,entry in zip(plate['items'],root.find(p.Q+'build')):
  m=trimesh.load(OUT/item['stl'],process=True);M=rot(Z,item['z_rotation_deg']);m.apply_transform(M);M[:3,3]=np.array(item['offset_mm'])-m.bounds[0];entry.set('transform',' '.join(f'{x:.12g}' for x in M[:3,:].T.flat));item['transform']=M.tolist();item['bounds_mm']=np.r_[m.bounds[0]+M[:3,3],m.bounds[1]+M[:3,3]].tolist()
 files['3D/3dmodel.model']=p.xb(root)
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
  for name,blob in files.items():z.writestr(name,blob)
 plate['sha256']=sha(path)
 # The checks use transformed bounds and exact embedded vertex data.
 assert len(plate['items'])==14
 for a1 in plate['items']:
  b=np.array(a1['bounds_mm']).reshape(2,3);assert min(b[0,:2])>=7.999 and max(b[1,:2])<=172.001 and abs(b[0,2])<1e-6
  for b1 in plate['items']:
   if a1['id']==b1['id']:continue
   bb=np.array(b1['bounds_mm']).reshape(2,3);assert np.any(b[0,:2]>=bb[1,:2]+7.999) or np.any(bb[0,:2]>=b[1,:2]+7.999)
 put(OUT/'printing/combined_plate.json',dict(plates=[plate],minimum_print_files=1,printer='A1 mini 180×180 mm / 0.4 mm',model_gap_mm=8,bed_edge_mm=8,includes='9 joint parts + 4 removable fixtures + 1 optional fit coupon; one each',unchanged_STLs=True,orientation='Original print contact faces; in-plane Z rotation only'))
 print('PACK: 14 objects on one plate',flush=True)
 result=p.run(plate)
 put(OUT/'verification/combined_printing.json',dict(passed=result['passed'],geometry_sha256=sha(OUT/'assembly_meshes.npz'),plate=result,model_gap_mm=8,unchanged_STL_hashes=all(sha(OUT/r['stl'])==r['stl_sha256'] for r in rows),gcode_delivered=False))
 if not result['passed']:raise SystemExit(1)

if __name__=='__main__':main()
