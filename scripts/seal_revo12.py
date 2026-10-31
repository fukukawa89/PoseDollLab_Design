"""Seal O12 coupon evidence; physical fit, spring force and strength stay unknown."""
from pathlib import Path
import sys, json, hashlib, subprocess
R=Path(__file__).resolve().parents[1]; H=R/'Hardware/PoseDoll44'
G=H/'generated/revO12/runs/o12_20260926_r1'; B=H/'bench/revO12'; PAGE=H/'tutorials/taobao-bench'
DEST=G/'evidence_manifest.json'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'),parse_constant=lambda s:(_ for _ in ()).throw(ValueError(s)))
def upstream():
    r=subprocess.run([sys.executable,'-X','utf8',str(R/'scripts/seal_revo11.py'),'--verify'],cwd=R,capture_output=True,text=True,encoding='utf-8')
    assert r.returncode==0,r.stdout+r.stderr
    return json.loads(r.stdout)
def main():
    old=upstream()
    if '--verify' in sys.argv:
        m=read(DEST)
        bad=[n for n,d in m['repository_files_sha256'].items() if not (R/n).exists() or sha(R/n)!=d]
        print(json.dumps({'verified':not bad,'files':len(m['repository_files_sha256']),'errors':bad,'upstream_O11_verified':old['verified'],'physical_tested':False}))
        raise SystemExit(bool(bad))
    assert not DEST.exists(),'Use a new revision after sealing.'
    plan=read(B/'plan.json'); c=read(G/'digital_checks.json'); procurement=read(B/'procurement.json')
    ui=read(G/'page_checks.json')
    for report in (plan,c,ui):
        for n,d in report['inputs_sha256'].items(): assert sha(R/n)==d,('changed dependency',n)
    assert plan['physical_tested'] is False and plan['manufacturing_released'] is False
    assert plan['stock_parts_fit_confirmed'] is False and plan['spring_force_N'] is None and not plan['reuse_O11_210N_force_reference']
    assert len(plan['parts'])==15 and not plan['nominal_findings']
    assert all(p['solid_components']==1 and p['volume_mm3']>0 for p in plan['parts'].values())
    assert plan['shoulder_thread_length_mm']==6 and plan['shoulder_socket_AF_mm']==3 and plan['printed_load_web_mm']==2.8
    assert len(c['stack_cases'])==4 and c['pair_checks_per_stack']==105 and len(c['sampled_lever_motion'])==292
    assert not any(r['findings'] for r in c['stack_cases']+c['sampled_lever_motion'])
    assert all(abs(r['nominal_thread_overlap_mm']-2.4)<1e-5 for r in c['stack_cases'])
    assert c['half_closure_max_overlap_mm3']<1e-4 and max(r['max_overlap_mm3'] for r in c['insertions'])<1e-4
    assert not c['straight_AF3_tool_shank_findings']
    assert all(r['nut_into_washer_mm3']>.01 and r['washer_into_base_mm3']>.01 for r in c['axial_retention_obstructions'])
    assert len(c['thread_sensitivity'])==128 and c['washer_actual_slip_fit'] is None and c['spring_measured_force_N'] is None
    assert len([r for r in c['washer_fit_counterexamples'] if r['status']=='ZERO_ALLOWANCE_NOT_SLIP_FIT'])==2
    assert all(v is None for k,v in read(B/'measurement_template.json').items() if k!='schema')
    assert sum(r['quantity'] for r in procurement['items'])==12
    assert len(procurement['source_images'])==7
    for item in procurement['source_images']: assert sha(B/item['file'])==item['sha256']
    assert ui['status']=='PASS' and not ui['errors'] and ui['download_matches_print_package']
    assert ui['partOptions']==16 and ui['nonBackgroundPixels']>100 and ui['mobile']['scrollWidth']<=ui['mobile']['width']
    files={Path(__file__),H/'docs/O12_TAOBAO_ADAPTATION.zh-CN.md',H/'generated/revO11/runs/o11_20260926_r1/evidence_manifest.json'}
    for root in (H/'cad/revO12',B,G,PAGE):
        files.update(p for p in root.rglob('*') if p.is_file() and p!=DEST and '__pycache__' not in p.parts)
    manifest={'schema':'o12-taobao-coupon-evidence-v1','status':'NOMINAL_COUPON_CHECKED_AWAITING_PHYSICAL_FIT_AND_LOAD_TESTS',
              'upstream':old,'repository_files_sha256':{p.relative_to(R).as_posix():sha(p) for p in sorted(files)},
              'physical_tested':False,'slicer_tested':False,'spring_force_verified':False,'washer_fit_verified':False,
              'strength_verified':False,'full_joint_recertified':False,'full_body_recertified':False,'manufacturing_released':False}
    DEST.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'files':len(files),'status':manifest['status'],'upstream_O11_verified':old['verified']}))
if __name__=='__main__':main()
