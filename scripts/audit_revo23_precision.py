"""Read-only STL robustness diagnostics, outputs under verification only."""
from build_revo23 import *

def audit(label,v,f):
    m=trimesh.Trimesh(v,f,process=True)
    print(label,'v/f',len(m.vertices),len(m.faces),'closed',m.is_watertight,'winding',m.is_winding_consistent,
          'degenerate',int((~m.nondegenerate_faces()).sum()),flush=True)
    m.update_faces(m.nondegenerate_faces());m.update_faces(m.unique_faces());m.remove_unreferenced_vertices()
    print('CLEAN','v/f',len(m.vertices),len(m.faces),'closed',m.is_watertight,'winding',m.is_winding_consistent,flush=True)
    mesh=md.Mesh64(np.asarray(m.vertices),np.asarray(m.faces,np.uint64));mesh.merge();s=md.Manifold(mesh)
    print('REIMPORT',s.status(),flush=True)
    return s

def main():
    q=np.load(H/'bench/revO22/O22F7_PLA_AssemblyRevision/parts/X046.npz')
    audit('original X046 double',q['v'],q['f']);audit('original X046 single',q['v'].astype('f4').astype(float),q['f'])
    doc=read(B/'assembly.json');item=next(i for i in doc['items']if i['key']=='frame/chest');n=np.load(B/'assembly.npz')
    v,f=n[str(item['index'])+'v'],n[str(item['index'])+'f']
    s=audit('O23 chest double',v,f);audit('O23 chest single',v.astype('f4').astype(float),f)
    s=solid(v,f)
    for tolerance in (.0001,.001,.01,.03):
        simp=s.simplify(tolerance);sv,sf=vf(simp)
        fixed=audit('simplify '+str(tolerance),sv.astype('f4').astype(float),sf)
        if str(fixed.status())=='Error.NoError':
            out=B/'verification'/f'chest_cleaned_{tolerance}.stl';stl(out,fixed)
            again=trimesh.load(out,process=True);print('FINAL',out.name,again.is_watertight,again.is_winding_consistent,flush=True)

if __name__=='__main__':main()
