"""Clavicle-only stop variant supports the reference 30-degree elevation.
No full-shoulder range is inferred; the input bend remains -50..0 degrees.
"""
from common import *
import core,twist

def make():
 p,o,sk=core.make();AX=np.array([[0,0,1],[1,0,0],[0,1,0]])
 for side in (-1,1):
  cut=twist.sector(6.4,7.8,-39,39,11.4,13.6);cut=pose(pose(cut,rot(0,180)) if side<0 else cut,AX)
  for k in ('C14','C15'):p[k]-=cut
 # The inherited Z=32.25..34.5 tray belongs to the superseded end sensor.
 # Both current encoders sit on the ring side faces; keep the load bridge intact.
 p['C02']=p['C02']^box([-100,-100,-100],[100,100,31.5])
 p['C01']-=cyl(1.25,-17,0)+box([-4.1,-4.1,-2.6],[4.1,4.1,1.6])
 return p,o,sk

def main():
 p,o,sk=make();rec={k:mesh_record(v) for k,v in p.items()};rr=[]
 for a,b in itertools.product((-30,-15,0,15,30),(-50,-40,-30,-20,-10,0)):
  fs={'C01':rot(0,a),'C02':rot(1,b),'ring':np.eye(3)};hh=hits({k:pose(v,fs[o[k]]) for k,v in p.items()});rr.append({'angles_deg':[a,b],'findings':hh})
 np.savez_compressed(OUT/'clavicle_core_parts.npz',**{k:tri(v) for k,v in p.items()});save('clavicle_core_build.json',{'parts':rec,'owners':o,'stock_skus':sk,'motion':rr,'physical_tested':False,'alpha_operating_deg':[-30,30],'beta_operating_deg':[-50,0],'alpha_nominal_stop_deg':[-33,33]});print('CLAVICLE','components',[(k,r['components']) for k,r in rec.items() if r['components']!=1],'fails',[(r['angles_deg'],r['findings']) for r in rr if r['findings']],flush=True)
if __name__=='__main__':main()
