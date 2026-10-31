"""Application-specific three-angle trunk/neck joint, one outer twist.
The C02 yoke is retained; the X-stop relief is sized for +/-45 degrees.
No shoulder/hip module or its limits are silently changed.
"""
from common import *
import core,twist

def make():
 p,o,sk=core.make(extensions=(6,0),wide=True);tp,to,ts=twist.make();AX=np.array([[0,0,1],[1,0,0],[0,1,0]])
 for side in (-1,1):
  cut=twist.sector(6.4,7.8,-51,51,11.4,13.6);cut=pose(pose(cut,rot(0,180)) if side<0 else cut,AX)
  for k in ('C14','C15'):p[k]-=cut
 # Keep the full C02 yoke: its original bridge is necessary for large bends.
 # O13's central magnet-support pin is superseded by the retained side encoder.
 p['C01']-=cyl(1.25,-22,0)+box([-4.1,-4.1,-2.6],[4.1,4.1,1.6])
 p['C01']=p['C01']^box([-60,-60,-26.1],[60,60,60])
 for k,v in tp.items():
  vv=v.translate([0,0,-7.5])
  if k=='rotor':p['C01']+=vv
  else:p['P_'+k]=vv;o['P_'+k]='C01' if to[k]=='child' else 'P';sk['P_'+k]=ts[k]
 # Relieve the ring exterior while retaining both radius-8 bearing lands.
 protect=pose(cyl(8.00005,-14,14,n=720),AX)
 for a in range(-45,46,3):
  cutter=pose(p['C01'],rot(0,a))-protect
  for k in ('C14','C15'):p[k]-=cutter
 for k in ('C01_pcb_clip_screw','C01_pcb_clip_nut'):
  cutter=p[k]
  for ax in range(3):
   for sign in (-1,1):cutter+=p[k].translate(np.eye(3)[ax]*sign*.15)
  p['C14']-=cutter
 return p,o,sk

def frames(q):
 p,a,b=q;P=rot(2,p);A=P@rot(0,a);B=A@rot(1,b);return {'P':np.eye(3),'C01':P,'ring':A,'C02':B}
def inverse(M):
 a=np.rad2deg(np.arcsin(np.clip(M[2,1],-1,1)));b=np.rad2deg(np.arctan2(-M[2,0],M[2,2]));p=np.rad2deg(np.arctan2(-M[0,1],M[1,1]));q=np.array([p,a,b]);return q,float(np.max(np.abs(frames(q)['C02']-M)))
def main():
 p,o,sk=make();rec={k:mesh_record(v) for k,v in p.items()};cases=[[ph,a,b] for ph,a,b in itertools.product((-90,0,90),(-45,-30,0,30,45),(-90,-60,-30,0))];results=[]
 for i,q in enumerate(cases):
  fs=frames(q);pp={k:pose(v,fs[o[k]]) for k,v in p.items()};hh=hits(pp);results.append({'angles_deg':q,'findings':hh})
  if (i+1)%20==0:print('three-axis',i+1,'fail',sum(bool(x['findings']) for x in results),flush=True)
 save('three_axis_build.json',{'parts':rec,'owners':o,'stock_skus':sk,'motion':results,'raw_encoder_count':3,'semantic_rotation_count':3,'physical_tested':False});np.savez_compressed(OUT/'three_axis_parts.npz',**{k:tri(v) for k,v in p.items()})
 print('THREE',len(p),'components',[(k,v['components']) for k,v in rec.items() if v['components']!=1],'fail',[(r['angles_deg'],len(r['findings'])) for r in results if r['findings']],flush=True)
if __name__=='__main__':main()
