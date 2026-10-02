"""Localized extrusion of a planar section; preserves original interfaces on either side.
Not a uniform STL scale. This is a research adaptation of the provided TUT mesh.
"""
import numpy as np,struct,json,hashlib
from pathlib import Path
from reference_assembly import OUT,restored_core

def extend_section(t,direction,length,section=6.):
    if not length:return t.copy(),0.
    normal=np.array([0.,0.,direction]);shift=normal*length;output=[];area=0.
    def clip(poly,keep):
        result=[]
        for a,b in zip(poly,np.roll(poly,-1,axis=0)):
            da=a@normal-section;db=b@normal-section;ina=keep*da>=-1e-9;inb=keep*db>=-1e-9
            if ina:result.append(a)
            if ina!=inb:result.append(a+(b-a)*(-da)/(db-da))
        return np.asarray(result)
    def emit(poly):
        if len(poly)<3:return
        for i in range(1,len(poly)-1):
            face=np.array([poly[0],poly[i],poly[i+1]])
            if np.linalg.norm(np.cross(face[1]-face[0],face[2]-face[0]))>1e-10:output.append(face)
    for tri in t:
        ds=tri@normal-section
        if ds.max()<-1e-9:output.append(tri);continue
        if ds.min()>1e-9:output.append(tri+shift);continue
        fixed=clip(tri,-1);moved=clip(tri,1);emit(fixed);emit(moved+shift)
        if ds.min()<-1e-9 and ds.max()>1e-9:
            for p,q in zip(fixed,np.roll(fixed,-1,axis=0)):
                if abs(p@normal-section)<1e-8 and abs(q@normal-section)<1e-8:
                    emit(np.array([p,p+shift,q+shift,q]));area+=direction*(p[0]*q[1]-q[0]*p[1])/2
    return np.array(output),abs(area)

def volume(t):return float(np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum()/6)

def topology(t):
    _,iv=np.unique(np.round(t.reshape(-1,3),5),axis=0,return_inverse=True);f=iv.reshape(-1,3);edges=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1);_,counts=np.unique(edges,axis=0,return_counts=True)
    areas=np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1)/2
    return {'triangles':len(t),'boundary_edges':int((counts==1).sum()),'nonmanifold_edges':int((counts>2).sum()),'zero_area_faces':int((areas<1e-10).sum()),'volume_mm3':volume(t)}

def stl(path,t):
    cr=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);norm=cr/np.maximum(np.linalg.norm(cr,axis=1,keepdims=True),1e-14)
    dtype=np.dtype([('n','<f4',(3,)),('v','<f4',(3,3)),('a','<u2')]);a=np.zeros(len(t),dtype=dtype);a['n']=norm;a['v']=t
    path.write_bytes(b'PoseDoll O8 research adaptation; mm; not production qualified'.ljust(80,b' ')+struct.pack('<I',len(t))+a.tobytes())

def candidate(length):
    original,_,_=restored_core();meshes={};receipts=[]
    for name,t in original.items():
        new,area=extend_section(t,-1 if name=='C01' else 1,length) if name in ('C01','C02') else (t.copy(),0.)
        expected=volume(t)+area*length;actual=volume(new)
        if abs(expected-actual)>1e-5:raise ValueError((name,expected,actual))
        check=topology(new)
        if check['boundary_edges'] or check['nonmanifold_edges'] or check['zero_area_faces']:raise ValueError((name,check))
        meshes[name]=new;receipts.append({'part':name,'added_length_mm':length if name in ('C01','C02') else 0,'section_area_mm2':area,'expected_volume_mm3':expected,'topology':check})
    return meshes,receipts

def main():
    rows=[]
    for length in (0,1,2,3,4):
        meshes,receipts=candidate(length);folder=OUT.parent/f'fork_extension_{length}mm';folder.mkdir(exist_ok=True)
        np.savez_compressed(folder/'core_meshes.npz',**meshes)
        for name,t in meshes.items():stl(folder/(name+'.stl'),t)
        result={'scope':'Four-part TUT mechanical core only. Original axes, journals, ring halves and magnet cup retained; outer fork bodies moved away from the pivot by planar-section extrusion. No PCB or connector qualification.',
                'extension_each_yoke_mm':length,'receipts':receipts,'parts':{name:{'bounds_mm':[*t.min((0,1)),*t.max((0,1))],'volume_mm3':volume(t),'stl':name+'.stl','sha256':hashlib.sha256((folder/(name+'.stl')).read_bytes()).hexdigest()} for name,t in meshes.items()},
                'source_mesh_sha256':hashlib.sha256((OUT/'component_meshes.npz').read_bytes()).hexdigest(),'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'physical_tested':False,'manufacturing_released':False}
        (folder/'manifest.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');rows.append({'extension_mm':length,'volume_total_mm3':sum(volume(t) for t in meshes.values())})
    print(json.dumps(rows))
if __name__=='__main__':main()
