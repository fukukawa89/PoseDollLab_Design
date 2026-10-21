"""Validate revised external fin bypasses in a separate complete batch snapshot."""
import json,shutil,concurrent.futures
from pathlib import Path
import o22f6_holeclear as h
BASE=h.WORK;STAGE=BASE/'bypass_batch';RUN=BASE/'external_run2'
def one(p):
 h.OUT=STAGE;h.WORK=RUN;h.TARGET_PART_IDS={'D01':['P095','X058'],'D02':['P073'],'D03':['X038'],'D06':['X066']}[p['id']];h.build_plate(p);return h.screen_plate(p)
def main():
 for sub in ['parts','design']:shutil.copytree(h.OUT/sub,STAGE/sub,dirs_exist_ok=True)
 for sub in ['parts','design']:
  for p in (BASE/'bypass'/sub).glob('*'):shutil.copy2(p,STAGE/sub/p.name)
 for pid in ['P095','P073']:
  r=json.loads((BASE/f'routes/{pid}.json').read_text());folder=BASE/f"candidates/{pid}/{r['label']}"
  shutil.copy2(folder/f'parts/{pid}.npz',STAGE/f'parts/{pid}.npz');shutil.copy2(folder/f'design/{pid}.json',STAGE/f'design/{pid}.json')
 RUN.mkdir(parents=True,exist_ok=True);shutil.copy2(BASE/'profile_overrides.json',RUN/'profile_overrides.json')
 plates=[p for p in json.loads((h.SRC/'manifest.json').read_text())['plates']if p['id']in ['D01','D02','D03','D06']]
 with concurrent.futures.ProcessPoolExecutor(max_workers=1)as pool:
  for r in pool.map(one,plates):pass
if __name__=='__main__':main()