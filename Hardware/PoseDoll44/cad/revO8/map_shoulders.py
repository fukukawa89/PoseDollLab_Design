"""Explicit TUT orientation mapping of all O7 shoulder poses and neutral-to-pose paths.
A kinematic existence study: not a whole-arm fit or user manipulation certificate.
"""
from pathlib import Path
import sys,json,hashlib,math
import numpy as np
from reference_assembly import OUT,rot
R=Path(__file__).resolve().parents[4];H=R/'Hardware/PoseDoll44';sys.path.insert(0,str(H/'cad'))
from model import fk

def frame_z(z):
 z=np.array(z,float);z/=np.linalg.norm(z);x=np.cross([0,0,1],z);x/=np.linalg.norm(x);return np.column_stack((x,np.cross(z,x),z))

def sphere_search(v,n=100000):
 i=np.arange(n);z=1-2*(i+.5)/n;phi=i*np.pi*(3-np.sqrt(5));a=np.sqrt(1-z*z);d=np.c_[a*np.cos(phi),a*np.sin(phi),z];best=(-2,None)
 for block in np.array_split(d,100):
  scores=(block@v.T).min(1);k=np.argmax(scores)
  if scores[k]>best[0]:best=(float(scores[k]),block[k])
 return best

def tut_angles(M):
 # Exact decomposition with alpha=0; redundant proximal twist steers the bend plane.
 v=M[:,2];beta=np.arccos(np.clip(v[2],-1,1));phi=np.arctan2(v[1],v[0]);U=rot([0,1,0],-np.rad2deg(beta))@rot([0,0,1],-np.rad2deg(phi))@M;psi=np.arctan2(U[1,0],U[0,0]);angles=np.rad2deg([phi,0,beta,psi]);rebuilt=rot([0,0,1],angles[0])@rot([0,1,0],angles[2])@rot([0,0,1],angles[3]);return angles,float(np.max(np.abs(M-rebuilt)))

def main():
 source=H/'generated/revO7/runs/o7_20260924_r1/bilateral_current';layout=json.loads((source/'layout_search.json').read_text());groups=[];cout=rot([0,1,0],180)
 for row in layout['characters']:
  char,side=row['character'],row['side'];path=source/f'{char}_{side}_profile.json';profile=json.loads(path.read_text());paths=[]
  for p in row['poses']:
   count=max(1,int(np.ceil(max([abs(v) for v in p['angles_deg'].values()]+[0])/5)));steps=[]
   for u in np.linspace(0,1,count+1):
    T,_=fk(profile,{k:v*u for k,v in p['angles_deg'].items()});relative=T[f'clavicle_{side}'][:3,:3].T@T[f'upperarm_{side}'][:3,:3];steps.append(relative@cout)
   paths.append({'pose':p['pose'],'requested_angles_deg':p['angles_deg'],'matrices':steps})
  # Repeated directions do not influence the minimax score.
  vectors=np.unique(np.round(np.array([m[:,2] for p in paths for m in p['matrices']]),9),axis=0);score,axis=sphere_search(vectors);mount=frame_z(axis);paths_out=[];all_angles=[];max_error=0.
  for p in paths:
   computed=[tut_angles(mount.T@m) for m in p['matrices']];angles=np.array([a for a,e in computed]);angles[:,0]=np.rad2deg(np.unwrap(np.deg2rad(angles[:,0])));angles[:,3]=np.rad2deg(np.unwrap(np.deg2rad(angles[:,3])));angles[:,[0,3]]-=angles[0,[0,3]];all_angles.extend(angles);max_error=max(max_error,max(e for a,e in computed));paths_out.append({'pose':p['pose'],'requested_angles_deg':p['requested_angles_deg'],'relative_twist_angles_and_absolute_bend_deg':angles.tolist(),'endpoint_required_bend_deg':float(angles[-1,2])})
  a=np.array(all_angles);groups.append({'character':char,'side':side,'input_axis_in_clavicle_frame':axis.tolist(),'mount_matrix':mount.tolist(),'max_bend_deg':float(np.rad2deg(np.arccos(score))),'reconstruction_matrix_max_error':max_error,'angle_column_order':['phi_relative_to_neutral','alpha','beta','psi_relative_to_neutral'],'angle_ranges_deg':np.c_[a.min(0),a.max(0)].tolist(),'physical_path_samples':len(a),'paths':paths_out,'profile_sha256':hashlib.sha256(path.read_bytes()).hexdigest()});print(char,side,groups[-1]['max_bend_deg'],groups[-1]['angle_ranges_deg'],flush=True)
 data={'scope':'All 51 prior O7 poses per character/side, including previously out-of-profile stress poses, plus joint-angle-linear paths at <=5 degree increments. Rotations only. No source poses dropped. This uses one alpha=0 path through the redundant 4-axis mechanism; it does not prove arbitrary mixed-alpha paths, continuous collision clearance, ergonomics or final wire twist limits.','mount_search':'100000-point Fibonacci sphere, numerical minimax over sampled directions; no global optimality claim','characters':groups,'source_layout_sha256':hashlib.sha256((source/'layout_search.json').read_bytes()).hexdigest(),'physical_tested':False,'manufacturing_released':False}
 (OUT.parent/'shoulder_mapping.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
