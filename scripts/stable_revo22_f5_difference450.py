from pathlib import Path
p=Path(__file__).parent/'verify_revo22_f5_contacts298.py';s=p.read_text(encoding='utf-8-sig');a=s.index(' n=np.load(fp);');b=s.index('\n rois=',a)
s=s[:a]+''' print('FIT450_BEGIN',pid,flush=True)
 n=np.load(fp);d=json.loads((folder/'design'/f'{pid}.json').read_text());old=np.load(OLD/'parts'/f'{pid}.npz');Q=np.array(d['f4_to_current_matrix']);off=np.array(d['f4_to_current_translation_mm']);reference=solid(old['v']@Q.T+off,old['f']);new=solid(n['v'],n['f']);tol=max(1e-5,reference.volume()*1e-9);has_additions=bool(d.get('f5_additions'))
 raw=(reference-new).as_original();added=(new-reference).as_original()
 # Source-material clipping is only needed for mixed addition/subtraction
 # differences that contain the diagnosed coincident void shell. A proven
 # subtractive body is already a subset; a second coincident Boolean can
 # crash Manifold without changing the intended solid.
 if has_additions and abs(raw.volume())>VTOL and abs(added.volume())>VTOL:
  raw=(raw^reference).as_original();added=(added^new).as_original()
 assert added.volume()<tol or(has_additions and added.volume()<min(10.,reference.volume()*.002))
'''+s[b:];s=s.replace('boolean_differences_clipped_to_their_source_material=True,','mixed_boolean_differences_clipped_to_their_source_material=True,');p.write_text(s,encoding='utf-8')
