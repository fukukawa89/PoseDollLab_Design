"""Locate native review regions relative to exact preceding solid geometry.
This is context, not an exemption from native checking or print certification.
"""
from pathlib import Path
import json,sys,numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,union,md
from o22_cross_section_geometry import polygon
from shapely.geometry import box
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def context(pid,label,lh=.2):
 folder=O/'candidates'/pid/label;n=np.load(folder/'parts'/f'{pid}.npz');it=json.loads((folder/'verification/plate_manifest.json').read_text())['items'][0];M=np.array(it['rotation_matrix']);t=np.array(it['translation_mm']);whole=union([solid(n[v],n[f]) for v,f in [('v','f'),('fin_v','fin_f'),('teeth_v','teeth_f')] if len(n[f])]).transform(np.c_[M,t]);part=solid(n['v'],n['f']).transform(np.c_[M,t]);rep=json.loads((folder/'verification/local_extrusion.json').read_text());cache={};rows=[]
 for kind,ls in [('detached',rep['detached_bead_regions']),('span',rep['unresolved_spans'])]:
  for r in ls:
   z=round(r['z_mm'],4)
   if z not in cache:
    prev=polygon(whole.slice(max(.01,z-lh*1.5)));current=polygon(part.slice(z-lh*.5));cache[z]=(prev,current)
   prev,current=cache[z];bb=r['bounds_mm'];region=box(bb[0]-.015,bb[1]-.015,bb[2]+.015,bb[3]+.015);f0=region.intersection(prev).area/region.area;f1=region.intersection(prev.buffer(lh)).area/region.area;pb=region.intersection(current).area/region.area
   q=dict(r,kind=kind,previous_solid_geometry_bbox_coverage=f0,previous_solid_plus_one_layer_bbox_coverage=f1,current_part_bbox_coverage=pb)
   q['context']='inside_prior_solid_infill_region' if f0>.995 else 'one_layer_geometric_overhang' if f1>.995 else 'external_or_cavity_region';rows.append(q)
 d={'id':pid,'label':label,'layer_height_mm':lh,'note':'Context only. A span over the previous model solid may be normal infill bridging; an external cavity roof remains external. Native flags are retained.','regions':rows};(folder/'verification/native_region_context.json').write_text(json.dumps(d,indent=2));return d
if __name__=='__main__':
 for spec in sys.argv[1:]:
  fields=spec.split(':');d=context(fields[0],fields[1],float(fields[2]) if len(fields)>2 else .2);from collections import Counter;print(d['id'],Counter(q['context'] for q in d['regions']),flush=True)
