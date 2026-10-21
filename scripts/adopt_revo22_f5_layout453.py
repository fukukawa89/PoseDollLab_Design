import json,shutil
from search_revo22_f5_orientation268 import put
from stage_revo22_f5_compact296 import S
m=json.loads((S/'proposed_layout446.json').read_text());assert len(m['plates'])==14;shutil.copy2(S/'stage_manifest.json',S/'layout_before453.json');m['status']='All types frozen; last five whole-plate native checks pending';put(S/'stage_manifest.json',m)
