"""Bounded four-angle allocation on every retained O7 shoulder path.
No geometry acceptance is inferred from a successful rotation decomposition.
"""
import json,sys,numpy as np
from common import H,G8,OUT,rot,save,sha
sys.path.insert(0,str(H/'cad'))
from model import fk

def wrap(x):return (x+180)%360-180

def compose(q):
 return rot([0,0,1],q[0])@rot([1,0,0],q[1])@rot([0,1,0],q[2])@rot([0,0,1],q[3])

def candidates(M,phi0,psi0,limit=25,phi_limit=180):
 # Parameterize by alpha: a uniform phi grid misses feasible solutions near beta=90.
 polar=np.rad2deg(np.arccos(np.clip(M[2,2],-1,1)))
 extrema=min(limit,polar,180-polar)
 alpha=np.unique(np.r_[np.arange(-limit,limit+.01,1.),-extrema,0.,extrema])
 ca=np.cos(np.deg2rad(alpha));cb=M[2,2]/ca;ok=np.abs(cb)<=1+1e-10
 alpha=alpha[ok];cb=np.clip(cb[ok],-1,1);positive=np.rad2deg(np.arccos(cb));rows=[]
 for beta in (positive,-positive):
  sa=np.sin(np.deg2rad(alpha));sb=np.sin(np.deg2rad(beta));phi=np.rad2deg(np.arctan2(M[1,2],M[0,2])-np.arctan2(-sa*cb,sb))
  for a,b,p in zip(alpha,beta,phi):
   if abs(b)>100+1e-8:continue
   U=(rot([0,0,1],p)@rot([1,0,0],a)@rot([0,1,0],b)).T@M
   psi=np.rad2deg(np.arctan2(U[1,0],U[0,0]));pr=wrap(p-phi0);sr=wrap(psi-psi0)
   if abs(pr)<=phi_limit+1e-8:rows.append([pr,a,b,sr])
 return np.array(rows).reshape(-1,4)

def allocate(matrices,limit=25,phi_limit=180):
 # The same physical neutral is used for every path, not re-zeroed per target.
 M0=matrices[0];phi0=np.rad2deg(np.arctan2(M0[1,2],M0[0,2]));beta0=np.rad2deg(np.arccos(M0[2,2]));U=rot([0,1,0],-beta0)@rot([0,0,1],-phi0)@M0;psi0=np.rad2deg(np.arctan2(U[1,0],U[0,0]));q0=np.array([0.,0.,beta0,0.])
 prev=q0[None,:];cost=np.zeros(1);stages=[prev];parents=[None]
 for k,M in enumerate(matrices[1:],1):
  now=candidates(M,phi0,psi0,limit,phi_limit)
  if not len(now):return {'status':'NO_BOUNDED_DECOMPOSITION','step':k}
  delta=now[:,None,:]-prev[None,:,:]
  # Unwrapped finite joints: wrap-around is not silently treated as a short path.
  continuity=np.max(np.abs(delta),axis=2)<=30
  local=np.sum(delta**2*np.array([1,.7,.7,1]),axis=2)
  score=cost[None,:]+local+.003*np.sum(now**2*np.array([1,.2,0,1]),axis=1)[:,None]
  score[~continuity]=np.inf;parent=np.argmin(score,axis=1);nextcost=score[np.arange(len(now)),parent]
  if not np.isfinite(nextcost).any():return {'status':'NO_CONTINUOUS_BOUNDED_BRANCH','step':k,'candidate_count':len(now),'previous_count':len(prev)}
  keep=np.isfinite(nextcost);stages.append(now[keep]);parents.append(parent[keep]);prev=now[keep];cost=nextcost[keep]
 idx=int(np.argmin(cost));out=[]
 for k in range(len(stages)-1,-1,-1):
  out.append(stages[k][idx]);idx=parents[k][idx] if k else 0
 out=np.array(out[::-1]);error=max(float(np.max(np.abs(compose(q+[phi0,0,0,psi0])-m))) for q,m in zip(out,matrices))
 assert error<1e-8,error
 return {'status':'DISCRETE_ROTATION_PATH_FOUND','zero_offsets_deg':[phi0,0,0,psi0],'angles_deg':out.tolist(),'max_matrix_error':error,'max_sample_joint_change_deg':float(np.max(np.abs(np.diff(out,axis=0))))}

def inputs(step=2):
 source=H/'generated/revO7/runs/o7_20260924_r1/bilateral_current';old=json.loads((G8/'shoulder_mapping.json').read_text());layout=json.loads((source/'layout_search.json').read_text());cout=rot([0,1,0],180)
 for g,row in zip(old['characters'],layout['characters']):
  assert (g['character'],g['side'])==(row['character'],row['side'])
  profile=json.loads((source/f"{g['character']}_{g['side']}_profile.json").read_text());mount=np.array(g['mount_matrix']);paths=[]
  for p in row['poses']:
   count=max(1,int(np.ceil(max([abs(v) for v in p['angles_deg'].values()]+[0])/step)));matrices=[]
   for u in np.linspace(0,1,count+1):
    T,_=fk(profile,{k:v*u for k,v in p['angles_deg'].items()});relative=T[f"clavicle_{g['side']}"][:3,:3].T@T[f"upperarm_{g['side']}"][:3,:3];matrices.append(mount.T@relative@cout)
   paths.append((p,matrices))
  yield g,paths

def main():
 groups=[]
 for g,paths in inputs():
  out=[]
  for p,matrices in paths:
   r=allocate(matrices);out.append({'pose':p['pose'],'requested_angles_deg':p['angles_deg'],**r})
  valid=[p for p in out if p['status']=='DISCRETE_ROTATION_PATH_FOUND'];a=np.array([q for p in valid for q in p['angles_deg']]);group={'character':g['character'],'side':g['side'],'mount_matrix':g['mount_matrix'],'paths':out,'pass':len(valid),'fail':len(out)-len(valid),'ranges_deg':np.c_[a.min(0),a.max(0)].tolist() if len(a) else None};groups.append(group);print(group['character'],group['side'],group['pass'],group['fail'],group['ranges_deg'],[(p['pose'],p['status']) for p in out if p not in valid],flush=True)
  save('bounded_mapping.json',{'characters':groups,'alpha_limit_deg':25,'beta_limit_deg':100,'phi_relative_limit_deg':180,'psi_relative_limit_deg':180,'input_step_max_deg':2,'scope':'Retained O7 targets and their angle-linear sampled paths. Finite four-angle decomposition only; continuous interpolation, mechanical stops, wiring, tolerances and full assembly are not accepted by this result.','physical_tested':False,'manufacturing_released':False,'input_sha256':{'O8_mapping':sha(G8/'shoulder_mapping.json')}})
if __name__=='__main__':main()
