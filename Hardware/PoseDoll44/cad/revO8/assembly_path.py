"""Staged assembly translations for four core plastic pieces; finite samples only."""
import json, numpy as np
from reference_assembly import OUT
from mesh_collision import compare

def main():
 core=dict(np.load(OUT.parent/'fork_extension_2mm/core_meshes.npz'));rows=[]
 stages=[('interleave_yokes','C02',['C01'],[np.array([0,0,z]) for z in np.linspace(30,0,31)]),('lower_ring_side_entry','C14',['C01','C02'],[np.array([0,y,-7]) for y in np.linspace(-30,0,31)]),('lower_ring_seat','C14',['C01','C02'],[np.array([0,0,z]) for z in np.linspace(-7,0,15)]),('upper_ring_side_entry','C15',['C01','C02','C14'],[np.array([x,0,7]) for x in np.linspace(30,0,31)]),('upper_ring_seat','C15',['C01','C02','C14'],[np.array([0,0,z]) for z in np.linspace(7,0,15)])]
 for name,part,others,offsets in stages:
  cases=[]
  for offset in offsets:
   moved=core[part]+offset;findings=[]
   for other in others:
    b=core[other]
    if np.any(np.minimum(moved.max((0,1)),b.max((0,1)))-np.maximum(moved.min((0,1)),b.min((0,1)))<0):continue
    r=compare(moved,b)
    # Only the final mating plane of the ring halves is intentionally in contact.
    intended=part=='C15' and other=='C14' and np.linalg.norm(offset)<1e-8 and r['status']=='CONTACT_REQUIRES_REVIEW'
    if r['status']!='CLEAR_NOMINAL_MESH':findings.append({'other':other,'intended_final_plane_contact':bool(intended),**r})
   status='FAIL' if any(x['status']=='PENETRATION' for x in findings) else 'REVIEW' if any(not x['intended_final_plane_contact'] for x in findings) else 'PASS_DISCRETE_ASSEMBLY_STEP'
   cases.append({'offset_mm':offset.tolist(),'status':status,'findings':findings})
  row={'stage':name,'part':part,'obstacles':others,'cases':cases};rows.append(row);print(name,[(x['offset_mm'],x['status']) for x in cases if x['status']!='PASS_DISCRETE_ASSEMBLY_STEP'],flush=True)
  (OUT.parent/'assembly_path.json').write_text(json.dumps({'scope':'Discrete 0.5-1 mm translations of four plastic parts. This is a nominal staged assembly candidate, not a continuous/tolerance or hand-clearance proof. No retention before screws.','stages':rows,'physical_tested':False,'manufacturing_released':False},indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
