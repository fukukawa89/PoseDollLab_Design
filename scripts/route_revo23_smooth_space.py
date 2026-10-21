"""Find round strut centrelines in actual swept free space, never in old material."""
from revo23_smooth import *
from audit_revo23_load_paths import grid_graph
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.interpolate import splprep,splev


class FreeRoutes:
    def __init__(self,space,other=None,pitch=1.25):
        self.pitch=pitch;self.space=space;self.other=other
        own=move(space.parts[space.key]['s'],space.M)
        bb=np.array(own.bounding_box());bb[:3]-=20;bb[3:]+=20
        self.origin=np.floor(bb[:3]/pitch)*pitch
        self.shape=tuple((np.ceil((bb[3:]-self.origin)/pitch).astype(int)+1).tolist())
        occupied=np.zeros(self.shape,bool);reflection=np.diag([1.,-1.,1.,1.])
        for source,mirror in [(space,False)]+([(other,True)] if other else []):
            for i,row in enumerate(source.records):
                s=row['solid'] if row['solid'] is not None else move(row['source'],row['transform'])
                if mirror:s=move(s,reflection)
                ob=np.array(s.bounding_box())
                if np.any(np.minimum(bb[3:],ob[3:])-np.maximum(bb[:3],ob[:3])<=0):continue
                occupied|=raster(s,self.origin,self.shape,pitch)
                if i%200==0:print('FREE GRID',space.key,mirror,i,flush=True)
        self.clearance=distance_transform_edt(~occupied)*pitch
        self.cache={}

    def paths(self,land,landings,radius):
        # Raster clearance is a search aid; every final complete solid must
        # separately pass exact CAD intersection against every actual obstacle.
        for margin in (.7,0.,-.7):
            threshold=radius+margin
            if threshold not in self.cache:
                mask=self.clearance>=threshold
                coords,ids,a,b=grid_graph(mask);c=self.clearance[mask]
                w=self.pitch*(1+4/np.maximum(1.,np.minimum(c[a],c[b])-radius+1)**2)
                graph=coo_matrix((np.r_[w,w],(np.r_[a,b],np.r_[b,a])),shape=(len(coords),len(coords))).tocsr()
                self.cache[threshold]=(mask,coords,ids,graph)
            mask,coords,ids,graph=self.cache[threshold]
            src=raster(land,self.origin,self.shape,self.pitch)&mask
            if not src.any():print('NO GRID ANCHOR',radius,margin,flush=True);continue
            targets=[]
            for j,t in enumerate(landings):
                ij=np.round((t['point']-self.origin)/self.pitch).astype(int)
                if np.any(ij<0) or np.any(ij>=self.shape) or not mask[tuple(ij)]:continue
                targets.append((j,int(ids[tuple(ij)])))
            for j,index in targets:
                dist,pred=dijkstra(graph,indices=index,return_predecessors=True)
                candidates=ids[src];rank=candidates[np.argsort(dist[candidates])[:30]]
                for start in rank:
                    if not np.isfinite(dist[start]):continue
                    path=[];cur=int(start)
                    while cur>=0:
                        path.append(coords[cur]*self.pitch+self.origin);cur=int(pred[cur])
                    if len(path)<3:continue
                    path=np.array(path);path=np.vstack([path,landings[j]['point']])
                    # Remove duplicate points and approximate the grid's stair
                    # steps with one continuous curve, not unions of balls.
                    path=path[np.r_[True,np.linalg.norm(np.diff(path,axis=0),axis=1)>.1]]
                    if len(path)<4:continue
                    for smooth in (len(path)*.4,len(path)*1.5,len(path)*4.):
                        try:
                            tck,u=splprep(path.T,s=smooth,k=3)
                            points=np.array(splev(np.linspace(0,1,max(24,len(path)*2)),tck)).T
                            points[0]=path[0];points[-1]=landings[j]['point']
                            yield points[0],j,points,'smooth free-space bend'
                        except ValueError:continue
