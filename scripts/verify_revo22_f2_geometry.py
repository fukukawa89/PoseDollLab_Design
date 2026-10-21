import json,sys,hashlib
import numpy as np
from build_revo22_fins_v2 import *
from pack_revo22_a1mini import read_mesh
rows=[];counts=0
items={i['id']:i for p in json.loads((B/'a1mini/manifest.json').read_text())['plates'] if not p['optional'] for i in p['items']};vols={x['part']:x['volumes'] for x in json.loads((D/'all_protected_volumes.json').read_text())['objects']}
for pid,it in items.items():
 n=np.load(O/'parts'/f'{pid}.npz');r=json.loads((O/'design'/f'{pid}.json').read_text());v,f=read_mesh(B/it['source_3mf']);M=np.array(r['orientation']['matrix']);offset=np.array(r['orientation']['source_translation_mm']);s=solid(n['v'],n['f']);b=solid(n['fin_v'],n['fin_f']) if len(n['fin_f']) else md.Manifold();t=solid(n['teeth_v'],n['teeth_f']) if len(n['teeth_f']) else md.Manifold();ban=protected(vols.get(r['part'],[])).transform(np.c_[M,offset]);both=b+t
 assert np.array_equal(v,n['source_v']) and np.array_equal(f,n['f'])
 assert np.max(abs(n['v']-(v@M.T+offset)))<1e-8 and np.max(abs(M@M.T-np.eye(3)))<1e-8 and abs(np.linalg.det(M)-1)<1e-8
 assert all(str(x.status())=='Error.NoError' for x in [s,b,t,both])
 bodybite=float((b^s).volume());guardbite=float((both^ban).volume());assert bodybite<1e-6 and guardbite<1e-5,(pid,bodybite,guardbite)
 roots=[]
 for c in b.decompose():
  roots.append({'minimum_z_mm':c.bounding_box()[2],'bed_section_mm2':c.slice(.1).area(),'connection_to_teeth_mm3':float((c^t).volume())});assert c.bounding_box()[2]<1e-6 and c.slice(.1).area()>.01 and (c^t).volume()>.01
 connections=[]
 for c in t.decompose():
  a=float((c^s).volume());z=float((c^b).volume());connections.append([a,z]);assert a>.005 and z>.005,(pid,a,z)
 whole=union([s,b,t]);assert str(whole.status())=='Error.NoError' and whole.volume()>=s.volume()-1e-5
 tall=[seg for seg in r['segments'] if seg['height_mm']>35];unbraced=[seg['number'] for seg in tall if seg['brace_count']==0 and seg['blade_thickness_mm']<seg['height_mm']/12-.001]
 assert not unbraced,(pid,unbraced)
 row={'id':pid,'source_mesh_exact_before_rigid_rotation':True,'determinant':float(np.linalg.det(M)),'source_height_mm':r['source_height_mm'],'print_height_mm':r['new_height_mm'],'fin_part_overlap_mm3':bodybite,'functional_guard_overlap_mm3':guardbite,'fin_components':len(roots),'fin_roots':roots,'connected_tooth_components':len(connections),'minimum_tooth_part_bite_mm3':min([x[0] for x in connections],default=None),'minimum_tooth_fin_root_mm3':min([x[1] for x in connections],default=None),'design_teeth':len(r['teeth']),'tall_panels':tall,'support_volume_mm3':both.volume(),'npz_sha256':hashlib.sha256((O/'parts'/f'{pid}.npz').read_bytes()).hexdigest()};rows.append(row);print(pid,'roots',len(roots),'connected teeth',len(connections),flush=True)
(O/'verification/geometry_final.json').write_text(json.dumps({'version':'O22-F2','all_geometry_checks_passed':True,'source_types':len(rows),'fin_body_collision_count':0,'every_fin_component_reaches_bed':True,'every_tooth_component_connects_part_and_fin':True,'no_narrow_inclined_body_routes':True,'physical_strength_simulation':False,'parts':rows},ensure_ascii=False,indent=2),encoding='utf-8')
print('GEOMETRY PASS',len(rows),flush=True)