from pathlib import Path
p=Path(__file__).parent/'polish_revo22_f5_delivery439.py';s=p.read_text(encoding='utf-8-sig').replace("(esc(it.part)+(it.optional_sample?' · 可选小样':'')))","(esc(it.part)+(it.optional_sample?' · 可选小样':''))");p.write_text(s,encoding='utf-8')
import stage_revo22_f5_compact296 as stage
stage.prepare()
