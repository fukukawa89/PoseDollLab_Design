from production import *
from matplotlib.path import Path as PolygonPath
from scipy import ndimage

def main():
    inventory=load(OUT/'production_parts.json');zz=np.load(OUT/'production_meshes.npz');prod=load(OUT/'production_assembly.json')['parts'];parts=read_saved();allrows=[]
    for rec in inventory['structural_parts']:
        if rec['frame'] not in (sys.argv[1:] or ['l_ankle_roll','l_hip_flex','lumbar_flex','neck_yaw']):continue
        p=next(x for x in prod if x['name']==rec['part_number']);i=str(p['i']);s=md.Manifold(md.Mesh64(np.asarray(zz[i+'v'],dtype=np.float64),np.asarray(zz[i+'f'],dtype=np.uint64)))
        v=zz[i+'v'];cen=v.mean(0);_,basis=np.linalg.eigh(np.cov(v.T));basis[:,0]*=np.linalg.det(basis);loc=moved(s,T(-basis.T@cen,basis.T));pitch=.25
        lo,hi=bounds(loc);lo=np.floor(lo/pitch)*pitch-pitch;shape=np.ceil((hi-lo)/pitch).astype(int)+2
        xx,yy=np.meshgrid(lo[0]+np.arange(shape[0])*pitch,lo[1]+np.arange(shape[1])*pitch,indexing='ij');grid=np.c_[xx.ravel(),yy.ravel()];vox=np.zeros(shape,bool)
        for iz,z in enumerate(lo[2]+np.arange(shape[2])*pitch):
            inside=np.zeros(len(grid),bool)
            for poly in loc.slice(float(z)).to_polygons():inside^=PolygonPath(poly).contains_points(grid)
            vox[:,:,iz]=inside.reshape(shape[:2])
        lab,n=ndimage.label(ndimage.distance_transform_edt(vox,sampling=pitch)>.5);counts=np.bincount(lab.ravel());rows=[]
        for k in np.argsort(-counts[1:])+1:
            vol=counts[k]*pitch**3
            if vol<2:continue
            pts=np.argwhere(lab==k)*pitch+lo;world=pts@basis.T+cen;c=world.mean(0);near=[]
            for pp in parts:
                if pp['name'] not in rec['source_features']:continue
                ss=moved(pp['s'],np.linalg.inv(F0[rec['frame']])@F0[pp['frame']]);test=md.Manifold.sphere(.45,8).translate(c);over=(test^ss).volume()
                if over>.005:near.append(pp['name'])
            rows.append(dict(volume_mm3=vol,center_local_mm=c,bounds_local_mm=[world.min(0),world.max(0)],features=near))
        r=dict(part=rec['part_number'],frame=rec['frame'],cores=rows);allrows.append(r);print(json.dumps(r,default=lambda x:x.tolist(),ensure_ascii=False),flush=True)
    put(OUT/'verification/core_locations.json',allrows)
if __name__=='__main__':main()
