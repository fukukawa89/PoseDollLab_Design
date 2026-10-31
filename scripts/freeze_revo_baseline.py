"""Create once, then verify the source and local-export fallback inventory."""
import argparse
import datetime
import subprocess
from revo_common import REPO, HW, VERIFY, save, read, sha

MANIFEST = VERIFY / 'fallback_91cm_inventory.json'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.check or MANIFEST.exists():
        old = read(MANIFEST)
        failures = [r['path'] for r in old['files']
                    if not (REPO / r['path']).is_file() or sha(REPO / r['path']) != r['sha256']]
        print(f"Fallback: {len(old['files'])} files checked; changed/missing: {len(failures)}")
        if failures:
            raise RuntimeError(failures)
        return
    files = set()
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=REPO).decode().split('\0')
    mutable = {'README.md', 'scripts/Start-Viewer.ps1'}
    for rel in tracked:
        if rel and rel not in mutable:
            files.add(REPO / rel)
    for rev in ('revM', 'revN'):
        files.update(p for p in (HW / 'generated' / rev).rglob('*') if p.is_file())
    entries = [dict(path=p.relative_to(REPO).as_posix(), bytes=p.stat().st_size, sha256=sha(p))
               for p in sorted(files) if '__pycache__' not in p.parts]
    save(MANIFEST, dict(status='FALLBACK_91CM_DIGITAL_ONLY', physical_tested=False,
         manufacturing_released=False, captured_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
         head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO).decode().strip(),
         branch=subprocess.check_output(['git', 'branch', '--show-current'], cwd=REPO).decode().strip(),
         software_worktree_preexisting_change='DollSimulation/Config/DefaultEditor.ini (untouched)',
         baseline_test_log='.local/revO-baseline-tests.log', files=entries,
         storage_note='Original local exports remain in place; this inventory is not an off-device backup.'))
    print(f'Frozen {len(entries)} files / {sum(e["bytes"] for e in entries):,} bytes')

if __name__ == '__main__':
    main()
