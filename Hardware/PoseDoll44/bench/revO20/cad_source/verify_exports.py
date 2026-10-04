"""Read exported meshes back and check topology, volumes and profile identity."""
from base import *
import struct,zipfile,xml.etree.ElementTree as ET

def stl_tri(path):
 raw=path.read_bytes()
 if raw.startswith(b'solid '):
  return np.array([[float(v) for v in line.split()[1:]] for line in raw.decode('ascii').splitlines() if line.startswith('vertex ')]).reshape(-1,3,3)
 n=struct.unpack_from('<I',raw,80)[0];assert len(raw)==84+50*n
 a=np.frombuffer(raw[84:],dtype=np.dtype([('normal','<f4',(3,)),('vertices','<f4',(3,3)),('attr','<u2')]))
 return a['vertices'].astype(float)

def topology(t):
 _,ii=np.unique(t.reshape(-1,3),axis=0,return_inverse=True);f=ii.reshape(-1,3)
 e=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);_,n=np.unique(np.sort(e,axis=1),axis=0,return_counts=True)
 return int(np.count_nonzero(n!=2))

def mf_tri(path):
 N='{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}'
 with zipfile.ZipFile(path) as z:r=ET.fromstring(z.read('3D/3dmodel.model'))
 v=np.array([[float(a.attrib[k]) for k in ('x','y','z')] for a in r.findall('.//'+N+'vertex')]);f=np.array([[int(a.attrib[k]) for k in ('v1','v2','v3')] for a in r.findall('.//'+N+'triangle')]);return v[f]

def main():
 manifest=g.read(BENCH/'print_batch/manifest.json');records=[];fail=[]
 for row in manifest['rows']:
  assert g.sha(BENCH/row['stl'])==row['stl_sha256']
  if not row['id'].startswith('W'):continue
  path=BENCH/row['stl'];t=stl_tri(path);u=mf_tri(path.with_suffix('.3mf'));e=topology(t);s=from_tri_exact(t);f=from_tri_exact(u)
  rec={'id':row['id'],'stl_nonmanifold_edges':e,'stl_components':solid_count(s),'stl_status':str(s.status()),'three_mf_components':solid_count(f),'volume_delta_mm3':abs(float(s.volume()-f.volume())),'stl_void_shells':mesh_record(s)['enclosed_void_shells'],'three_mf_void_shells':mesh_record(f)['enclosed_void_shells'],'stl_triangles':len(t),'three_mf_triangles':len(u)}
  records.append(rec)
  if e or solid_count(s)!=1 or solid_count(f)!=1 or rec['stl_void_shells']!=rec['three_mf_void_shells'] or rec['volume_delta_mm3']>.03:fail.append(rec)
  print(rec,flush=True)
 for pid in ():
  t=stl_tri(BENCH/'coupon'/(pid+'.stl'));s=from_tri_exact(t);e=topology(t)
  rec={'id':pid,'stl_nonmanifold_edges':e,'stl_components':solid_count(s),'stl_status':str(s.status())};records.append(rec)
  if e or solid_count(s)!=1:fail.append(rec)
 old=g.read(H/'bench/revO19/profiles/device_profile.json');new=g.read(BENCH/'profiles/device_profile.json')
 fields=['root_transform_mm','joints','fixed_markers','raw_order','raw_limits_deg','neutral_raw_deg','transport','capture_policy']
 assert all(old[k]==new[k] for k in fields)
 proc=g.read(BENCH/'procurement.json');op=g.read(H/'bench/revO19/procurement.json');counts={r['sku']:r['net_quantity'] for r in proc['characters'][0]['rows']}
 assert all(counts.get(r['sku'],0)==r['net_quantity']-({'SCREW_M3_L20':4,'NUT_M3':4}.get(r['sku'],0)) for r in op['characters'][0]['rows'])
 assert manifest['print_pieces']==186 and manifest['print_types']==115
 g.write(OUT/'export_verification.json',{'status':'PASS' if not fail else 'FAIL','new_mesh_checks':records,'failures':fail,'profile_identical_fields':fields,'print_types':115,'print_pieces':186,'all_print_STL_hashes_checked':True,'stock_delta_checked':{'SCREW_M3_L20':-4,'NUT_M3':-4},'physical_tested':False})
 if fail:raise SystemExit(1)

if __name__=='__main__':main()
