from pathlib import Path
import sys,json,numpy as np,shapely
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from o22_f3_gcode import extract_detailed
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
for spec in sys.argv[1:]:
 pid,label=spec.split(':');p=O/'candidates'/pid/label;aq=p/'verification/full_bead_contacts_v5.json';aq=aq if aq.exists() else p/'verification/full_bead_contacts_v2.json';q=json.loads(aq.read_text());proj=p/'projects'/json.loads((p/'verification/local_extrusion.json').read_text())['project'];rep,raw,feature,names=extract_detailed(proj,arc_tolerance_mm=.025,max_arc_segment_mm=1.);a=np.asarray(raw).reshape(-1,9);ft=np.asarray(feature)
 for flag in q['external_islands']+q['critical_external_runs']:
  b=flag['bounds_mm'];z=flag['z_mm'];m=(abs(a[:,5]-z)<.002)&(a[:,7]==0)&(np.minimum(a[:,0],a[:,3])<b[2]+.1)&(np.maximum(a[:,0],a[:,3])>b[0]-.1)&(np.minimum(a[:,1],a[:,4])<b[3]+.1)&(np.maximum(a[:,1],a[:,4])>b[1]-.1);idx=np.flatnonzero(m);print(pid,z,'features',[(names[j],sum(ft[idx]==j))for j in np.unique(ft[idx])],flush=True)
