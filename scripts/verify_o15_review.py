"""Verify the sealed O15 review package from any clone (Python standard library)."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
HW = ROOT / 'Hardware/PoseDoll44'
RUN = HW / 'generated/revO15/runs/o15_20260929_r1'
BENCH = HW / 'bench/revO15'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def check(condition, detail):
    if not condition:
        raise ValueError(detail)


def rebase(name):
    normalized = name.replace('\\', '/')
    if '/design/' in normalized:
        normalized = normalized.split('/design/', 1)[1]
    path = (ROOT / normalized).resolve()
    check(path.is_relative_to(ROOT), f'Outside repository: {name}')
    return path


def main():
    counts = {}
    index = read(RUN / 'FINAL_EVIDENCE_INDEX.json')
    for group in ('reports_sha256', 'source_sha256'):
        for name, expected in index[group].items():
            check(sha(rebase(name)) == expected, f'Hash mismatch: {name}')
        counts[group] = len(index[group])
    firmware = read(RUN / 'firmware_builds_final.json')
    for name, expected in firmware['sources_sha256'].items():
        check(sha(rebase(name)) == expected, f'Firmware source mismatch: {name}')
    for role in firmware['roles']:
        check(sha(rebase(role['build_log'])) == role['build_log_sha256'],
              f'Firmware log mismatch: {role["role"]}')
    counts['firmware_sources'] = len(firmware['sources_sha256'])
    expected_packages = {
        'Quinn': '83981bd77a43e3ca6ae00cf691d2a072229715fc54f09c2cc00b507f0e017b36',
        'Manny': 'e80579b8bd3ac2b2960c1bd5a562b0e81753d15b79569c7e625a4b0cf09d9ebc',
    }
    counts['packages'] = []
    for character, digest in expected_packages.items():
        path = BENCH / f'PoseDoll_O15_{character}_Prototype.zip'
        check(sha(path) == digest, f'Package hash mismatch: {character}')
        with zipfile.ZipFile(path) as archive:
            check(archive.testzip() is None, f'ZIP CRC failure: {character}')
            hashes = json.loads(archive.read('PACKAGE_SHA256.json'))
            for name, expected in hashes.items():
                actual = hashlib.sha256(archive.read(name)).hexdigest()
                check(actual == expected, f'ZIP content mismatch: {character}/{name}')
            manifest = json.loads(archive.read('print_batch/manifest.json'))
            check(manifest['selected_character'] == character.lower(), 'Wrong character')
            check(len(manifest['rows']) == 214, 'Wrong print type count')
            quantity = sum(row['quantity_by_character'][character.lower()]
                           for row in manifest['rows'])
            check(quantity == 273, 'Wrong print quantity')
            counts['packages'].append({'character': character, 'files': len(archive.namelist()),
                                       'content_hashes': len(hashes), 'print_pieces': quantity})
    print(json.dumps({'status': 'PASS', 'scope': 'Sealed file integrity only; no hardware test',
                      'checked': counts}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
