"""Compare the real browser's pose transforms to the Python model."""
from spherical_wrist import *
def main():
    raw=(OUT/'verification/browser_cli_result.txt').read_bytes()
    txt=raw.decode('utf-16' if raw[:2] in [b'\xff\xfe',b'\xfe\xff'] else 'utf-8-sig')
    report=json.loads(txt.split('### Result',1)[1].split('### Ran Playwright code',1)[0].strip())
    assert report['status']=='PASS' and not report['errors']
    put(OUT/'verification/browser_review.json',report)
    p=load(OUT/'profiles/arm_profile.json');worst=0.;count=0
    for case in report['samples']:
        f=frames(p,case['angles'])
        if case['mode']=='wrist':
            inv=np.linalg.inv(f['wrist_base']);f={key:inv@val for key,val in f.items()}
        for key,val in case['frames'].items():
            worst=max(worst,float(np.max(abs(np.array(val).reshape(4,4)-f[key]))));count+=1
    assert worst<1e-8 and report['geometry_sha256']==sha(OUT/'assembly_meshes.npz')
    result=dict(status='PASS',pose_samples=len(report['samples']),frames_compared=count,max_matrix_element_error=worst,
        geometry_sha256=report['geometry_sha256'],browser_report_sha256=sha(OUT/'verification/browser_review.json'),
        source_sha256={name:sha(HERE/name) for name in ['index.html','style.css','viewer.js','browser_review.js']})
    put(OUT/'verification/browser_fk_agreement.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'},ensure_ascii=False))
if __name__=='__main__':main()
