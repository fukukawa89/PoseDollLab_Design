"""Check every tutorial insertion/move against already installed components."""
from kit import *
from tutorial import pose_matrix
import time

def overlap(a,b):
    return np.all(a[1]>b[0]+1e-7) and np.all(b[1]>a[0]+1e-7)

def main():
    start=time.time();data=json.loads((OUT/'tutorial/steps.json').read_text('utf8'))
    if '--stock-washers' in sys.argv:
        from hardware_alternatives import alternative_build
        k,_=alternative_build()
    else:k=build()
    parts={p['id']:p['s'] for p in k.parts};bounds={id:np.array(s.bounding_box()).reshape(2,3) for id,s in parts.items()}
    reports=[];fail=[];samples=0
    for station,lesson in data['lessons'].items():
        for step in lesson['steps']:
            poses=step.get('posePaths',{});moving=set(step['paths'])|set(poses)
            if not moving:continue
            fixed={id:moved(parts[id],np.array(step.get('beforeM',{}).get(id,a.T(off)))) for id,off in step['before'].items() if id not in moving}
            bb={id:np.array(s.bounding_box()).reshape(2,3) for id,s in fixed.items()};worst={};n=0
            for id,path in step['paths'].items():
                for offset0,offset1 in zip(path,path[1:]):
                    distance=np.linalg.norm(np.array(offset1)-offset0)
                    for t in np.linspace(0,1,max(5,math.ceil(distance/.75)+1)):
                        off=np.array(offset0)*(1-t)+np.array(offset1)*t;s=None;box1=bounds[id]+off;n+=1
                        for other,target in fixed.items():
                            if not overlap(box1,bb[other]):continue
                            if s is None:s=parts[id].translate(off)
                            volume=float((s^target).volume())
                            if volume>.02:worst[id+' / '+other]=max(worst.get(id+' / '+other,0),volume)
            for id,path in poses.items():
                for a0,b0 in zip(path,path[1:]):
                    count=max(5,math.ceil(abs(b0['angle']-a0['angle'])/.5)+1,math.ceil(np.linalg.norm(np.array(b0['before'])-a0['before'])/.5)+1,math.ceil(np.linalg.norm(np.array(b0['after'])-a0['after'])/.5)+1)
                    for t in np.linspace(0,1,count):
                        p={key:((1-t)*np.array(a0[key])+t*np.array(b0[key])).tolist() for key in a0}
                        s=moved(parts[id],pose_matrix(p));box1=np.array(s.bounding_box()).reshape(2,3);n+=1
                        for other,target in fixed.items():
                            if overlap(box1,bb[other]):
                                volume=float((s^target).volume())
                                if volume>.02:worst[id+' / '+other]=max(worst.get(id+' / '+other,0),volume)
            row=dict(station=station,step=step['n'],title=step['title'],samples=n,passed=not worst,collisions=worst)
            reports.append(row);samples+=n
            if worst:fail.append(row);print('PATH FAIL',station,step['n'],worst,flush=True)
        print('PATH STATION',station,'done',flush=True)
    result=dict(passed=not fail,geometry_sha256=sha(OUT/'assembly_meshes.npz'),steps_sha256=sha(OUT/'tutorial/steps.json'),source_sha256=sha(Path(__file__)),samples=samples,threshold_mm3=.02,rows=reports,failures=fail,elapsed_s=time.time()-start,scope='Rigid translated motion against all previously installed non-moving components, max sample spacing 0.75 mm. Excludes screw helices, tool access, elasticity, force, manufacturing tolerance and physical verification; no collision pairs suppressed.')
    result['hardware_configuration']='all M2 washers 0.5 mm; R M6 washers 1.5 mm' if '--stock-washers' in sys.argv else 'nominal exported geometry'
    put(OUT/'verification'/('tutorial_paths_stock.json' if '--stock-washers' in sys.argv else 'tutorial_paths.json'),result)
    print('TUTORIAL PATHS',not fail,samples,round(time.time()-start,1),flush=True)
    if fail:raise SystemExit(1)

if __name__=='__main__':main()
