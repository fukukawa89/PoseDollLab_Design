import json
from stage_revo22_f5_compact296 import S
m=json.loads((S/'stage_manifest.json').read_text())
for p in m['plates']:
 if p['id']in ['D01','D02','D11','D12','D13']:
  print(p['id'],[(i['id'],i['number'],[round(x,1)for x in i['size'][:2]],i.get('has_fins'),i['source_profile']['layer'],i.get('finer_layer_for_compact_layout',False))for i in p['items']])
