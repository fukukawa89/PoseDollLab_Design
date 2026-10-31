"""Dual-axis printed core with both complete magnetic encoders.
The mechanical core comes from sealed O13; O15 adds retained cups and PCBA supports.
"""
from common import *
import hinge
G13=H/'generated/revO13/runs/o13_20260929_r1';G8=H/'generated/revO8/runs/o8_20260925_r1'
def make(signs=(1,1),phases=(0,180),extensions=(0,0),wide=False,rear_second=False):
 old={k:from_tri(t) for k,t in np.load(G13/'printed_core/parts.npz').items()};hp,ho,hs=hinge.make();p={};o={};sku={}
 stock={'inner_M4_wide':'W_M4_D12_T1','outer_M4_wide':'W_M4_D12_T1','front_M4_washer':'W_M4_D9_T0P8','spring_1':'A8_SS','spring_2':'A8_SS','shoulder_D4_L8_M3_thread6':'SHOULDER_D4_L8_M3_L6','M3_nut':'NUT_M3','M3_reaction_washer':'W_M3_D9_T0P8'}
 for k,s in old.items():
  if k in ('C01','C02') and extensions[0 if k=='C01' else 1]:
   tt=tri(s);direction=-1 if k=='C01' else 1;tt[:,:,2]+=direction*extensions[0 if k=='C01' else 1]*np.clip((direction*tt[:,:,2]-8)/6,0,1);s=from_tri(tt)
  p[k]=s;o[k]=k if k in ('C01','C02') else 'ring';sku[k]=None if k in ('C01','C02','C14','C15') else next(v for a,v in stock.items() if k.endswith(a))
 # Side encoders replace the old central magnet pin and square tray.
 # Leaving this obsolete pin would trap the lower bearing half during assembly.
 p['C01']-=cyl(1.25,-20-extensions[0],0)+box([-4.1,-4.1,-2.6],[4.1,4.1,1.6])
 for k,t in np.load(G8/'fastened_core/fasteners.npz').items():p['ring_'+k]=from_tri(t);o['ring_'+k]='ring';sku['ring_'+k]='NUT_M1P6' if 'nut' in k.lower() else 'SCREW_M1P6_L6'
 frames=[];attachments=md.Manifold()
 for i,(key,sgn,phase,e) in enumerate(zip(('C01','C02'),signs,phases,extensions)):
  Z=np.eye(3)[i]*sgn;X=np.array([0,0,-1 if i==0 else 1]);Y=np.cross(Z,X);M=np.c_[X,Y,Z]@rot(2,phase);pos=Z*16;frames.append((M,pos))
  def tr(s):return pose(s,M,pos)
  # Compact retained cup: keyed to the printed fork, no adhesive or metal machining.
  cup=washer(8.5,6.3,1.4,8.4)
  seat=cyl(6.2,8.4,10.6)+cyl(8.5,9.8,10.6)
  seat-=cyl(3.1,10.4,10.7)+cyl(1.9,8.3,10.7)
  cup+=box([6.4,-2,-.8],[12,2,2.2])
  cap=cyl(8.5,10.6,13.1)-cyl(3.075,10.5,12.95)-cyl(2.9,12.8,13.2)
  extras={}
  for xx in (-6.1,6.1):
   seat-=cyl(1.15,8.3,10.7).translate([xx,0,0])
   cup-=cyl(1.1,5.9,10.7).translate([xx,0,0]);cup-=hexagon(4.3,6.1,7.8).translate([xx,0,0]);cup-=box([6 if xx>0 else -10,-2.2,6.05],[10 if xx>0 else -6,2.2,7.8])
   cap-=(cyl(1.15,10.5,13.2)+cyl(2.05,11.1,13.2)).translate([xx,0,0])
   extras[f'magnet_nut_{xx}']=(nut(2,4,1.6,6.2).translate([xx,0,0]),key,'NUT_M2')
   extras[f'magnet_screw_{xx}']=(screw(2,5,3.8,2,11.1).translate([xx,0,0]),key,'SCREW_M2_L5')
  # Cup frame follows the fork stem, independently of fixed support placement.
  MC=np.c_[X,Y,Z]
  p[key]+=pose(cup,MC,pos)
  for kk,(ss,oo,sk) in extras.items():p[key+'_'+kk]=pose(ss,MC,pos);o[key+'_'+kk]=oo;sku[key+'_'+kk]=sk
  p[key+'_magnet_seat']=pose(seat,MC,pos);o[key+'_magnet_seat']=key;sku[key+'_magnet_seat']=None
  p[key+'_magnet_cap']=pose(cap,MC,pos);o[key+'_magnet_cap']=key;sku[key+'_magnet_cap']=None
  p[key+'_magnet']=pose(cyl(3,10.4,12.9),MC,pos);o[key+'_magnet']=key;sku[key+'_magnet']='MAGNET_D6_T2P5_DIAMETRIC'
  holder=hp['base_sensor_half']-box([-50,-50,-50],[50,50,-2.5])
  anchor=np.array([6,-9,-3]) if i==0 else np.array([9,6,-3])
  tip=M@np.array([-13.5,-13.5,-2.4])+pos
  via=np.array([13.8,-11.5,-3]) if i==0 else np.array([11.5,13.8,-3])
  if wide and i==0:
   holder=holder^box([-50,-50,10.5],[50,50,50]);anchor=np.array([6,-9,-5]);via=np.array([27,-9,-5]);tip=np.array([27,-13.5,13.5]);attachments+=tr(holder)+beam(anchor,via,1.3)+beam(via,tip,1.3)
  elif rear_second and i==1:
   holder=holder^box([-50,-50,10.5],[50,50,50]);anchor=np.array([-9,0,-6.5]);via=np.array([-9,27,-6.5]);tip=np.array([-13.5,27,-13.5]);attachments+=tr(holder)+beam(anchor,via,1.3)+beam(via,tip,1.3)
  else:attachments+=tr(holder)+beam(anchor,via,1.8)+beam(via,tip,1.8)
  for k,ss in hp.items():
   if k.startswith(('sensor_','passive_','pcb_')):p[key+'_'+k]=tr(ss);o[key+'_'+k]='ring';sku[key+'_'+k]=hs[k]
 # Preserve mating-half clearance and the real fastener insertion bores.
 for k in ['C15']+[kk for kk in p if kk.startswith('ring_') or ('pcb_clip_' in kk and (wide or rear_second))]:
  clearance=p[k]
  for ax in range(3):
   for ss in (-1,1):clearance+=p[k].translate(np.eye(3)[ax]*ss*.15)
  attachments-=clearance
 p['C14']+=attachments
 return p,o,sku

def frames(a,b):return {'ring':np.eye(3),'C01':rot(0,a),'C02':rot(1,b)}
def main():
 p,o,s=make(); rec={k:mesh_record(v) for k,v in p.items()};nom=hits(p)
 motion=[]
 for a,b in itertools.product((-25,0,25),(-95,-60,0,60,95)):
  fs=frames(a,b);pp={k:pose(v,fs[o[k]]) for k,v in p.items()};hh=[h for h in hits(pp) if o[h['pair'][0]]!=o[h['pair'][1]]];motion.append({'angles_deg':[a,b],'findings':hh})
 save('core_build.json',{'parts':rec,'owners':o,'stock_skus':s,'nominal_findings':nom,'motion':motion,'physical_tested':False});np.savez_compressed(OUT/'core_parts.npz',**{k:tri(v) for k,v in p.items()})
 print('core',len(p),'components',[(k,r['components']) for k,r in rec.items() if r['components']!=1], 'nominal',nom,'motion',[(x['angles_deg'],len(x['findings'])) for x in motion],flush=True)
if __name__=='__main__':main()
