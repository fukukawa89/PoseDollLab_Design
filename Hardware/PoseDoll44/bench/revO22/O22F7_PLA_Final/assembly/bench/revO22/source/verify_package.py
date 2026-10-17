"""Read-only local O21 package checksum verification."""
from pathlib import Path
import hashlib,json,sys,zipfile
root=Path(__file__).resolve().parent.parent
files=json.loads((root/'FILES_SHA256.json').read_text(encoding='utf-8-sig'))['files']
bad=[]
for name,digest in files.items():
    path=root/name
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:bad.append(name)
archive=root/'PoseDoll_O21_CostDown_Design.zip'
if archive.exists():
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:bad.append('ZIP CRC')
        for name,digest in files.items():
            if hashlib.sha256(z.read(name)).hexdigest()!=digest:bad.append('ZIP:'+name)
print(json.dumps({'status':'FAIL' if bad else 'PASS','files':len(files),'mismatches':bad,'manufacturing_release':False},indent=2))
sys.exit(bool(bad))
