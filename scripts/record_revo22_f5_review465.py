import json,re,csv,shutil,hashlib
from pathlib import Path
from publish_revo22_f5_compact302 import D,write
from search_revo22_f5_orientation268 import B,put
from stage_revo22_f5_compact296 import S,sha
m=json.loads((D/'manifest.json').read_text());rows=list(csv.DictReader((D/'零件与打印盘对照.csv').open(encoding='utf-8-sig')));addresses={r['address']for r in rows};text=(D/'assembly/tutorials/assembly-o22/index.html').read_text();used=set(re.findall(r'\bD\d\d-\d\d\b',text));assert used<=addresses and len(re.findall(r'class="view-step"',text))==26
oldsha=sha(B/'O22F4_合盘打印包.zip');r2sha=sha(B/'X062_SupportTrial_R2/X062_R2_A1mini_PLA.3mf');assert oldsha=='d00ab375b79792491341ca3fba33e18bb8f44dac8ed44779ae37de53f82f94c9';assert r2sha=='a0b7e134693012db2f6b9911732d1b43a5649d607ad53087f0f97ccc160399bb'
put(D/'verification/reference_preservation.json',dict(original_f4_archive_unchanged_sha256=oldsha,physical_X062_R2_3mf_unchanged_sha256=r2sha,physical_X062_R2_body_fin_teeth_npz_sha256=sha(D/'parts/X062.npz')))
put(D/'verification/browser_review.json',dict(actual_browser='Chromium via Playwright',color_meshes_visually_inspected=['X046','P130','X062'],roles=['blue permanent part','orange fin','yellow connector'],fin_and_cavity_stem_selectors_checked=True,bed_plane_reference_shown=True,layout_D12_optional_samples_labelled=True,assembly_steps=26,assembly_cad_S01_loaded=True,assembly_new_addresses_valid=True,console_errors=0,physical_print_scope='Only X062 R2 has user print feedback'))
shutil.copy2(S/'final_inventory459.json',D/'verification/final_inventory.json')
qa=D/'verification/visual_review';qa.mkdir(exist_ok=True)
for fn in ['f5-x046-canvas.png','f5-p130-canvas.png','f5-x062-canvas.png','f5-d12-layout.png','f5-assembly-cad.png']:shutil.copy2(Path(__file__).parents[3]/'output/playwright'/fn,qa/fn)
print('DELIVERY465_REVIEW',len(used),'valid assembly addresses',flush=True)
