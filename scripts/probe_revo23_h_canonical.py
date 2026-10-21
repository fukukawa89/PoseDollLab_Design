"""Measure subtraction residue before proposing an analytic recomposition."""
from repair_revo23_endfaces import *
parts,p,cfg=load_h();N=frames(p,p['neutral_raw_deg']);rows=[]
dest=HROOT/'canonical_probe';dest.mkdir(exist_ok=True)
for key,item in parts.items():
    if item['role']!='structure':continue
    old=item['s'];M=N[item['token']]
    candidate=move(preserved_material(key,parts,p,N,False)+structural_connectors(connection_records(key)['rods']),np.linalg.inv(M))
    cc=[c for c in candidate.decompose() if c.volume()>.001]
    removed=max(0.,(old-candidate).volume());added=max(0.,(candidate-old).volume())
    r=dict(key=key,removed_mm3=removed,added_mm3=added,components=len(cc),old_volume_mm3=old.volume())
    rows.append(r);save_s(dest/(key.replace('/','__')+'.npz'),union(cc));print(r,flush=True)
put(dest/'comparison.json',dict(rows=rows))
