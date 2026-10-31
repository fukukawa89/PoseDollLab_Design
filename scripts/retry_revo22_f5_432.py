from pathlib import Path
p=Path(__file__).parent/'inspect_revo22_f5_contact431.py';s=p.read_text(encoding='utf-8-sig');s=s.replace('for c in material_components(env):','for c in env.decompose():');p.write_text(s,encoding='utf-8')
