"""F2 orientation sweep; geometric ranking, not FEM or physical qualification."""
from pathlib import Path
import sys,json,math,collections,argparse
import numpy as np
from pack_revo22_a1mini import read_mesh
R=Path(__file__).resolve().parents[1];B=R/'Hardware/PoseDoll44/bench/revO22';O=B/'a1mini_fins_v2';O.mkdir(exist_ok=True)

def frame(n):
 n=np.asarray(n,float);n/=np.linalg.norm(n);seed=np.eye(3)[np.argmin(abs(n))];x=np.cross(seed,n);x/=np.linalg.norm(x);y=np.cross(n,x);return np.array([x,y,n])
def weighted_q(v,w,q):
 ix=np.argsort(v);return float(v[ix][np.searchsorted(np.cumsum(w[ix]),w.sum()*q,side='left')]) if len(v) else 0.
def analyze(v,f):
 tr=v[f];cross=np.cross(tr[:,1]-tr[:,0],tr[:,2]-tr[:,0]);a=np.linalg.norm(cross,axis=1)/2;n=cross/np.maximum(2*a[:,None],1e-15);cent=tr.mean(axis=1);good=a>1e-9
 tr,a,n,cent=tr[good],a[good],n[good],cent[good]
 vals={}
 for nn,aa in zip(n,a):
  key=tuple(np.round(nn,3));vals[key]=vals.get(key,0)+aa
 dirs=[np.array(x) for x in [(0,0,1),(0,0,-1),(1,0,0),(-1,0,0),(0,1,0),(0,-1,0)]]
 dirs += [-np.array(k) for k,w in sorted(vals.items(),key=lambda p:-p[1])[:40]]
 _,_,vh=np.linalg.svd(v-v.mean(axis=0),full_matrices=False)
 dirs += [d*sgn for d in vh for sgn in [-1,1]]
 for i in range(72):
  z=1-2*(i+.5)/72;t=math.pi*(3-math.sqrt(5))*i;r=math.sqrt(1-z*z);dirs.append(np.array([r*math.cos(t),r*math.sin(t),z]))
 seen=set();out=[]
 for d in dirs:
  d=d/np.linalg.norm(d);key=tuple(np.round(d,4))
  if key in seen:continue
  seen.add(key);m=frame(d);best=None
  for angle in [0,15,30,45,60,75]:
   r=math.radians(angle);rz=np.array([[math.cos(r),-math.sin(r),0],[math.sin(r),math.cos(r),0],[0,0,1]])
   M=rz@m;vv=v@M.T;size=np.ptp(vv,axis=0);value=size[0]*size[1]+10000*max(0,max(size[:2])-168)
   if best is None or value<best[0]:best=(value,M,size,vv.min(axis=0))
  _,m,size,lo=best;z=cent@d-lo[2];nz=n@d;down=(nz<-.55)&(z>.35);proj=a[down]*-nz[down];dh=z[down];area=float(proj.sum());top=(tr@d-lo[2]).max(axis=1);contact=float((a*np.maximum(0,-nz)*(top<.21)).sum())
  risk=float((proj*(dh+2)*(1+(dh/15)**2)).sum());h95=weighted_q(dh,proj,.95);hmax=float(dh.max()) if len(dh) else 0
  score=risk+2*size[2]**2+1500/(contact+1)+15*h95**2+5000*max(0,max(size[:2])-168)**2
  out.append({'score':score,'matrix':m.tolist(),'source_translation_mm':(-lo).tolist(),'gravity_in_source':d.tolist(),'size_mm':size.tolist(),'overhang_projected_area_mm2':area,'overhang_height_95_mm':h95,'max_overhang_face_height_mm':hmax,'bed_contact_projection_mm2':contact,'is_original_up':bool(np.linalg.norm(d-[0,0,1])<.0001)})
 out.sort(key=lambda x:x['score']);return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--id',nargs='*');q=ap.parse_args();manifest=json.loads((B/'a1mini/manifest.json').read_text());items={it['id']:it for p in manifest['plates'] if not p['optional'] for it in p['items']};dest=O/'orientation';dest.mkdir(exist_ok=True)
 for pid,it in items.items():
  if q.id and pid not in q.id:continue
  v,f=read_mesh(B/it['source_3mf']);out=analyze(v,f);old=next(x for x in out if x['is_original_up']);data={'id':pid,'part':it['part'],'source_3mf':it['source_3mf'],'candidate_count':len(out),'original':old,'ranked_candidates':out};(dest/f'{pid}.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');new=out[0];print(pid,'candidates',len(out),'height',round(old['size_mm'][2],1),'->',round(new['size_mm'][2],1),'overhang95',round(old['overhang_height_95_mm'],1),'->',round(new['overhang_height_95_mm'],1),'bed',round(new['bed_contact_projection_mm2'],1),flush=True)
if __name__=='__main__':main()