import json,traceback
from build_revo22_fins_v2 import O
from check_revo22_f2_layers import check
for f in sorted((O/'parts').glob('*.npz')):
 if f.stem in ['P033','W016','X046','X005','X045','P035','X050','H004']:continue
 try:check(f.stem)
 except Exception:print('ERROR',f.stem,traceback.format_exc(),flush=True)
print('ALL CHECKS COMPLETE',flush=True)