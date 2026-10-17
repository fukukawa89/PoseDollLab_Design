from pathlib import Path
import sys,json,hashlib
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_x062_open242 import S
import slice_revo22_f4_candidate as runner
import verify_revo22_f4_full_bead as full
import o22_recover_native_flag_paths as recover
import refine_revo22_f4_full_bead as finer
import refine_revo22_f4_islands84 as exact
import refine_revo22_f4_lateral104 as lateral
from verify_revo22_f3_native_mesh import check as meshcheck
label=sys.argv[1];folder=S/'candidates/X062'/label;vp=folder/'verification';runner.O=S
if not (vp/'local_extrusion.json').exists():runner.run('X062',label)
plate=json.loads((vp/'plate_manifest.json').read_text());native=next((folder/'projects').glob('*.3mf'));source=R/'.local/o22-fins-v4/candidates/X062'/label/plate['id']/'input.3mf'
meshcheck(plate,path=native,source=source,report_dir=vp,expected_layer_height=json.loads((folder/'design/X062.json').read_text())['required_layer_height_mm'])
for module in [full,recover,finer,exact,lateral]:module.O=S
if not (vp/'full_bead_contacts.json').exists():full.check('X062',label)
d=finer.refine('X062',label)
if d['external_islands']:d=exact.trial('X062',label)
if d['critical_external_runs']:d=lateral.check('X062',label)
print('X062_TRIAL_NATIVE',label,d['native_review_resolved'],d['external_island_count'],d['critical_external_count'],flush=True)

