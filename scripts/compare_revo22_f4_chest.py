from pathlib import Path
import sys,json,numpy as np,math
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import box,md
B=R/'Hardware/PoseDoll44/bench/revO22';O=B/'a1mini_fins_v4';out=[]
source_plate=next(p for p in json.loads((B/'O22F3_Release/manifest.json').read_text(encoding='utf8'))['plates'] if p['id']=='F01')['items'][0]
candidate_plate=json.loads((O/'candidates/X046/cov_00/verification/plate_manifest.json').read_text(encoding='utf8'))['items'][0]
for label,folder,report,place in [('F3',B/'O22F3_Release/reference',O/'audit/native_baseline/Orca/F01_O22F3_PLA_fins.json',source_plate),('candidate_cov_00',O/'candidates/X046/cov_00',O/'candidates/X046/cov_00/verification/local_extrusion.json',candidate_plate)]:
 d=json.loads((folder/'design/X046.json').read_text(encoding='utf8'));M=np.array(d['orientation']['matrix']);t=np.array(d['orientation']['source_translation_mm']);P=np.array(place['rotation_matrix']);T=np.array(place['translation_mm']);band=box([8.5,10.5,1.6],[30.5,105.5,2.1]).transform(np.c_[P@M,P@t+T]);angle=math.degrees(math.acos(abs(M[2,2])));rep=json.loads(report.read_text(encoding='utf8'));assert rep['audit_schema']=='local-extrusion-v2-preserve-nested-islands';hits=[]
 for q in rep['unresolved_spans']:
  b=q['bounds_mm'];patch=md.CrossSection.square([max(.002,b[2]-b[0]),max(.002,b[3]-b[1])]).translate([b[0],b[1]])
  if (band.slice(q['z_mm']-.1)^patch).area()>1e-7:hits.append(q)
 r={'version':label,'audit_schema':rep['audit_schema'],'source_project_sha256':rep['project_sha256'],'ceiling_inclination_from_horizontal_deg':angle,'nominal_layer_advance_at_0p2mm_mm':.2/math.tan(math.radians(angle)),'roof_adjacent_flagged_path_regions':len(hits),'maximum_associated_path_length_mm':max((x['length_mm'] for x in hits),default=0),'associated_regions':hits,'association_method':'Flagged path bounding boxes at the layer mid-plane intersected with the interior ceiling band in original source coordinates x8.5..30.5/y10.5..105.5/z1.6..2.1. Locates adjacent flags only; not physical qualification.'};out.append(r);print({k:v for k,v in r.items() if k not in ['associated_regions','association_method']})
(O/'review/evidence/chest_comparison.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')

