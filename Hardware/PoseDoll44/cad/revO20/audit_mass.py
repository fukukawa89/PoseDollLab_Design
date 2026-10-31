from base import *
from load_budget import density
from collections import Counter,defaultdict

def audit():
 p,m,pr,st,prov=load_o19();groups=defaultdict(lambda:{'count':0,'volume_mm3':0.,'estimated_mass_g':0.});rows=[]
 for k,s in p.items():
  sku=m[k]['sku'];vol=float(s.volume());d,note=density(sku);mass=vol*d*1000
  if sku in ('XIAO_ESP32S3','POLOLU_D24V22F3'):mass={'XIAO_ESP32S3':4,'POLOLU_D24V22F3':6}[sku];note='Inherited O15 provisional item mass'
  cat='print' if sku is None else 'steel' if sku.startswith(('SCREW_','NUT_','W_M','A8','SHOULDER_')) else 'electronics_or_magnet'
  groups[cat]['count']+=1;groups[cat]['volume_mm3']+=vol;groups[cat]['estimated_mass_g']+=mass
  rows.append({'part':k,'body':m[k]['body'],'sku':sku,'volume_mm3':vol,'mass_g_proxy':mass,'basis':note})
 rows.sort(key=lambda x:-x['mass_g_proxy']);print('GROUPS',dict(groups),flush=True)
 print('TOP PRINTS',[(r['part'],round(r['volume_mm3']/1000,2),round(r['mass_g_proxy'],2)) for r in rows if r['sku'] is None][:35],flush=True)
 print('COUNTS',Counter(m[k]['sku'] for k in p),flush=True)
 print('LARGEST HARDWARE',[(r['part'],round(r['mass_g_proxy'],2)) for r in rows if r['sku'] is not None][:12],flush=True)
 g.write(OUT/'baseline_mass_audit.json',{'revision':'O19','groups':dict(groups),'parts':rows,'scope':'Actual modeled assembly, existing PETG solid proxy; wires/fixtures not included in this first ranking. Not weighed mass.'})
 return p,m
if __name__=='__main__':audit()
