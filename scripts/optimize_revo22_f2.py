import sys,json,shutil,time,traceback,math
import numpy as np
import build_revo22_fins_v2 as f2
from check_revo22_f2_layers import check
from repair_revo22_f2_contacts import repair
B=f2.B;O=f2.O;u={i['id']:i for p in json.loads((B/'a1mini/manifest.json').read_text())['plates'] if not p['optional'] for i in p['items']};vols={i['part']:i['volumes'] for i in json.loads((f2.D/'all_protected_volumes.json').read_text())['objects']}
def paths(pid):return [O/'parts'/f'{pid}.npz',O/'design'/f'{pid}.json',O/'verification'/f'{pid}_layers.json']
def evaluate(pid,label):
 d=json.loads(paths(pid)[2].read_text());r=json.loads(paths(pid)[1].read_text());fl=d['combined_floating_islands'];over=d['long_overhang_layers'];area=sum(x['area_mm2'] for x in fl);maxarea=max([x['unbacked_beyond_2mm_area'] for x in over],default=0);h=max([x['height_mm'] for x in r['segments']],default=0)
 score=area*50+maxarea*3+len(fl)*3+h*.5+r['support_volume_mm3']/2000
 info={'label':label,'score':score,'floating_count':len(fl),'floating_area_mm2':area,'max_unbacked_area_mm2':maxarea,'max_fin_height_mm':h,'part_height_mm':r['new_height_mm'],'volume':r['support_volume_mm3'],'gravity':r['orientation']['gravity_in_source']}
 dest=O/'optimization'/pid/label;dest.mkdir(parents=True,exist_ok=True)
 for p in paths(pid):shutil.copy2(p,dest/p.name)
 print(pid,json.dumps(info),flush=True);return info
for pid in sys.argv[1:]:
 try:
  original=evaluate(pid,'baseline');records=[original];rank=json.loads((O/'orientation'/f'{pid}.json').read_text())['ranked_candidates'];selected=[];seen={tuple(np.round(original['gravity'],5))};heightlimit=max(original['part_height_mm']*1.5,40)
  for c in rank[:14]+[x for x in rank if max(abs(np.array(x['gravity_in_source'])))>.999999]:
   key=tuple(np.round(c['gravity_in_source'],5))
   if key in seen or c['size_mm'][2]>heightlimit:continue
   seen.add(key);selected.append(c)
   if len(selected)>=8:break
  for j,ori in enumerate(selected):
   f2.choose=lambda _:ori
   f2.make(pid,u[pid],vols.get(u[pid]['part'],[]));check(pid);repair(pid);val=evaluate(pid,f'try_{j:02}');records.append(val)
   if val['floating_count']==0 and val['max_unbacked_area_mm2']<8:break
  best=min(records,key=lambda x:x['score']);source=O/'optimization'/pid/best['label']
  for p in paths(pid):shutil.copy2(source/p.name,p)
  (O/'optimization'/pid/'comparison.json').write_text(json.dumps({'best':best,'candidates':records},indent=2),encoding='utf-8');print('CHOSEN',pid,best['label'],round(best['score'],2),flush=True)
 except Exception:print('ERROR',pid,traceback.format_exc(),flush=True)