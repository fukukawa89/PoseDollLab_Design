"""Four measured angles for a three-rotation ball-like joint.
No extra angle is silently discarded; the calibrated matrix is reconstructed.
"""
from common import *
import core,twist

def make():
 p,o,sku=core.make();tp,to,ts=twist.make()
 for key,e,flip,lab in [('C01',1.5,np.eye(3),'P'),('C02',7,rot(0,180),'D')]:
  plane=18.6+e
  p[key]=p[key]^box([-60,-60,-plane if key=='C01' else -60],[60,60,60 if key=='C01' else plane])
  for k,v in tp.items():
   vv=pose(v.translate([0,0,-e]),flip)
   if k=='rotor':p[key]+=vv
   else:p[lab+'_'+k]=vv;o[lab+'_'+k]=key if to[k]=='child' else lab;sku[lab+'_'+k]=ts[k]
 return p,o,sku

def frames(q):
 phi,a,b,psi=q;C=rot(2,phi);A=C@rot(0,a);B=A@rot(1,b)
 return {'P':np.eye(3),'C01':C,'ring':A,'C02':B,'D':B@rot(2,psi)}
def main():
 p,o,s=make();rec={k:mesh_record(v) for k,v in p.items()};motion=[]
 cases=[[0,0,0,0],[0,0,-45,0],[0,0,-90,0]]+[[ph,a,b,ps] for ph,a,b,ps in itertools.product((-90,90),(-25,25),(-95,0),(-90,90))]
 for q in cases:
  fs=frames(q);pp={k:pose(v,fs[o[k]]) for k,v in p.items()};hh=hits(pp);motion.append({'angles_deg':q,'findings':hh})
 save('tut_build.json',{'parts':rec,'owners':o,'stock_skus':s,'motion':motion,'physical_tested':False,'raw_encoder_count':4,'semantic_rotation_count':3,'nominal_limits_deg':[[-170,170],[-25,25],[-95,0],[-170,170]]});np.savez_compressed(OUT/'tut_parts.npz',**{k:tri(v) for k,v in p.items()})
 print('tut',len(p),'components',[(k,r['components']) for k,r in rec.items() if r['components']!=1], 'motion',[(x['angles_deg'],len(x['findings'])) for x in motion],flush=True)
if __name__=='__main__':main()
