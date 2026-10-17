import json,shutil
import o22f6_holeclear as h
BASE=h.WORK;SOURCE=BASE/'bypass_batch'
def main():
 p=next(p for p in json.loads((h.SRC/'manifest.json').read_text())['plates']if p['id']=='D01')
 for label,angle in [('none_wide075','0'),('none_wide080','0')]:
  h.OUT=BASE/'profile_batch'/label;h.WORK=BASE/'profile_runs'/label;h.WORK.mkdir(parents=True,exist_ok=True)
  for sub in ['parts','design']:shutil.copytree(SOURCE/sub,h.OUT/sub,dirs_exist_ok=True)
  overrides=json.loads((BASE/'profile_overrides.json').read_text());overrides['P095']={'bridge_angle':angle,'is_infill_first':'1','outer_wall_line_width':'0.75'if label.endswith('075')else'0.8','inner_wall_line_width':'0.75'if label.endswith('075')else'0.8'};h.put(h.WORK/'profile_overrides.json',overrides);h.TARGET_PART_IDS=['P095'];h.build_plate(p);h.screen_plate(p)
if __name__=='__main__':main()