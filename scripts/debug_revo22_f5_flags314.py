import json,numpy as np,shapely
from search_revo22_f5_orientation268 import O
from optimize_revo22_f5_276 import candidates
from build_revo22_fins import solid
from o22_cross_section_geometry import polygon
for pid in ['P033','P049','P051','P071','P073','P130','W006','W016','W017','X038','X046','X054','X058','X066','X073','X080']:
 cc=[x for x in candidates(pid)if not x[4].get('part_body_modified_from_F4')];label=cc[0][2];a=O/'candidates'/pid/label;r=json.loads((a/'verification/native_final.json').read_text());it=json.loads((a/'verification/plate_manifest.json').read_text())['items'][0];M=np.array(it['rotation_matrix']);t=np.array(it['translation_mm']);n=np.load(a/'parts'/f'{pid}.npz');ss={k:solid(n[v],n[f])for k,v,f in [('body','v','f'),('fin','fin_v','fin_f'),('teeth','teeth_v','teeth_f')]};print(pid,label,'I',r['external_island_count'],'R',r['critical_external_count'])
 for q in(r['external_islands']+r['critical_external_runs'])[:4]:
  b=q['bounds_mm'];z=q['z_mm'];p=(np.array([(b[0]+b[2])/2,(b[1]+b[3])/2,z])-t)@M;roi=shapely.box(p[0]-.5,p[1]-.5,p[0]+.5,p[1]+.5);area={k:round(polygon(s.slice(float(p[2]-.3))).intersection(roi).area,3)for k,s in ss.items()};print(' ',np.round(p,3).tolist(),area,q.get('area_mm2'),q.get('length_mm'),q.get('cad_previous_coverage'))
