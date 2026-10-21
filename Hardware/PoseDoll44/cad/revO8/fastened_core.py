"""Add explicit nominal M1.6 x 6 fasteners to the recovered split ring.
Threads are envelopes; no thread preload or material strength qualification.
"""
import json,itertools,hashlib
import numpy as np
import cadquery as cq
from reference_assembly import OUT,at_pose,rot
from mesh_collision import compare
from extend_forks import stl

def tess(shape):
 v,f=shape.tessellate(.015,.08);v=np.array([x.toTuple() for x in v]);return v[np.array(f)]

def fasteners():
 parts={};tools={};spec=[]
 for i,(x,y) in enumerate(itertools.product((-7.,7.),repeat=2)):
  # At same-sign corners head is on +Z; opposite-sign corners reversed.
  s=1 if x*y>0 else -1
  screw=cq.Workplane('XY').workplane(offset=-4).circle(.8).extrude(6).union(cq.Workplane('XY').workplane(offset=2).circle(1.5).extrude(1.6)).val()
  # Closed thread-major envelope; nut hole enlarged only for collision bookkeeping.
  nut=cq.Workplane('XY').workplane(offset=-2.9).polygon(6,3.2/np.cos(np.pi/6)).circle(.81).extrude(1.3).val()
  screw=screw.rotate((0,0,0),(1,0,0),180 if s<0 else 0).translate((x,y,0));nut=nut.rotate((0,0,0),(1,0,0),180 if s<0 else 0).translate((x,y,0))
  parts[f'screw_{i+1}']=tess(screw);parts[f'nut_{i+1}']=tess(nut)
  # Access volume: 1.5 mm AF hex key circumscribed cylinder, minimum exposed 20 mm shaft.
  tool=cq.Workplane('XY').workplane(offset=3.6).circle(.87).extrude(20).val();tool=tool.rotate((0,0,0),(1,0,0),180 if s<0 else 0).translate((x,y,0));tools[f'key_{i+1}']=tess(tool)
  spec.append({'corner':[x,y],'head_side':s,'head_seat_z_mm':2*s,'under_head_length_mm':6,'thread_pitch_mm':.35,'nominal_nut_engagement_length_mm':1.3,'thread_end_z_mm':-4*s,'nut_af_mm':3.2,'nut_thickness_mm':1.3,'head_diameter_mm':3,'head_height_mm':1.6,'tool_af_mm':1.5})
 return parts,tools,spec

def main():
 base=OUT.parent/'fork_extension_2mm';core=dict(np.load(base/'core_meshes.npz'));parts,tools,spec=fasteners();out=OUT.parent/'fastened_core';out.mkdir(exist_ok=True)
 np.savez_compressed(out/'fasteners.npz',**parts);np.savez_compressed(out/'tools.npz',**tools)
 for n,t in parts.items():stl(out/(n+'.stl'),t)
 # Neutral ring-seat verification. Bearing contacts allowed only if not penetrating.
 fits=[]
 for n,t in parts.items():
  for ring in ('C14','C15'):
   r=compare(t,core[ring]);fits.append({'fastener':n,'ring':ring,**r})
 print('FIT',[(r['fastener'],r['ring'],r['status']) for r in fits],flush=True)
 moving=np.concatenate(list(parts.values()));cases=[]
 angles=[(a,0) for a in range(-100,101,10)]+[(0,b) for b in range(-100,101,10) if b]+list(itertools.product((-60,-30,30,60),repeat=2))
 for alpha,beta in angles:
  m=at_pose(core,alpha,beta);fixed=moving@rot([1,0,0],alpha).T;findings=[]
  for n in ('C01','C02'):
   r=compare(fixed,m[n]);
   if r['status']!='CLEAR_NOMINAL_MESH':findings.append({'yoke':n,**r})
  status='FAIL' if any(r['status']=='PENETRATION' for r in findings) else 'REVIEW' if findings else 'CLEAR_FASTENERS_ONLY';cases.append({'alpha_deg':alpha,'beta_deg':beta,'status':status,'findings':findings});print(alpha,beta,status,flush=True)
 access=[]
 for n,t in tools.items():
  found=None;attempts=[]
  for alpha,beta in [(0,0)]+list(itertools.product((-60,-40,40,60),repeat=2)):
   m=at_pose(core,alpha,beta);key=t@rot([1,0,0],alpha).T;r=[compare(key,m[p]) for p in ('C01','C02')];attempts.append({'alpha_deg':alpha,'beta_deg':beta,'statuses':[x['status'] for x in r]})
   if all(x['status']=='CLEAR_NOMINAL_MESH' for x in r):found={'alpha_deg':alpha,'beta_deg':beta};break
  access.append({'tool':n,'clear_straight_shaft_pose':found,'attempts':attempts});print('ACCESS',n,found,flush=True)
 report={'scope':'Nominal split-ring fasteners only. Threads represented by envelopes; engagement length is not thread strength. Tool check covers a 20 mm exposed 1.5 AF straight hex shaft, not every commercial handle or approach sweep.','spec':spec,'ring_fits':fits,'motion_cases':cases,'tool_access':access,'source_sha256':hashlib.sha256((base/'core_meshes.npz').read_bytes()).hexdigest(),'physical_tested':False,'manufacturing_released':False}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
