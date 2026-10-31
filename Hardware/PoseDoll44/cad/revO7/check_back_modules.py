"""Actual O7 arm modules versus both declared back reservations (no skin/yokes)."""
from pathlib import Path
import argparse,json,hashlib,itertools,sys
import cadquery as cq
import numpy as np
R=Path(__file__).resolve().parents[4];H=R/'Hardware/PoseDoll44'
sys.path.insert(0,str(H/'cad'));sys.path.insert(0,str(H/'cad/revO6'))
from model import fk,rotation
from audit_mixed import located
from thread_geometry import overlap_volume

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--large',type=Path,required=True);ap.add_argument('--small',type=Path,required=True);ap.add_argument('--layout',type=Path,required=True);ap.add_argument('--space',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 sources=[Path(__file__),H/'cad/model.py',H/'cad/revO6/audit_mixed.py',H/'cad/revO6/thread_geometry.py',a.layout/'layout_search.json',a.space];parts={}
 for fam,folder in [('LP6',a.large),('M4',a.small)]:
  m=json.loads((folder/'manifest.json').read_text());sources.append(folder/'manifest.json');lib=[]
  for part in m['parts']:
   p=folder/part['step_file'];assert sha(p)==part['step_sha256'];sources.append(p);b=part['bounds_mm'];corners=np.array(list(itertools.product(*zip(b[:3],b[3:]))));lib.append((part['part_id'],part['owner'],cq.importers.importStep(str(p)).val(),corners))
  parts[fam]=lib
 d=json.loads((a.layout/'layout_search.json').read_text());records={(c['character'],c['side']):c for c in d['characters']};profiles={}
 for key in records:
  p=a.layout/('_'.join(key)+'_profile.json');sources.append(p);profiles[key]=json.loads(p.read_text())
 space=json.loads(a.space.read_text());variants=[space['prior_targets'][0],space['selected_thin_target']];assert all(variants)
 inputs={p.resolve().relative_to(R).as_posix():sha(p) for p in sources};cases=[]
 for char in ('manny','quinn'):
  left,right=records[char,'l'],records[char,'r']
  for k,lp in enumerate(left['poses']):
   q=dict(lp['angles_deg']);q.update(right['poses'][k]['angles_deg']);T,A=fk(profiles[char,'l'],q);chest=T['chest'];cache={};hits_by_variant=[]
   for variant in variants:
    lo=np.array(variant['local_bounds_mm'][:3]);hi=np.array(variant['local_bounds_mm'][3:]);dims=hi-lo;box=cq.Workplane('XY').box(*dims).val().translate(tuple((lo+hi)/2));box=located(box,chest);bc=np.array(list(itertools.product(*zip(lo,hi))))@chest[:3,:3].T+chest[:3,3];bl,bh=bc.min(0),bc.max(0);hits=[];clear=[];nexact=0
    for side in ('l','r'):
     c=records[char,side];_,axes=fk(profiles[char,side],c['poses'][k]['angles_deg'])
     for i,(axis,fam) in enumerate(zip(c['axes'],c['families'])):
      M=np.array(c['module_frames'][i][k]);C=M.copy();C[:3,:3]=rotation(axes[axis]['direction'],c['poses'][k]['angles_deg'].get(axis,0))@M[:3,:3];hit=None
      for name,owner,s,corners in parts[fam]:
       frame=C if owner=='child' else M;pc=corners@frame[:3,:3].T+frame[:3,3]
       if np.any(np.minimum(bh,pc.max(0))-np.maximum(bl,pc.min(0))<=1e-5):continue
       if (axis,name) not in cache:cache[axis,name]=located(s,frame)
       v=overlap_volume(box,cache[axis,name]);nexact+=1
       if v>1e-4:hit={'axis':axis,'part':name,'intersection_mm3':v};hits.append(hit);break
      if hit is None:clear.append(axis)
    cases.append({'character':char,'pose':lp['pose'],'variant':variant['name'],'status':'FAIL_RESERVATION_MODULE_COLLISION' if hits else 'CLEAR_SAMPLED_MODULES_ONLY','first_hit_per_module':hits,'fully_checked_clear_modules':clear,'exact_checks':nexact});hits_by_variant.append(len(hits))
   save(a.out/'back_modules.json',{'status':'RUNNING_INCOMPLETE','cases':cases,'input_sha256':inputs});print(char,lp['pose'],hits_by_variant,flush=True)
 assert all(sha(R/n)==h for n,h in inputs.items())
 save(a.out/'back_modules.json',{'status':'FAIL' if any(c['first_hit_per_module'] for c in cases) else 'CLEAR_SCOPED_RESERVATIONS_ONLY','cases':cases,'variants':variants,'input_sha256':inputs,'physical_tested':False,'manufacturing_released':False,'scope':'Current trial modules vs reservation boxes. Single first positive per module; clear modules tested all relevant part pairs. Excludes real back PCBA, mount, shell, neck/torso hardware and harness. Discrete, not full motion certification.'})
if __name__=='__main__':main()
