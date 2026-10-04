"""Paths and provenance for Rev O. Historical geometry and snapshots are read-only."""
from pathlib import Path
import hashlib
import json

REPO = Path(__file__).resolve().parents[1]
HW = REPO / 'Hardware/PoseDoll44'
OUT = HW / 'generated/revO'
VERIFY = HW / 'verification/revO'

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')

def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()
