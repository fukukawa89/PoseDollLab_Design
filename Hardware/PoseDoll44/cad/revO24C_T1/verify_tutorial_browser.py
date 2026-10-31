"""Independent transform and UI audit for the delivered tutorial."""
from kit import *
from tutorial import pose_matrix
import shutil

def main():
    data=json.loads((OUT/'tutorial/steps.json').read_text('utf8'))
    audit=json.loads((ROOT/'output/playwright/o24ct1-tutorial-browser.json').read_text('utf-8-sig'))
    assert audit['passed'] and not audit['errors']
    assert audit['geometrySha']==sha(OUT/'assembly_meshes.npz') and audit['revision']==REVISION
    assert len(audit['rows'])==sum(len(l['steps']) for l in data['lessons'].values())==188
    assert all(r['webglError']==0 and r['miniError']==0 for r in audit['rows'])
    assert all(r['status']==200 for r in audit['checked'])
    assert audit['mobile']['width']==audit['mobile']['scrollWidth']
    assert audit['offline']['ready'] and audit['offline']['webglError']==0 and audit['offline']['station']=='W'
    assert not audit['initial']['playing'] and not audit['checkpoint']['playing'] and audit['checkpoint']['kind']=='check'
    oriented={id for id,p in data['catalog'].items() if 'orientation' in p}
    assert {r['id'] for r in audit['hardware']}==oriented and len(audit['hardware'])==73
    maxerror=0
    for sample in audit['matrixSamples']:
        step=data['lessons'][sample['station']]['steps'][sample['index']];t=sample['t'];smooth=t*t*(3-2*t)
        for id,actual in sample['currentMatrices'].items():
            if id in step.get('posePaths',{}):
                p0,p1=step['posePaths'][id][0],step['posePaths'][id][-1]
                pose={key:((1-smooth)*np.array(p0[key])+smooth*np.array(p1[key])).tolist() for key in p0}
                expected=pose_matrix(pose)
            elif step['kind']=='rom':
                frame=data['catalog'][id]['frame'];expected=frames(sample['station'],*sample['angles'])[frame]
            elif id in step['paths']:
                path=np.array(step['paths'][id]);distance=np.linalg.norm(np.diff(path,axis=0),axis=1);travel=sum(distance)*smooth
                for i,segment in enumerate(distance):
                    if travel<=segment or i==len(distance)-1:
                        expected=a.T(path[i]+(path[i+1]-path[i])*(travel/segment if segment else 1));break
                    travel-=segment
            else:expected=np.array(step['beforeM'][id])
            error=float(np.max(np.abs(np.array(actual).reshape(4,4)-expected)));maxerror=max(maxerror,error);assert error<1e-7,(sample['station'],sample['index'],id,error)
            face=sample.get('orientation')
            if face and face['shown'] and face['id']==id:
                o=data['catalog'][id]['orientation']
                expected_face=(expected@np.r_[o['face'],1])[:3]
                expected_normal=expected[:3,:3]@o['normal']
                assert np.allclose(face['face'],expected_face,atol=1e-7),(id,'face')
                assert np.allclose(face['normal'],expected_normal,atol=1e-7),(id,'normal')
    assets={name:sha(OUT/'tutorial'/name) for name in ['index.html','tutorial.js','orientation.js','style.css','steps.js']}
    put(OUT/'verification/tutorial_browser.json',dict(passed=True,geometry_sha256=audit['geometrySha'],revision=REVISION,steps_sha256=sha(OUT/'tutorial/steps.json'),ui_source_sha256=sha(OUT/'tutorial/tutorial.js'),ui_assets_sha256=assets,all_steps_exercised=len(audit['rows']),oriented_hardware_exercised=len(audit['hardware']),max_transform_error=maxerror,tests=['part labels and counts','73 nut/washer instructions','actual nylon/smooth face pixels','reverse-face inspection','face markers follow tilted paths','step navigation','scrubbing','play/replay/pause','auto-play stops at check','transparent face focus','mobile width','offline WebGL','local links'],audit=audit))
    for name in ['tutorial-H-preload.png','tutorial-W-liner.png','tutorial-mobile.png']+[r[2] for r in audit['faceScreens']]:shutil.copyfile(ROOT/'output/playwright'/name,OUT/'images'/name)
    print('TUTORIAL BROWSER PASS',len(audit['rows']),'matrix error',maxerror,flush=True)

if __name__=='__main__':main()
