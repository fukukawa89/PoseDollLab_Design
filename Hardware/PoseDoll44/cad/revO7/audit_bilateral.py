"""Both arms, all recorded poses: actual 18-module solids, no invented yokes or shells."""
from pathlib import Path
import argparse,hashlib,json,itertools,sys
import numpy as np
import cadquery as cq
R=Path(__file__).resolve().parents[4];H=R/'Hardware/PoseDoll44'
sys.path.insert(0,str(H/'cad'));sys.path.insert(0,str(H/'cad/revO6'))
from model import fk,rotation
from thread_geometry import overlap_volume
from audit_mixed import located
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--large',type=Path,required=True);ap.add_argument('--small',type=Path,required=True);ap.add_argument('--layout',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.layout=a.layout.resolve()
 sources=[Path(__file__),H/'cad/revO6/thread_geometry.py',H/'cad/revO6/audit_mixed.py',H/'cad/model.py',a.layout/'layout_search.json'];libraries={}
 for fam,folder in [('LP6',a.large.resolve()),('M4',a.small.resolve())]:
  m=json.loads((folder/'manifest.json').read_text());sources.append(folder/'manifest.json');parts=[]
  assert not m['nominal_intersections'] and all(x.get('pass',True) for x in m['boolean_volume_guards'])
  for row in m['parts']:
   p=folder/row['step_file'];assert sha(p)==row['step_sha256'];sources.append(p);b=row['bounds_mm'];corners=np.array(list(itertools.product(*zip(b[:3],b[3:]))));parts.append((row['part_id'],row['owner'],cq.importers.importStep(str(p)).val(),corners))
  libraries[fam]=parts
 layout=json.loads((a.layout/'layout_search.json').read_text());records={(c['character'],c['side']):c for c in layout['characters']};profiles={}
 for key,c in records.items():
  p=a.layout/('_'.join(key)+'_profile.json');sources.append(p);profiles[key]=json.loads(p.read_text())
 receipt={p.relative_to(R).as_posix():sha(p) for p in sources};results=[]
 for character in ('manny','quinn'):
  left,right=records[character,'l'],records[character,'r'];assert len(left['poses'])==len(right['poses'])
  for k,pose in enumerate(left['poses']):
   assert pose['pose'].replace('_l.','_r.')==right['poses'][k]['pose']
   objects={};cache={}
   for side,c in [('l',left),('r',right)]:
    q=c['poses'][k];T,A=fk(profiles[character,side],q['angles_deg'])
    for i,(axis,fam) in enumerate(zip(c['axes'],c['families'])):
     M=np.array(c['module_frames'][i][k]);C=M.copy();C[:3,:3]=rotation(A[axis]['direction'],q['angles_deg'].get(axis,0))@M[:3,:3];rows=[]
     for n,owner,shape,corners in libraries[fam]:
      frame=C if owner=='child' else M;pt=corners@frame[:3,:3].T+frame[:3,3];rows.append((n,shape,frame,pt.min(0),pt.max(0)))
     objects[axis]=rows
   actual=[];clear=[];nexact=0
   for x,y in itertools.combinations(objects,2):
    aa,bb=objects[x],objects[y];la=np.array([r[3] for r in aa]);ha=np.array([r[4] for r in aa]);lb=np.array([r[3] for r in bb]);hb=np.array([r[4] for r in bb]);ov=np.minimum(ha[:,None,:],hb[None,:,:])-np.maximum(la[:,None,:],lb[None,:,:]);candidates=np.argwhere((ov>1e-5).all(2));hit=None
    for ai,bi in candidates:
     an,sa,ma,_,_=aa[ai];bn,sb,mb,_,_=bb[bi]
     for axis,name,shape,frame in [(x,an,sa,ma),(y,bn,sb,mb)]:
      if (axis,name) not in cache:cache[axis,name]=located(shape,frame)
     volume=overlap_volume(cache[x,an],cache[y,bn]);nexact+=1
     if volume>1e-4:hit={'axis_a':x,'axis_b':y,'part_a':an,'part_b':bn,'volume_mm3':volume,'cross_arm':('_l.' in x)!=('_l.' in y)};actual.append(hit);break
    if hit is None:clear.append([x,y])
   row={'character':character,'pose':pose['pose'],'first_hit_per_module_pair':actual,'fully_checked_clear_module_pairs':clear,'exact_part_pair_checks':nexact,'status':'FAIL' if actual else 'PASS_NOMINAL_MODULES_ONLY'}
   results.append(row);save(a.out/'bilateral.json',{'status':'RUNNING_INCOMPLETE','cases':results,'input_sha256':receipt,'physical_tested':False,'manufacturing_released':False});print(character,pose['pose'],len(actual),'hits',nexact,'exact',flush=True)
 assert all(sha(R/k)==h for k,h in receipt.items())
 save(a.out/'bilateral.json',{'status':'FAIL' if any(c['first_hit_per_module_pair'] for c in results) else 'PASS_SCOPED_NOMINAL_MODULES_ONLY','cases':results,'input_sha256':receipt,'scope':'18 modules, all 153 pair combinations per case, discrete poses; no yokes, PCB assemblies, skin, neck/trunk or harness. Not full-arm qualification.','physical_tested':False,'manufacturing_released':False})
if __name__=='__main__':main()

