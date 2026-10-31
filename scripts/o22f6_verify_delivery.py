import csv,json,zipfile,hashlib
from pathlib import Path
b=Path('PoseDoll_HW44_Plan/design/Hardware/PoseDoll44/bench/revO22');d=b/'O22F6_HoleClear';m=json.loads((d/'manifest.json').read_text());rows=list(csv.DictReader((d/'零件与打印盘对照.csv').open(encoding='utf-8-sig',newline='')));assert len(rows)==193 and all((d/q['project']).exists()for q in rows);assert len(m['plates'])==14 and len(m['rows'])==150;assert not m['complete']
checks=0
with zipfile.ZipFile(b/'O22F6_HoleClear_候选_未放行_20261015.zip')as z:
 for line in z.read('O22F6_HoleClear/SHA256SUMS.txt').decode().splitlines():
  want,path=line.split('  ',1);assert hashlib.sha256(z.read('O22F6_HoleClear/'+path)).hexdigest()==want,path;checks+=1
 assert sum(x.startswith('O22F6_HoleClear/projects/')and x.endswith('.3mf')for x in z.namelist())==14
r=dict(zip_files_hash_verified=checks,mapping_rows=193,all_mapping_project_links_exist=True,projects=14,types=150,status='HOLD_NOT_RELEASED');(b/'diagnostics/O22F6_holeclear_20261015/delivery_integrity.json').write_text(json.dumps(r,indent=2));print(r)
summary=json.loads((d/'verification/summary.json').read_text());print({k:summary[k]for k in ['source_types_with_support_intrusion','support_geometry_changed_types','guard_envelopes','native_passed_plates','external_islands','critical_external_runs']})
print('ZIP_MiB',round((b/'O22F6_HoleClear_候选_未放行_20261015.zip').stat().st_size/1048576,1))