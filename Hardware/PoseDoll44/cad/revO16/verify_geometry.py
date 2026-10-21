"""Read-only size and solid validity check of the retained O16 hardware."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
H=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(H/'cad/revO15'))
from fitted import build_fitted
p,m,st,f,pr,prov=build_fitted('quinn',{})
if f:raise ValueError(f)
b=np.array([s.bounding_box() for s in p.values()]);lo=b[:,:3].min(0);hi=b[:,3:].max(0)
bad=[k for k,s in p.items() if 'NoError' not in str(s.status())]
report={'status':'PASS' if not bad and hi[2]-lo[2]<=600 else 'FAIL','parts':len(p),
    'min_mm':lo.tolist(),'max_mm':hi.tolist(),'size_mm':(hi-lo).tolist(),
    'height_mm':float(hi[2]-lo[2]),'invalid_solids':bad,
    'source':'retained final fitted O15 exact manifold solids, neutral pose',
    'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'geometry_changed':False,'collision_checked':False,'physical_tested':False}
(H/'generated/revO16/exact_geometry_check.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
if report['status']!='PASS':sys.exit(1)
