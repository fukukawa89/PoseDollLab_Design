from pathlib import Path
p=Path(__file__).parent/'publish_revo22_f5_compact302.py';s=p.read_text(encoding='utf-8-sig')
needle="  proof=json.loads((S/'plate_results'/f\"{p['id']}.json\").read_text());src="
replace="  proof=json.loads((S/'plate_results'/f\"{p['id']}.json\").read_text());key=hashlib.sha256(json.dumps(dict(plate=p,geometry={i['id']:sha(S/'parts'/f\"{i['id']}.npz\")for i in p['items']}),sort_keys=True).encode()).hexdigest();assert key==proof['layout_and_source_hash'],(p['id'],'Stale plate proof');src="
assert needle in s;s=s.replace(needle,replace);p.write_text(s,encoding='utf-8')
