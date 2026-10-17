import json,concurrent.futures
import o22f6_holeclear as h
from o22f6_route import collect
SCOPES=None
def one(item):
 p,scope=item;h.TARGET_PART_IDS=scope;return h.screen_plate(p)
def main():
 reports,_=collect();changed=set(reports)|{'X058','X066','X038','P095','P073','X046','W007','X062','P051','P117','P071','P093','P035','P130','W017'}
 m=json.loads((h.SRC/'manifest.json').read_text());jobs=[(p,sorted({it['id']for it in p['items']} & changed))for p in m['plates']];jobs=[j for j in jobs if j[1]];h.put(h.WORK/'final_path_scopes.json',{p['id']:scope for p,scope in jobs});print('FINAL_SCOPES',[(p['id'],s)for p,s in jobs],flush=True)
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as pool:
  for result in pool.map(one,jobs):pass
if __name__=='__main__':main()