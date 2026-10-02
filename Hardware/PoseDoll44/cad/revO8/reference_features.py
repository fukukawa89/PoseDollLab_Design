"""Recover geometric features from the pinned TUT print file, without altering it.
Run with Python + numpy + Pillow. Face-connected components use the audit IDs.
"""
from pathlib import Path
import json,sys,hashlib,math
import numpy as np
R=Path(__file__).resolve().parents[4]; H=R/'Hardware/PoseDoll44'; P=R.parent
sys.path.insert(0,str(H/'research/tangible_2014_2016'))
from audit_sources import read_stl,connected
OUT=H/'generated/revO8/runs/o8_20260925_r1/reference'
SOURCE=P/'research/tangible_reuse_20260925/atamid/Hardware/Mechanics/jointTUT.stl'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def cylinders(t):
    v,iv=np.unique(np.round(t.reshape(-1,3),5),axis=0,return_inverse=True);f=iv.reshape(-1,3)
    cr=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);area=np.linalg.norm(cr,axis=1)/2;n=cr/np.maximum(2*area[:,None],1e-12)
    edge_to_face={};adj=[]
    for i,face in enumerate(f):
        for a,b in zip(face,np.roll(face,-1)):
            k=(min(a,b),max(a,b))
            if k in edge_to_face:adj.append((edge_to_face[k],i))
            else:edge_to_face[k]=i
    rows=[]
    for ax in range(3):
        cols=[j for j in range(3) if j!=ax];data={}
        for i,face in enumerate(t):
            if abs(n[i,ax])>1e-4 or area[i]<1e-8:continue
            pts=np.unique(np.round(face[:,cols],5),axis=0)
            if len(pts)!=2:continue
            q=n[i,cols];q=q/np.linalg.norm(q);data[i]=(pts.mean(0),q)
        bins={}
        for i,j in adj:
            if i not in data or j not in data:continue
            p1,n1=data[i];p2,n2=data[j]
            cross=n1[0]*n2[1]-n1[1]*n2[0]
            if abs(cross)<.008 or np.dot(n1,n2)<.5:continue
            A=np.array([[-n1[1],n1[0]],[-n2[1],n2[0]]]); c=np.linalg.solve(A,np.array([A[0]@p1,A[1]@p2]))
            radius=np.linalg.norm(t[i,0,cols]-c)
            if not .2<radius<35:continue
            key=tuple(np.round([*c,radius],2));bins.setdefault(key,set()).update([i,j])
        for key,indices in bins.items():
            if len(indices)<8:continue
            ids=np.array(sorted(indices));verts=t[ids].reshape(-1,3);rads=np.linalg.norm(verts[:,cols]-np.array(key[:2]),axis=1)
            rows.append({'axis':'xyz'[ax],'center_perpendicular_coords':list(key[:2]),'radius':round(float(np.median(rads)),5),
                         'axis_min':round(float(verts[:,ax].min()),5),'axis_max':round(float(verts[:,ax].max()),5),'facets':len(ids),
                         'radial_max_residual_mm':round(float(np.max(np.abs(rads-np.median(rads)))),6)})
    return sorted(rows,key=lambda x:(x['axis'],-x['facets']))

def main():
    expected=json.loads((H/'research/tangible_2014_2016/evidence.json').read_text())
    expected_sha=next(x['sha256'] for x in expected['sources'] if x['path_from_plan'].endswith('/jointTUT.stl'))
    assert sha(SOURCE)==expected_sha
    t=read_stl(SOURCE);groups,faces=connected(t,5);parts={}
    for i,g in enumerate(groups,1):
        if i==12 or i>17:continue
        s=t[g];lo=s.min((0,1));hi=s.max((0,1))
        raw_signed=np.einsum('ij,ij->i',s[:,0],np.cross(s[:,1],s[:,2])).sum()/6
        cr=np.cross(s[:,1]-s[:,0],s[:,2]-s[:,0]);a=np.linalg.norm(cr,axis=1)/2;n=cr/np.maximum(2*a[:,None],1e-15)
        planes=[]
        for k in range(3):
            mask=np.abs(n[:,k])>.999999
            for level in np.unique(np.round(s[mask,:,k].mean(1),3)):
                ids=mask & (np.abs(s[:,:,k].mean(1)-level)<.001)
                ar=float(a[ids].sum())
                if ar>3:planes.append({'axis':'xyz'[k],'position':float(level),'area_mm2':round(ar,4)})
        features=cylinders(s)
        parts[f'C{i:02d}']={'bounds_mm':[*lo.tolist(),*hi.tolist()],'volume_signed_mm3':raw_signed,'planes':planes,'cylinders':features}
        print(f'C{i:02d}',len(features),'cylinder groups',flush=True)
    save(OUT/'features.json',{'source_sha256':expected_sha,'source_file':str(SOURCE),'parts':parts,'excluded_surface_groups':[12,*range(18,37)],'exclusion_reason':'Peripheral print frame and thin connecting rods; classification to be checked against assembly features.','units':'mm assumed from original design, not STL metadata','physical_tested':False})
    np.savez_compressed(OUT/'component_meshes.npz',**{f'C{i:02d}':t[g] for i,g in enumerate(groups,1) if i!=12 and i<=17})
    assert sha(SOURCE)==expected_sha
    print('features saved',flush=True)
if __name__=='__main__':main()

