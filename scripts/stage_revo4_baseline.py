"""Read-only inheritance of O3; no relabelled old checks."""
from revo4_evidence import *
from revo3_evidence import verify_artifacts as verify_old
def main():
    v,o=run_paths();old=HW/'verification/revO3/runs/o3_20260924_r3';meta=read(old/'run.json');bad=[]
    for name,digest in meta['source_sha256'].items():
        if not (REPO/name).is_file() or sha(REPO/name)!=digest:bad.append(name)
    record=read(old/'joint_execution.json')['artifacts'];data=verify_old(record,'o3_20260924_r3')
    joint=read(old/'joint.json');joint['origin_run_id']=joint.pop('run_id');joint['origin_artifact_set']=record;save(v/'joint.json',joint)
    manifest=read(HW/'docs/revO4_review_source/DELIVERY_MANIFEST.json')
    # Original delivery schema is separately recorded and byte-hashed in inputs.json.
    report={'source_commit':meta['base_commit'],'reviewed_commit':git_head(),'O3_source_files_checked':len(meta['source_sha256']),'changed_old_sources':bad,'joint_inherited':record,'status':'PASS' if not bad else 'FAIL_LEGACY_CHANGED','scope':'O3 inputs and sealed joint outputs; no new manufacturing pass'}
    save(v/'baseline.json',report);print(report['status'],len(bad));return bool(bad)
if __name__=='__main__':raise SystemExit(main())
