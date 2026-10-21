"""Distinguish a fastener cavity from merely adjacent assembled hardware."""
import json,sys,math
import numpy as np
from shapely.geometry import Point,LineString,Polygon
from o22f6_holeclear import SRC,WORK,B,H,solid,put,assembly_context
from o22_cross_section_geometry import polygon

def inspect(body,hw):
 mesh=hw.to_mesh64();v=np.asarray(mesh.vert_properties)[:,:3];center=v.mean(0);cov=(v-center).T@(v-center)/len(v);values,vectors=np.linalg.eigh(cov);axis=min(range(3),key=lambda k:abs(math.log(max(values[(k+1)%3],1e-9)/max(values[(k+2)%3],1e-9))))
 z=vectors[:,axis];x=vectors[:,(axis+1)%3];y=np.cross(z,x);rot=np.array([x,y,z]);tr=np.c_[rot,-rot@center];bs=body.transform(tr);hs=hw.transform(tr);bb=hs.bounding_box();accepted=[];tests=[]
 for zz in np.linspace(bb[2]+.03,bb[5]-.03,15):
  hp=polygon(hs.slice(float(zz)));bp=polygon(bs.slice(float(zz)))
  if hp.is_empty or bp.is_empty:continue
  closed=False
  for poly in getattr(bp,'geoms',[bp]):
   for ring in poly.interiors:
    hole=Polygon(ring)
    if hole.covers(Point(0,0))and hole.area<max(9.,hp.area*3.5+3):closed=True
  close=0;distances=[]
  for a in np.arange(0,2*np.pi,np.pi/4):
   ray=LineString([[0,0],[30*math.cos(a),30*math.sin(a)]]);hi=hp.intersection(ray);bi=bp.intersection(ray)
   if hi.is_empty or bi.is_empty:distances.append(None);continue
   coords=[]
   for q in getattr(hi,'geoms',[hi]):
    if hasattr(q,'coords'):coords.extend(q.coords)
   extent=max((math.hypot(*q)for q in coords),default=0);dist=bi.distance(Point(0,0))-extent;distances.append(float(dist));close+=int(-.6<=dist<=.65)
  ok=closed or close>=5
  if ok:accepted.append(float(zz))
  tests.append(dict(z=float(zz),closed_fitted_hole=closed,close_radial_sides=close,accepted=ok))
 return bool(accepted),dict(method='15 axial sections, actual closed cavity area relative to hardware section, or >=5 of 8 close surrounding walls. Nearby exposed hardware alone is not a hole in this part.',axis=z.tolist(),origin=center.tolist(),samples=tests)

def main():
 parts,meta,hw=assembly_context();exports={q['id']:q for q in json.loads((B/'print_batch/manifest.json').read_text())['rows']};results={}
 for fp in sorted((WORK/'initial').glob('*.json')):
  r=json.loads(fp.read_text());pid=r['id'];records=[x for x in r['features']if x['source']=='assembled_fastener'];d=json.loads((SRC/f'design/{pid}.json').read_text());n=np.load(SRC/f'parts/{pid}.npz');body=solid(n['v'],n['f']);result={}
  if records:
   a=np.array(meta[d['part']]['transform'],float).copy()
   if pid.startswith(('P','X'))and np.linalg.det(a[:3,:3])<0:a[:3,1]*=-1
   bed=exports[pid]['bed'];t=H(d['orientation']['matrix'],d['orientation']['source_translation_mm'])@H(bed['rotation'],bed['translation_mm'])@np.linalg.inv(a)
   for q in records:
    key=q['feature'];ok,evidence=inspect(body,hw[key].transform(t[:3,:]));result[key]=dict(is_cavity=ok,evidence=evidence)
  results[pid]=result;put(WORK/f'cavity_selection/{pid}.json',result);print('CAVITY',pid,sum(x['is_cavity']for x in result.values()),'of',len(result),flush=True)
 put(WORK/'hardware_cavity_selection.json',results)
if __name__=='__main__':main()