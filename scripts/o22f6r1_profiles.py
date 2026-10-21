"""Check two local wall-order settings against P095's native paths, in isolation."""
import json,shutil,sys,concurrent.futures
import o22f6r1_p095 as r

def run(spec):
 label,overrides=spec;w=r.WORK/'profile_trials'/label;o=w/'package';w.mkdir(parents=True,exist_ok=True)
 for sub in ['parts','design']:shutil.copytree(r.OUT/sub,o/sub,dirs_exist_ok=True)
 options=json.loads((r.OLDWORK/'profile_overrides.json').read_text());options['P095']=overrides;r.h.put(w/'profile_overrides.json',options)
 r.configure();h=r.h;h.OUT=o;h.WORK=w;h.SCREEN_LABEL=label;h.TARGET_PART_IDS=['P095'];h.PRINT_SETTINGS_ID='O22-F6 R1 P095 elbows / A1 mini PLA 0.4'
 h.build_plate(r.plate());q=h.screen_plate(r.plate());rep=dict(label=label,overrides=overrides,islands=q['external_island_count'],critical=q['critical_external_count'],passed=q['native_review_resolved'],project_sha256=q['project_sha256']);r.h.put(w/'result.json',rep);print('PROFILE_RESULT',rep,flush=True);return rep
if __name__=='__main__':
 jobs=[('outerfirst',{'wall_sequence':'outer wall/inner wall'}),('outerfirst_infilllast',{'wall_sequence':'outer wall/inner wall','is_infill_first':'0'})]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as pool:results=list(pool.map(run,jobs))
 r.h.put(r.WORK/'profile_trials/summary.json',results)