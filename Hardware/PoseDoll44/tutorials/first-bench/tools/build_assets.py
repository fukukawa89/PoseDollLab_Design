"""Build the beginner guide's offline CAD views and handoff files; never edit O7."""
from pathlib import Path
import hashlib, json, zipfile
import cadquery as cq
ROOT = Path(__file__).resolve().parents[1]
H = ROOT.parents[1]
BENCH = H / 'bench/revO7'
ASSETS = ROOT / 'assets'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    models, sources = {}, {}
    for family in ['LP6', 'M4']:
        for role in ['PEEK_coupon', 'metal_counterface']:
            name = family + '_' + role
            p = BENCH / 'coupons' / (name + '.step')
            before = sha(p)
            solid = cq.importers.importStep(str(p)).val()
            vertices, faces = solid.tessellate(.12, .18)
            models[name] = {'vertices': [[round(x, 5) for x in v.toTuple()] for v in vertices], 'faces': faces, 'source_sha256': before, 'units': 'mm'}
            assert before == sha(p)
            sources[str(p.relative_to(H))] = before
    plan = json.loads((BENCH / 'plan.json').read_text(encoding='utf-8'))
    for name in ['plan.json', 'coupons/LP6_dimensions.json', 'coupons/M4_dimensions.json', 'measurement_template.json', 'spring_curve_template.json']:
        sources['bench/revO7/' + name] = sha(BENCH / name)
    data = {'models': models, 'plan': plan, 'dimensions': {f: json.loads((BENCH / 'coupons' / (f + '_dimensions.json')).read_text()) for f in ['LP6', 'M4']}, 'sources_sha256': sources, 'view_only': True, 'physical_data_available': False}
    (ASSETS / 'cad-data.js').write_text('window.BENCH_ASSETS = ' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n', encoding='utf-8')
    (ASSETS / 'provenance.json').write_text(json.dumps(data | {'models': {k: {'source_sha256': v['source_sha256'], 'triangles': len(v['faces'])} for k, v in models.items()}}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    with zipfile.ZipFile(ASSETS / 'bench-handoff.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(BENCH.rglob('*')):
            if p.is_file(): z.write(p, 'O7-original/' + str(p.relative_to(BENCH)))
        z.write(ROOT / 'HANDOFF.zh-CN.md', 'START-HERE.zh-CN.md')
    print(json.dumps({'models': len(models), 'triangles': sum(len(v['faces']) for v in models.values()), 'sources': len(sources), 'view_only': True}))
if __name__ == '__main__': main()
