"""Verify the candidate archive with Python standard library only."""
from pathlib import Path
import hashlib,json,sys,zipfile

def sha(data):return hashlib.sha256(data).hexdigest()

def verify(root):
    manifest=json.loads((root/'FILES_SHA256.json').read_text(encoding='utf-8-sig'))
    failures=[]
    for name,digest in manifest['files'].items():
        p=(root/name).resolve()
        if not p.is_relative_to(root.resolve()) or not p.is_file() or sha(p.read_bytes())!=digest:
            failures.append(name)
    p=json.loads((root/'profiles/device_profile.json').read_text(encoding='utf-8-sig'))
    bom=json.loads((root/'print_batch/manifest.json').read_text(encoding='utf-8-sig'))
    assert p['hardware_models']==['universal'] and len(set(p['raw_order']))==46
    assert len(bom['rows'])==214 and sum(r['quantity_by_character']['universal'] for r in bom['rows'])==273
    assert all(set(r['quantity_by_character'])=={'universal'} for r in bom['rows'])
    assert not p['physical_collision_domain_certified']
    for r in bom['rows']:
        assert (root/r['stl']).is_file()
        assert sha((root/r['stl']).read_bytes())==r['stl_sha256']
    archive=root/'PoseDoll_O16_Universal_Design.zip';zipped=None
    if archive.exists():
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            assert set(z.namelist())==set(manifest['files'])|{'FILES_SHA256.json'}
            for name,digest in manifest['files'].items():
                if sha(z.read(name))!=digest: failures.append('ZIP:'+name)
        zipped=sha(archive.read_bytes())
    result={'status':'PASS' if not failures else 'FAIL','files_checked':len(manifest['files']),
        'failures':failures,'single_hardware_model':True,'print_types':214,'print_pieces':273,
        'zip_sha256':zipped,'physical_qualification':False}
    if failures: raise ValueError(result)
    return result

if __name__=='__main__':
    here=Path(__file__).resolve().parent
    root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else (
        here.parent if (here.parent/'FILES_SHA256.json').exists() else here.parents[1]/'bench/revO16')
    print(json.dumps(verify(root),ensure_ascii=False,indent=2))
