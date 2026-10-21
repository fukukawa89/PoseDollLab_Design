import json,sys
sys.path.insert(0,'PoseDoll_HW44_Plan/design/scripts')
import o22f6_holeclear as h
for pid in ['P130','P095','X046','P002','W017','P035','P071']:
 d=json.loads((h.SRC/f'design/{pid}.json').read_text());print(pid,'layer',d.get('required_layer_height_mm'),'overrides',d.get('required_process_overrides'))
for p in ['D01','D04','D10','D11','D12']:
 r=json.loads((h.WORK/f'plates/{p}/support_paths.json').read_text());print(p,'islands',r['external_islands'])