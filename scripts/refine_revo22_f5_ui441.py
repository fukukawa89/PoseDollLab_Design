from pathlib import Path
p=Path(__file__).parent/'polish_revo22_f5_delivery439.py';s=p.read_text(encoding='utf-8-sig');s=s.replace('html=html.replace("esc(it.part)+\'</small>\'","esc(it.part)+(it.optional_sample?\' · 可选小样\':\'\')+\'</small>\'")','html=html.replace("esc(it.part)","(esc(it.part)+(it.optional_sample?\' · 可选小样\':\'\')))")')
s=s.replace("html=html.replace('本体半透明','本体半透明');write", "html=html.replace('</style>','#removal-info,#stem-info{max-height:6.5em;overflow:auto;margin:8px 0;line-height:1.7}</style>');write")
s=s.replace("js=(D/'viewer.js').read_text();js=", "js=(D/'viewer.js').read_text().replace('[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,1]','[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]');js=")
p.write_text(s,encoding='utf-8')
