from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from repair_revo22_f4_clean_chamfer import trial
from verify_revo22_f4_body_change import check as fit
from verify_revo22_f4_repaired_geometry import check as geom
pid='X042';parent='chamfer_precise_05'
for j in range(1,3):
 label='bounded25_'+str(j).zfill(2);d=trial(pid,parent,label)
 if d['native_review_resolved']:fit(pid,label);geom(pid,label);break
 parent=label
