"""Run unchanged native-extrusion audit stages on the independent R2 study root."""
import sys,runpy,json
from pathlib import Path
from build_revo22_x062_r2_262 import S,R
import build_revo22_x062_open242 as cfg
cfg.S=S
label=sys.argv[1]
runpy.run_path(str(R/'scripts/audit_revo22_x062_trial243.py'),run_name='__main__')
p=S/'candidates/X062'/label/'verification'
if not(p/'full_bead_contacts_v5.json').exists():
 src=next(p/n for n in ['full_bead_contacts_v4.json','full_bead_contacts_v2.json','full_bead_contacts.json']if(p/n).exists());(p/'full_bead_contacts_v5.json').write_bytes(src.read_bytes())
runpy.run_path(str(R/'scripts/verify_revo22_x062_endpoints256.py'),run_name='__main__')
