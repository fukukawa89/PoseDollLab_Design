"""Check Boolean tolerance on a freshly rebuilt chest, without changing delivery."""
import build_revo23 as b
from build_revo23 import *

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--tolerance',type=float,default=.005);args=ap.parse_args()
    def conditioned(v,f):
        m=md.Mesh64(np.asarray(v,np.float64),np.asarray(f,np.uint64),tolerance=args.tolerance)
        m.merge();s=md.Manifold(m)
        if str(s.status())!='Error.NoError':raise ValueError(s.status())
        return s.set_tolerance(args.tolerance)
    b.solid=conditioned
    baseline,_,_=load_baseline();cfg=read(CFG);p=profile(cfg['scale'])
    O=frames(kin.profile,p['neutral_raw_deg']);F=frames(p,p['neutral_raw_deg'])
    s,report,_,_=make_carrier('frame/chest',baseline['frame/chest'],O,F,p,cfg,baseline)
    v,f=vf(s);out=B/'verification'/f'chest_rebuild_tol{args.tolerance}.stl'
    stl(out,s);m=trimesh.load(out,process=True)
    result=dict(tolerance_mm=args.tolerance,source_triangles=len(f),export_triangles=len(m.faces),
                stl_watertight=m.is_watertight,stl_winding=m.is_winding_consistent,
                source_components=report['material_components'],volume_mm3=s.volume())
    put(out.with_suffix('.json'),result);print(json.dumps(result),flush=True)

if __name__=='__main__':main()
