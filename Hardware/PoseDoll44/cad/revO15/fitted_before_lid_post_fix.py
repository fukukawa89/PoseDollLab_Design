"""Fitted sensor tails and plug envelopes layered on immutable equipment evidence."""
from common import *
from equipped import build_full
from sensor_tails import pigtail,local_ports
from tail_fit import relieve_clip
from layout_fullbody import build,fk
from carriers_swept import ASSEMBLY_POSE
from functools import lru_cache

@lru_cache(maxsize=2)
def fit_inputs(char):
 path=OUT/f'harness/{char}_tails_final.json';d=read(path)
 if d['status']!='SAMPLED_TAILS_CLEAR':raise ValueError('Tail geometry not closed')
 for p,h in d['source_sha256'].items():
  if sha(p)!=h:raise ValueError('Tail evidence changed '+p)
 return {r['sensor']:r['selected'] for r in d['rows']},sha(path)

def connector_parts(char,pr,angles):
 T0,_=fk(pr,ASSEMBLY_POSE);T,_=fk(pr,angles);entry=next(x for x in read(OUT/f'equipment/{char}_search.json')['entries'] if x['kind']=='controller')
 F=np.c_[[0,1,0],[0,0,-1],[-1,0,0]];origin=np.array(entry['front_center_world_mm'])-F@np.array([35,30,0]);A=np.eye(4);A[:3,:3]=F;A[:3,3]=origin;M=T['chest']@np.linalg.inv(T0['chest'])@A
 return {k:(pose(s,M[:3,:3],M[:3,3]),sku,T['chest']) for k,s,sku in [('power_input_mate',box([31,51,13.2],[39,59,19]),'JST_PH_2P_MATE'),('buck_power_mate',box([30,41,13.2],[40,47,19]),'JST_PH_3P_MATE')]}

def build_fitted(char,angles=ASSEMBLY_POSE):
 p,m,st,f,pr,prov=build_full(char,angles);rows,h=fit_inputs(char);ports=local_ports(char);changed=[]
 for key,row in rows.items():
  A=m[key]['transform'];I=np.linalg.inv(A);F=np.array(row['basis']);c=np.array(row['board_top_center']);pre=key[:-len('sensor_PCB')]
  if row.get('pcb_rotation_deg',0):
   Q=F@ports[key]['basis'].T;B=np.eye(4);B[:3,:3]=Q;B[:3,3]=c-Q@c;M=A@B@I
   members=[k for k in p if k.startswith(pre) and m[k]['sku'] in ('AS5048A_MINI_PCBA','PCBA_INCLUDED')]
   for k in members:p[k]=pose(p[k],M[:3,:3],M[:3,3]);changed.append(k)
   ck=pre+'pcb_clip'
   if row.get('clip_relief'):
    clip=pose(p[ck],I[:3,:3],I[:3,3]);cut,rec=relieve_clip(clip,F,c,row['radius_mm'],row['length_mm']);p[ck]=pose(cut,A[:3,:3],A[:3,3]);changed.append(ck)
  ribbon,patch,end=pigtail(row['radius_mm'],row['length_mm'])
  for suffix,s,sku in [('ribbon',ribbon,'FFC_6P_0P5_T0P2_L'+str(int(row['length_mm']))),('transition',patch,'FFC_TRANSITION_INCLUDED')]:
   k='tail/'+key+'/'+suffix;v=pose(s,F,c);p[k]=pose(v,A[:3,:3],A[:3,3]);m[k]={**m[key],'sku':sku,'transform':A.copy(),'follows_part':key};changed.append(k)
 # Small printed-frame channels have their own shape/evidence, and only remove material.
 relief=OUT/f'harness/{char}_frame_reliefs.npz'
 if relief.exists():
  with np.load(relief) as z:
   for k,tt in z.items():
    M=m[k]['transform'];p[k]=pose(from_tri_exact(tt),M[:3,:3],M[:3,3]);changed.append(k)
 for name,(s,sku,M) in connector_parts(char,pr,angles).items():
  k='accessory/chest/'+name;p[k]=s;m[k]={'body':'chest','module':'frame/chest','modules':m['frame/chest']['modules'],'owner':'rigid_frame','sku':sku,'transform':M};changed.append(k)
 prov['changed_fitted']=changed;prov['tail_report_sha256']=h
 return p,m,st,f,pr,prov

if __name__=='__main__':
 for char in ('quinn','manny'):
  p,m,st,f,pr,prov=build_fitted(char);print(char,len(p),len(prov['changed_fitted']),f)
