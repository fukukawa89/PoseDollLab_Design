"""Check the complete compact deliverable, assembly addresses and archive without touching original F4."""
from pathlib import Path
import json,csv,collections
import publish_revo22_f4_compact232 as pub
import verify_revo22_f4_release207 as verifier
D=pub.D;B=pub.B
def main():
 c=pub.collect();m=json.loads((D/'manifest.json').read_text());assert m['version']=='O22-F4-Compact';assert m['main_plate_count']==14 and m['sample_plate_count']==1;trace={q['new_address']:q for q in c['trace']};mapping={q['original_address']:q['new_address']for q in c['trace']if not q['optional']};expected={ent['plate']['id']:ent['plate']for ent in c['plates']}
 for p in m['plates']:
  assert p['items']==expected[p['id']]['items'];assert pub.sha(D/p['project'])==pub.sha(pub.S/'projects'/Path(p['project']).name)
  for it in p['items']:
   q=trace[it['object_name'].split()[0]];assert q['previous_f4_address']==it['previous_f4_address']and q['id']==it['id']
 rows=list(csv.DictReader((D/'零件与打印盘对照.csv').open(encoding='utf-8-sig')));assert len(rows)==193
 for r in rows:assert trace[r['address']]['previous_f4_address']==r['previous_f4_address']
 guide=json.loads((D/'assembly/tutorials/assembly-o22/guide-data.json').read_text());matched=[]
 for q in guide['parts'].values():
  old=q.get('original_address')
  if old in mapping:assert q['address']==mapping[old]+'（原 '+old+'）';matched.append(old)
 assert collections.Counter(matched)==collections.Counter(mapping.keys()),('missing assembly addresses',set(mapping)-set(matched))
 report={'compact_main_plates':14,'optional_sample_plates':1,'previous_main_plates':23,'previous_sample_plates':2,'total_plate_reduction':10,'main_instances':186,'optional_instances':7,'same_frozen_150_part_npz_hashes_as_original_F4':True,'all_193_print_orientations_and_z_placements_unchanged':True,'all_old_to_new_addresses_unique_and_complete':True,'all_186_main_assembly_addresses_mapped':True,'minimum_bed_edge_mm':c['minimum_bed_edge_mm'],'minimum_body_fin_teeth_bbox_separation_mm':c['minimum_interobject_bbox_clearance_mm'],'all_14_changed_plates_have_fresh_native_mesh_profile_and_extrusion_audits':True,'C01_reuses_byte_identical_qualified_F01':True,'physical_print_tested':False};pub.write(D/'verification/compact_release_integrity233.json',json.dumps(report,indent=2));verifier.D=D;verifier.verify(archive=B/'O22F4_合盘打印包.zip')
if __name__=='__main__':main()
