"""Test the recovered original central mechanism. Never qualifies missing outer parts."""
from pathlib import Path
import json,itertools,hashlib,argparse
import numpy as np
from reference_assembly import OUT,restored_core,at_pose
from mesh_collision import compare

def main():
    local,transforms,fits=restored_core();names=list(local);rows=[]
    angles=[(0,0)]+[(a,0) for a in range(-100,101,5) if a]+[(0,b) for b in range(-100,101,5) if b]+list(itertools.product((-75,-45,45,75),repeat=2))
    ap=argparse.ArgumentParser();ap.add_argument('--limit',type=int,default=0);args=ap.parse_args();angles=angles[:args.limit] if args.limit else angles
    for alpha,beta in angles:
        meshes=at_pose(local,alpha,beta);pairs=[]
        for x,y in itertools.combinations(names,2):
            if x in ('C14','C15') and y in ('C14','C15'):continue
            a,b=meshes[x],meshes[y]
            if np.any(np.minimum(a.max((0,1)),b.max((0,1)))-np.maximum(a.min((0,1)),b.min((0,1)))<0):continue
            res=compare(a,b);pairs.append({'a':x,'b':y,**res})
        fail=any(p['status']=='PENETRATION' for p in pairs);review=any(p['status']=='CONTACT_REQUIRES_REVIEW' for p in pairs)
        rows.append({'alpha_deg':alpha,'beta_deg':beta,'status':'FAIL' if fail else 'REVIEW' if review else 'PASS_CORE_MESH_ONLY','pairs':pairs})
        print(alpha,beta,rows[-1]['status'],[(r['a'],r['b'],r['status']) for r in pairs if r['status']!='CLEAR_NOMINAL_MESH'],flush=True)
        (OUT/'core_motion.json').write_text(json.dumps({'status':'RUNNING','cases':rows,'scope':'Original two yokes + split ring only. No outer connector, fastener, sensor, harness, preload or tolerance qualification.','physical_tested':False},indent=2)+'\n',encoding='utf-8')
    result={'status':'SCOPED_REFERENCE_AUDIT_COMPLETE','cases':rows,'pass_cases':sum(r['status']=='PASS_CORE_MESH_ONLY' for r in rows),'fail_cases':sum(r['status']=='FAIL' for r in rows),'review_cases':sum(r['status']=='REVIEW' for r in rows),'source_sha256':{n:hashlib.sha256((OUT/n).read_bytes()).hexdigest() for n in ('component_meshes.npz','assembly_recovery.json')},'scope':'Original central four plastic pieces only; isolated discrete angles; no manufacturing release','physical_tested':False,'manufacturing_released':False}
    (OUT/'core_motion.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()

