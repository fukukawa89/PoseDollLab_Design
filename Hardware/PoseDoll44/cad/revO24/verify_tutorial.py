"""Compare browser tutorial motion with the original Python mechanical FK."""
from arm import *


def main():
    report=json.loads((OUT/'verification/tutorial_browser.json').read_text('utf-8-sig'))
    assert report['status']=='PASS'
    p=json.loads((OUT/'profiles/arm_profile.json').read_text('utf8'))
    baseline=json.loads((OUT/'STATUS.json').read_text('utf8'))
    digest=sha(OUT/'assembly_meshes.npz')
    assert baseline['geometry_sha256']==digest,'Tutorial must not change the CAD geometry'
    worst_position=0.;worst_rotation=0.;rows=[]
    for sample in report['kinematicSamples']:
        expected=frames(p,sample['angles']);position=rotation=0.
        for name,matrix in sample['frames'].items():
            actual=np.array(matrix).reshape(4,4)
            position=max(position,float(np.linalg.norm(actual[:3,3]-expected[name][:3,3])))
            rotation=max(rotation,float(np.max(abs(actual[:3,:3]-expected[name][:3,:3]))))
        rows.append(dict(motion=sample['motion'],time=sample['time'],max_position_error_mm=position,max_rotation_element_error=rotation))
        worst_position=max(worst_position,position);worst_rotation=max(worst_rotation,rotation)
    assert len({r['motion'] for r in rows})==9
    assert worst_position<1e-8 and worst_rotation<1e-10
    files=['index.html','viewer.js','style.css','tutorial.html','tutorial.css','tutorial-content.js','tutorial.js']
    for name in files:assert sha(HERE/name)==sha(OUT/'preview'/name),'Stale preview '+name
    result=dict(status='PASS',geometry_sha256=digest,geometry_unchanged=True,samples=len(rows),axes=9,
                max_position_error_mm=worst_position,max_rotation_element_error=worst_rotation,rows=rows,
                browser_report_sha256=sha(OUT/'verification/tutorial_browser.json'),
                source_sha256={name:sha(HERE/name) for name in files},
                scope='Browser joint transforms compared with Python arm.frames; explosion endpoints checked against exported original neutral matrices. Teaching separation paths are not manufacturing assembly paths or continuous collision certificates.')
    put(OUT/'verification/tutorial_fk_agreement.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['rows','source_sha256']},ensure_ascii=False))


if __name__=='__main__':main()
