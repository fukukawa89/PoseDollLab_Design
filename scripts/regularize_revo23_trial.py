"""Trial only: regularize coincident mesh seams; never modify the delivery."""
from build_revo23 import *
import pymeshfix

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--part',default='frame/upperarm_l');args=ap.parse_args()
    d=read(B/'assembly.json');item=next(r for r in d['items']if r['key']==args.part);n=np.load(B/'assembly.npz')
    i=str(item['index']);original=solid(n[i+'v'],n[i+'f']);s=original.as_original().simplify(.001)
    v,f=vf(s);m=trimesh.Trimesh(v.astype('f4').astype(float),f,process=True)
    print('START',args.part,len(m.faces),m.is_watertight,flush=True)
    m.update_faces(m.nondegenerate_faces());m.update_faces(m.unique_faces());m.remove_unreferenced_vertices()
    v,f=pymeshfix.clean_from_arrays(np.asarray(m.vertices),np.asarray(m.faces,np.int32),verbose=False,
                                  joincomp=False,remove_smallest_components=False)
    out=trimesh.Trimesh(v,f,process=True);print('REPAIRED',len(f),out.is_watertight,out.is_winding_consistent,flush=True)
    stem=args.part.replace('/','_');path=B/'verification'/f'regularized_trial_{stem}.stl';out.export(path)
    again=trimesh.load(path,process=True)
    report=dict(key=args.part,source_geometry_sha256=sha(B/'assembly.npz'),triangles=len(f),
        exported_watertight=again.is_watertight,exported_winding=again.is_winding_consistent,
        original_volume_mm3=original.volume(),repaired_volume_mm3=out.volume,applied=False)
    try:
        fixed=solid(v,f)
        report.update(removed_mm3=(original-fixed).volume(),added_mm3=(fixed-original).volume(),
                      components=len(fixed.decompose()))
        keep=np.load(B/'retained_interfaces.npz');ks=solid(keep[args.part+'|v'],keep[args.part+'|f'])
        report['retained_interface_removed_mm3']=(ks-fixed).volume()
    except Exception as ex:report['solid_error']=str(ex)
    put(path.with_suffix('.json'),report);print(json.dumps(report),flush=True)

if __name__=='__main__':main()
