"""Longer input yoke provides a 120-degree negative bend for full shoulder targets.
Original core and TUT remain separately reproducible. No measured strength claim.
"""
from common import *
import core,twist,tut
frames=tut.frames

def make():
 p,o,sk=core.make(extensions=(6,0));tp,to,ts=twist.make();AX=np.array([[1,0,0],[0,0,1],[0,-1,0]])
 p['C01']-=cyl(1.25,-29,0)+box([-4.1,-4.1,-2.6],[4.1,4.1,1.6])
 # Offset the lower negative-X yoke leg, preserving bearing lands above Z=-10.
 t=tri(p['C01']);t[:,:,0]+=4.5*np.clip(-t[:,:,0]/14.55,0,1)*np.clip((-t[:,:,2]-10)/5,0,1);p['C01']=from_tri(t)
 for side in (-1,1):
  cut=twist.sector(6.4,7.8,-126,126,11.4,13.6);cut=pose(pose(cut,rot(0,180)) if side<0 else cut,AX)
  for k in ('C14','C15'):p[k]-=cut
 for key,e,flip,lab in [('C01',7.5,np.eye(3),'P'),('C02',7,rot(0,180),'D')]:
  plane=18.6+e;p[key]=p[key]^box([-60,-60,-plane if key=='C01' else -60],[60,60,60 if key=='C01' else plane])
  for k,v in tp.items():
   vv=pose(v.translate([0,0,-e]),flip)
   if k=='rotor':p[key]+=vv
   else:p[lab+'_'+k]=vv;o[lab+'_'+k]=key if to[k]=='child' else lab;sk[lab+'_'+k]=ts[k]
 # Assembly lead-in on the lower outer rim: outside the radius-6 washer
 # contact and outside the C01 +/-25-degree stop sector. It admits C14 past
 # the inward-offset yoke leg without changing the working bearing face.
 protect=pose(cyl(6.1,-50,50,n=180),rot(1,90))
 p['C14']-=box([-13.7,-1.3,-8.2],[-12.5,4.,-6.0])-protect
 return p,o,sk

def main():
 p,o,sk=make();rec={k:mesh_record(v) for k,v in p.items()};rr=[]
 for i,(a,b) in enumerate(itertools.product((-25,0,25),(-120,-115,-110,-100,-90,-60,0))):
  fs=frames([0,a,b,0]);hh=hits({k:pose(v,fs[o[k]]) for k,v in p.items()});rr.append({'angles':[0,a,b,0],'findings':hh});print('wide TUT',a,b,[(h['pair'],round(h['overlap_mm3'],3)) for h in hh],flush=True)
 np.savez_compressed(OUT/'wide_tut_parts.npz',**{k:tri(v) for k,v in p.items()});save('wide_tut_build.json',{'parts':rec,'owners':o,'stock_skus':sk,'motion':rr,'physical_tested':False,'nominal_limits_deg':[[-170,170],[-25,25],[-120,0],[-170,170]]});print('components',[(k,r['components']) for k,r in rec.items() if r['components']!=1],flush=True)
if __name__=='__main__':main()
