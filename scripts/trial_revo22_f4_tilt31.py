"""Reorient an existing candidate without introducing further body changes."""
from pathlib import Path
import sys,json,copy,math,numpy as np,concurrent.futures,traceback
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
import build_revo22_fins_v4 as builder
from build_revo22_f4_coverage_candidates import ITEMS,VOLS
from build_revo22_fins import solid,vf
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
from repair_revo22_f4_fast_paths import repair as full
from verify_revo22_f4_body_change import check as fit
from verify_revo22_f4_repaired_geometry import check as geom
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def one(spec):
 pid,parent,ax,ay=spec;label=f'tilt31_{ax:+d}_{ay:+d}'.replace('+','p').replace('-','m');src=O/'candidates'/pid/parent;dst=O/'candidates'/pid/label
 try:
  n=dict(np.load(src/'parts'/f'{pid}.npz'));d=json.loads((src/'design'/f'{pid}.json').read_text());M=np.array(d['orientation']['matrix']);t=np.array(d['orientation']['source_translation_mm']);v=(n['v']-t)@M;f=n['f'];x=math.radians(ax);y=math.radians(ay);Rx=np.array([[1,0,0],[0,math.cos(x),-math.sin(x)],[0,math.sin(x),math.cos(x)]]);Ry=np.array([[math.cos(y),0,math.sin(y)],[0,1,0],[-math.sin(y),0,math.cos(y)]]);Q=Rx@Ry@M;vv=v@Q.T;off=-vv.min(0);ori={'matrix':Q.tolist(),'source_translation_mm':off.tolist(),'gravity_in_source':Q[2].tolist(),'size_mm':np.ptp(vv,axis=0).tolist()}
  for sub in ['parts','design','verification','figures']:(dst/sub).mkdir(parents=True,exist_ok=True)
  builder.O=dst;builder.read_mesh=lambda _: (v,f);builder.choose=lambda _:ori;builder.AXIS=None;builder.FACE_FILTER=None;builder.PITCH_OVERRIDE=3.2 if np.ptp(vv[:,2])<50 else 4.;builder.NORMAL_THRESHOLD=-.3;builder.SEGMENT_OVERRIDE=None;builder.make(pid,ITEMS[pid],VOLS.get(pid,[]));out=dict(np.load(dst/'parts'/f'{pid}.npz'));out['source_v']=n['source_v'];rd=json.loads((dst/'design'/f'{pid}.json').read_text());rd['orientation_trial_parent']=parent;rd['orientation_delta_deg']=[ax,ay,0]
  if 'body_change' in d:
   out['source_f']=n.get('source_f',n['f']);old=solid(out['source_v']@Q.T+off,out['source_f']);new=solid(out['v'],out['f']);out['removed_body_v'],out['removed_body_f']=vf(old-new);rep=copy.deepcopy(d['body_change']);A=Q@M.T;tt=off-A@t
   for row in rep.get('chamfers',[]):
    b=row['local_bounds_mm'];cs=np.array([[xx,yy,zz] for xx in [b[0],b[3]] for yy in [b[1],b[4]] for zz in [b[2],b[5]]])@A.T+tt;row['local_bounds_mm']=np.r_[cs.min(0),cs.max(0)].tolist()
   rd['body_change']=rep;rd['source_mesh_preserved']=False
  np.savez_compressed(dst/'parts'/f'{pid}.npz',**out);(dst/'design'/f'{pid}.json').write_text(json.dumps(rd,ensure_ascii=False,indent=2),encoding='utf8');run(pid,label);r=check(pid,label)
  if not r['native_review_resolved']:
   nextlabel=label+'_f';full(pid,label,nextlabel);label=nextlabel;r=check(pid,label)
  if r['native_review_resolved']:
   if 'body_change' in rd:fit(pid,label)
   geom(pid,label)
  result={k:r[k] for k in ['id','label','external_island_count','critical_external_count','native_review_resolved']};print('TILT31_RESULT',result,flush=True);return result
 except Exception:return {'id':pid,'label':label,'error':traceback.format_exc()}
if __name__=='__main__':
 pid,parent=sys.argv[1:3];jobs=[(pid,parent,x,y) for x,y in [(-2,-2),(-2,0),(-2,2),(0,-2),(0,2),(2,-2),(2,0),(2,2)]];out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
  for f in concurrent.futures.as_completed([pool.submit(one,j) for j in jobs]):
   out.append(f.result());(O/(pid+'_tilt31_progress.json')).write_text(json.dumps(out,indent=2))
