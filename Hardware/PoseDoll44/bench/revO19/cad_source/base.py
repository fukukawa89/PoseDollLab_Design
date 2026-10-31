from pathlib import Path
import sys,json,numpy as np
H=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(H/'cad/revO17'))
import geometry as g
import layout_fullbody as L
from common import *
OUT=H/'generated/revO19';BENCH=H/'bench/revO19'
OUT.mkdir(parents=True,exist_ok=True)

def load_o18():
 p,m,st,f,pr,prov=g.build_fitted('quinn',g.ASSEMBLY_POSE);assert not f
 c=g.read(H/'generated/revO17/changes.json');om=m.copy()
 for k in c['removed_parts']:p.pop(k);m.pop(k)
 with np.load(H/'generated/revO17/changed_parts.npz') as z:
  for r in c['replacements']:
   mm=om[r['anchor']].copy();mm['source_anchor']=r['anchor']
   for k in r['replaces']:p.pop(k);m.pop(k)
   p[r['part']]=g.move(from_tri_exact(z[r['part']]).simplify(1e-4),mm['transform']);m[r['part']]=mm
 c=g.read(H/'generated/revO18/changes.json');om=m.copy()
 for k in c['removed_stock_parts']:p.pop(k);m.pop(k)
 with np.load(H/'generated/revO18/changed_parts.npz') as z:
  for r in c['replacements']:
   mm=om[r['anchor']].copy()
   for k in r['replaces']:p.pop(k);m.pop(k)
   p[r['part']]=g.move(from_tri_exact(z[r['part']]).simplify(1e-4),mm['transform']);m[r['part']]=mm
 return p,m,pr,st,prov

def position(p,m,angles,overrides=None):
 _,mm,st,f,pr=L.build('quinn',angles,overrides=overrides,geometry=False)
 T,A=L.fk(pr,angles);out={};transforms={}
 for k,s in p.items():
  meta=m[k]
  M=T[meta['body']] if meta['owner']=='rigid_frame' else mm[meta.get('source_anchor',meta.get('follows_part',k))]['transform']
  transforms[k]=M;out[k]=g.move(s,M@np.linalg.inv(meta['transform']))
 return out,transforms,st,f,pr

def hip_overrides(tilt=0,phase=0,offset=0):
 _,mods=L.config('quinn');ov={}
 for s in mods:
  if not s['id'].startswith('thigh_'):continue
  V=np.array(s['V']);F=V@rot(0,tilt)@rot(2,phase)
  ov[s['id']]={'F':F.tolist(),'offset_parent_mm':[0,offset if s['id'].endswith('_l') else -offset,0]}
 return ov

def overlaps(p,focus,exclude=(),same_body_meta=None,tol=.001):
 keys=[k for k in p if k not in exclude];bb=np.array([p[k].bounding_box() for k in keys]);out=[]
 for i,a in enumerate(keys):
  mask=np.all(np.minimum(bb[i,3:],bb[i+1:,3:])>np.maximum(bb[i,:3],bb[i+1:,:3])+1e-8,axis=1)
  for j in np.flatnonzero(mask)+i+1:
   b=keys[j]
   if a not in focus and b not in focus:continue
   if same_body_meta and same_body_meta[a]['body']==same_body_meta[b]['body']:continue
   v=max(0.,float((p[a]^p[b]).volume()))
   if v>tol:out.append({'pair':[a,b],'overlap_mm3':v})
 return sorted(out,key=lambda r:-r['overlap_mm3'])
