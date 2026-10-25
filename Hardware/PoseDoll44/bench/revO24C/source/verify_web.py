from compact_arm import *

raw=(OUT/'verification/browser_cli_result.txt').read_bytes();txt=raw.decode('utf-16' if raw[:2] in [b'\xff\xfe',b'\xfe\xff'] else 'utf-8-sig')
report=json.loads(txt if txt.lstrip().startswith('{') else txt.split('### Result',1)[1].split('### Ran Playwright code',1)[0].strip())
assert report['status']=='PASS' and not report['errors'] and len(report['samples'])==18
assert report['geometry_sha256']==sha(OUT/'assembly_meshes.npz')
put(OUT/'verification/browser_review.json',report)
p=load(OUT/'profiles/arm_profile.json');worst=0.;count=0
for sample in report['samples']:
    f=frames(p,sample['angles'])
    f['hand']=f['hand_ball']  # Browser hand helper denotes C's physical palm, not A's unused legacy frame.
    for token,m in sample['frames'].items():
        worst=max(worst,float(np.max(abs(np.array(m).reshape(4,4)-f[token]))));count+=1
assert worst<1e-8
put(OUT/'verification/browser_fk_agreement.json',dict(status='PASS',poses=len(report['samples']),frames_compared=count,max_matrix_element_error=worst,geometry_sha256=report['geometry_sha256'],browser_report_sha256=sha(OUT/'verification/browser_review.json'),source_sha256={n:sha(HERE/n) for n in ['index.html','viewer.js','style.css','browser_review.js']}))
print('Browser/Python agreement PASS',worst)
