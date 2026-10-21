"""Make explicit feature recomposition the canonical H CAD assembly.

The obsolete-rod subtraction left zero-thickness skins along old sweep faces.
Rebuild from named native mounts, complete clean walls, retained wire seats,
new stems, new feet and mounting heads. All acceptance checks must be rerun.
"""
from revo23_endfaces import *
comparison=read(HROOT/'canonical_probe/comparison.json');backup=HROOT/'before_canonical_recomposition';backup.mkdir(exist_ok=True)
before=sha(HROOT/'assembly.npz')
for row in comparison['rows']:
    assert row['components']==1 and max(row['added_mm3'],row['removed_mm3'])<.03,row
    name=row['key'].replace('/','__');path=HROOT/(name+'.npz');record=path.with_suffix('.json')
    if not (backup/path.name).exists():shutil.copy2(path,backup/path.name);shutil.copy2(record,backup/record.name)
    shutil.copy2(HROOT/'canonical_probe'/path.name,path);r=read(record);r['candidate_sha256']=sha(path);r['analytic_recomposition']=row;put(record,r)
put(HROOT/'canonical_recomposition.json',dict(previous_candidate_geometry_sha256=before,rows=comparison['rows'],
    reason='Discard obsolete-rod subtraction membranes by re-union of named features. Raw numeric surface remnants are not treated as functional geometry.',
    requires_fresh_verification=True))
print('Promoted 24 explicit feature reconstructions; previous candidates preserved.')
