"""Prove coverage for unchanged items using the previous whole-plate checks and exact per-item extrusion sequence."""
import json,sys,hashlib,numpy as np,concurrent.futures
import o22f6_holeclear as h
from o22_f3_gcode import extract_detailed

def motion(p):
 pid=p['id'];oldrep=json.loads((h.WORK/f'history/scoped_none/plates/{pid}/support_paths.json').read_text());old=h.WORK/f"candidates/PLATE_{pid}/{oldrep['candidate_label']}/projects/{pid}_O22F6_PLA_holeclear.3mf";new=h.OUT/f'projects/{pid}_O22F6_PLA_holeclear.3mf';current=json.loads((h.WORK/f'plates/{pid}/support_paths.json').read_text());scope=current.get('scope_part_ids')
 oldr,ar,af,an=extract_detailed(old,arc_tolerance_mm=.025,max_arc_segment_mm=1.);newr,br,bf,bn=extract_detailed(new,arc_tolerance_mm=.025,max_arc_segment_mm=1.);a=np.asarray(ar).reshape(-1,9);b=np.asarray(br).reshape(-1,9);af=np.asarray(af);bf=np.asarray(bf);rows=[]
 for it in p['items']:
  bb=np.array(it['bounds_mm']);av=(a[:,7]==0)&(a[:,0]>=bb[0]-.5)&(a[:,0]<=bb[3]+.5)&(a[:,1]>=bb[1]-.5)&(a[:,1]<=bb[4]+.5);bv=(b[:,7]==0)&(b[:,0]>=bb[0]-.5)&(b[:,0]<=bb[3]+.5)&(b[:,1]>=bb[1]-.5)&(b[:,1]<=bb[4]+.5);aa=a[av];ba=b[bv];match=aa.shape==ba.shape and np.allclose(aa,ba,atol=1e-5,rtol=0);fmatch=np.array_equal(np.array(an)[af[av]],np.array(bn)[bf[bv]]);is_scoped=scope is None or it['id']in scope
  rows.append(dict(id=it['id'],name=it['object_name'],current_native_audited=is_scoped,old_segments=len(aa),new_segments=len(ba),extrusion_sequence_identical=bool(match and fmatch),prior_project_sha256=h.sha(old),project_sha256=h.sha(new),coverage_verified=is_scoped or bool(match and fmatch)))
 r=dict(plate=pid,all_covered=all(x['coverage_verified']for x in rows),rows=rows);h.put(h.WORK/f'plates/{pid}/coverage.json',r);print('COVERAGE',pid,r['all_covered'],[(x['id'],x['old_segments'],x['new_segments'])for x in rows if not x['coverage_verified']],flush=True);return r
if __name__=='__main__':
 m=json.loads((h.SRC/'manifest.json').read_text())
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as pool:
  for r in pool.map(motion,m['plates']):pass