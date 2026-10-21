"""Remove sub-micron Boolean handles from the inherited chest interface."""
from revo23_smooth import *

parts,p,cfg=load_g();N=frames(p,p['neutral_raw_deg']);key='frame/chest'
backup=GROOT/'checkpoints/before_chest_numeric_cleanup';backup.mkdir(exist_ok=True)
for name in ('assembly.npz','assembly.json','staging.json','frame__chest.npz','frame__chest.json','frame__chest_native_keep.npz'):
    if not (backup/name).exists():shutil.copy2(GROOT/name,backup/name)
rows=[]
for name in ('frame__chest_native_keep.npz','frame__chest.npz'):
    path=GROOT/name;z=np.load(path);s=solid(z['v'],z['f']);simplified=s.simplify(.00001)
    clean=union([c for c in simplified.decompose() if c.volume()>.001])
    removed=max(0.,(s-clean).volume());added=max(0.,(clean-s).volume())
    assert removed<.001 and added<.001,(name,removed,added)
    assert len(clean.decompose())==len([c for c in s.decompose() if c.volume()>.001])
    before=sha(path);save_s(path,clean)
    rows.append(dict(file=name,before_sha256=before,after_sha256=sha(path),tolerance_mm=.00001,
        removed_mm3=removed,added_mm3=added,genus_before=s.genus(),genus_after=clean.genus()))
r=read(GROOT/'frame__chest.json');r['candidate_sha256']=sha(GROOT/'frame__chest.npz');r['numeric_cleanup']=rows
put(GROOT/'frame__chest.json',r)
audit=read(GROOT/'positive_sweep_rebuild.json')
for r in audit['rows']:
    if r['key']==key:r['candidate_sha256']=sha(GROOT/'frame__chest.npz');r['numeric_cleanup']=rows
put(GROOT/'positive_sweep_rebuild.json',audit)
put(GROOT/'numeric_interface_cleanup.json',dict(rows=rows,passed=True,scope='Numerical cleanup only; no bore, axis, or nominal mounting dimension changed.'))
print(rows,flush=True)
