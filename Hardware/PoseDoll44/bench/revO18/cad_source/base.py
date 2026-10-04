from pathlib import Path
import sys,json, numpy as np
H=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(H/'cad/revO17'))
import geometry as g
from layout_fullbody import build,fk
from common import *

OUT=H/'generated/revO18'
BENCH=H/'bench/revO18'

def load_o17():
 p,m,st,f,pr,prov=g.build_fitted('quinn',g.ASSEMBLY_POSE)
 assert not f
 changes=g.read(H/'generated/revO17/changes.json')
 original_m=m.copy()
 for k in changes['removed_parts']:p.pop(k);m.pop(k)
 z=np.load(H/'generated/revO17/changed_parts.npz')
 for r in changes['replacements']:
  mm=original_m[r['anchor']].copy();mm['source_anchor']=r['anchor']
  for k in r['replaces']:p.pop(k);m.pop(k)
  p[r['part']]=g.move(from_tri_exact(z[r['part']]).simplify(1e-4),mm['transform']);m[r['part']]=mm
 return p,m,pr,st,prov

def position(p,m,angles):
 _,mm,st,f,pr=build('quinn',angles,geometry=False);assert not f
 T,_=fk(pr,angles);out={};transforms={}
 for k,s in p.items():
  meta=m[k]
  if meta['owner']=='rigid_frame':A=T[meta['body']]
  else:A=mm[meta.get('source_anchor',meta.get('follows_part',k))]['transform']
  transforms[k]=A
  out[k]=g.move(s,A@np.linalg.inv(meta['transform']))
 return out,transforms

if __name__=='__main__':
 p,m,pr,st,prov=load_o17()
 print('hinges',[(s['id'],s['parent'],s['child']) for s in st if s['kind']=='hinge'])
 for k in ['frame/pelvis','frame/chest','clavicle_l.protract/base_service_half']:
  print(k,m.get(k), p[k].bounding_box())
 pp,own,sk=libraries()['hinge'] if False else ({},{},{})
 from layout_fullbody import libraries
 pp,own,sk=libraries()['hinge']
 print('hinge stock',[(k, list(s.bounding_box())) for k,s in pp.items() if sk[k] and sk[k]!='PCBA_INCLUDED'])
 print('provenance',prov)
