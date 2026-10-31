"""Ankle variant: vertical input stem and rear-routed sensor supports.
Application stops bound both bends before neighbouring foot/toe hardware.
"""
from common import *
import core,twist

def make():
 p,o,sk=core.make(phases=(0,0),wide=True,rear_second=True)
 AX=np.array([[1,0,0],[0,0,1],[0,-1,0]])
 for side in (-1,1):
  stop=twist.sector(6.35,7.85,54,104,11.35,13.5)+twist.sector(6.35,7.85,-104,-54,11.35,13.5)
  stop=pose(pose(stop,rot(0,180)) if side<0 else stop,AX)
  p['C14']+=stop^box([-60,-60,-60],[60,60,0]);p['C15']+=stop^box([-60,-60,0],[60,60,60])
 # Local outside-yoke relief for the opposing encoder cup. Its radius includes
 # a 1 mm nominal guard; no bearing seat or fastener pocket is removed.
 envelope=pose(cyl(9.5,16.5,30.1),rot(1,90))
 for b in range(20,47):p['C02']-=pose(envelope,rot(1,-b))
 p['C01']=p['C01']^box([-60,-60,-20],[60,60,60])
 return p,o,sk

def main():
 p,o,sk=make();rec={k:mesh_record(v) for k,v in p.items()};rr=[]
 for a,b in itertools.product((-25,-15,0,15,25),(-45,-30,-15,0,15,30,45)):
  fs={'C01':rot(0,a),'C02':rot(1,b),'ring':np.eye(3)};hh=hits({k:pose(v,fs[o[k]]) for k,v in p.items()});rr.append({'angles_deg':[a,b],'findings':hh})
 np.savez_compressed(OUT/'ankle_core_parts.npz',**{k:tri(v) for k,v in p.items()});save('ankle_core_build.json',{'parts':rec,'owners':o,'stock_skus':sk,'motion':rr,'physical_tested':False,'alpha_operating_deg':[-25,25],'beta_operating_deg':[-45,45],'beta_nominal_stop_deg':[-48,48]});print('ANKLE','components',[(k,r['components']) for k,r in rec.items() if r['components']!=1],'fails',[(r['angles_deg'],r['findings']) for r in rr if r['findings']],flush=True)
if __name__=='__main__':main()
