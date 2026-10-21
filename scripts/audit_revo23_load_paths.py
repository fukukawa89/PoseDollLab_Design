"""Voxel minimum-cut screen of every retained mounting land's load path.

This is a geometry screen, not FEA or a material qualification. Six-neighbour
voxel cuts are reduced by sqrt(3) to avoid reporting their grid-face area as
the true oblique cross-section. Exact CAD collision checks remain separate.
"""
from revo23_reinforcement import *
from scipy.ndimage import distance_transform_edt
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import maximum_flow,breadth_first_order
from PIL import Image,ImageDraw
import time


def raster(s,origin,shape,pitch):
    mask=np.zeros(shape,dtype=bool)
    if s.is_empty():return mask
    bb=np.array(s.bounding_box())
    for iz in range(max(0,int((bb[2]-origin[2])/pitch)),
                    min(shape[2],int(np.ceil((bb[5]-origin[2])/pitch))+1)):
        polys=s.slice(origin[2]+iz*pitch).to_polygons()
        if not polys:continue
        polys=sorted(polys,key=lambda v:-abs(np.sum(v[:,0]*np.roll(v[:,1],-1)-v[:,1]*np.roll(v[:,0],-1))))
        img=Image.new('1',(shape[0],shape[1]));draw=ImageDraw.Draw(img)
        for poly in polys:
            area=np.sum(poly[:,0]*np.roll(poly[:,1],-1)-poly[:,1]*np.roll(poly[:,0],-1))
            q=(np.asarray(poly)-origin[:2])/pitch
            draw.polygon([tuple(x) for x in q],fill=1 if area>0 else 0)
        mask[:,:,iz]=np.asarray(img).T
    return mask


def grid_graph(mask):
    coords=np.argwhere(mask);ids=np.full(mask.shape,-1,dtype=np.int32)
    ids[mask]=np.arange(len(coords));aa=[];bb=[]
    for axis in range(3):
        lo=[slice(None)]*3;hi=lo.copy();lo[axis]=slice(None,-1);hi[axis]=slice(1,None)
        a=ids[tuple(lo)];b=ids[tuple(hi)];ok=(a>=0)&(b>=0)
        aa.append(a[ok]);bb.append(b[ok])
    a=np.concatenate(aa);b=np.concatenate(bb)
    return coords,ids,a,b


def screen(key,s,keep,skin,pitch=1.0):
    t=time.time();bounds=np.array(s.bounding_box())
    origin=np.floor((bounds[:3]-2*pitch)/pitch)*pitch
    shape=tuple((np.ceil((bounds[3:]+2*pitch-origin)/pitch).astype(int)+1).tolist())
    occupied=raster(s,origin,shape,pitch)
    coords,ids,a,b=grid_graph(occupied);n=len(coords);rows=[]
    lands=sorted([c for c in keep.decompose() if c.volume()>50],key=lambda c:-c.volume())
    landing_masks=[raster(c,origin,shape,pitch)&occupied for c in lands]
    shell=raster(skin,origin,shape,pitch)&occupied
    print('GRID',key,shape,n,'lands',len(lands),flush=True)
    for number,land in enumerate(lands):
        source=landing_masks[number]
        if source.sum()<10:continue
        distance=distance_transform_edt(~source,sampling=pitch)
        target=shell.copy()
        for j,m in enumerate(landing_masks):
            if j!=number:target|=m
        target&=distance>=6
        if not target.any():continue
        sid=ids[source];tid=ids[target]
        u=np.r_[a,b,np.full(len(sid),n),tid]
        v=np.r_[b,a,sid,np.full(len(tid),n+1)]
        cap=np.r_[np.ones(2*len(a),np.int32),np.full(len(sid)+len(tid),n,np.int32)]
        graph=coo_matrix((cap,(u,v)),shape=(n+2,n+2)).tocsr()
        flow=maximum_flow(graph,n,n+1)
        residual=graph-flow.flow;residual.data=(residual.data>0).astype(np.int32);residual.eliminate_zeros()
        reachable=np.zeros(n+2,bool)
        reachable[breadth_first_order(residual,n,directed=True,return_predecessors=False)]=True
        cut=reachable[a]!=reachable[b]
        points=(coords[a[cut]]+coords[b[cut]])*.5*pitch+origin
        area=len(points)*pitch*pitch/np.sqrt(3)
        center=points.mean(0) if len(points) else None
        normal=None;spread=0.;zmod=0.
        if len(points)>3:
            q=points-center
            _,vec=np.linalg.eigh(q.T@q);normal=vec[:,0]
            uv=q@vec[:,1:];spread=float(np.max(np.ptp(uv,axis=0)))
            # Conservative polar-radius denominator and smaller planar second moment.
            moments=(uv.T@uv+np.eye(2)*len(uv)*pitch*pitch/12)*(pitch*pitch/np.sqrt(3))
            zmod=float(np.linalg.eigvalsh(moments).min()/max(pitch,np.linalg.norm(uv,axis=1).max()))
        row=dict(land=number,land_volume_mm3=land.volume(),voxel_pitch_mm=pitch,
            conservative_cut_area_mm2=area,conservative_section_modulus_mm3=zmod,
            cut_spread_mm=spread,cut_center_mm=center,cut_normal=normal,
            cut_points_mm=points,connected_voxel_path=bool(flow.flow_value),
            land_bbox_mm=land.bounding_box())
        rows.append(row)
        print('CUT',key,number,'area',round(area,2),'Z',round(zmod,2),'spread',round(spread,1),flush=True)
    return dict(key=key,seconds=round(time.time()-t,2),rows=rows)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--keys',nargs='*');ap.add_argument('--pitch',type=float,default=1.)
    ap.add_argument('--candidate',action='store_true');args=ap.parse_args()
    parts,p,cfg=load_d();kz=np.load(DHISTORY/'source/retained_interfaces.npz')
    reports=[];out=EROOT/('load_paths_candidate' if args.candidate else 'load_paths_D');out.mkdir(parents=True,exist_ok=True)
    for key,item in parts.items():
        if item['role']!='structure' or args.keys and key not in args.keys:continue
        s=item['s']
        if args.candidate and (EROOT/(key.replace('/','__')+'.npz')).exists():
            z=np.load(EROOT/(key.replace('/','__')+'.npz'));s=solid(z['v'],z['f'])
        target=local_skin(key,p,cfg)
        if item['body'].startswith('hand_'):
            N=frames(p,p['neutral_raw_deg'])[item['token']]
            A=canonical(item['body'],N,cfg)[3]
            target=s^move(box([-60,-60,-60],[60,60,-31]),np.linalg.inv(N)@A)
        report=screen(key,s,solid(kz[key+'|v'],kz[key+'|f']),target,args.pitch)
        path=EROOT/(key.replace('/','__')+'.npz')
        report['candidate_mesh_sha256']=sha(path) if args.candidate else None
        put(out/(key.replace('/','__')+'.json'),report);reports.append(report)
    put(out/'summary.json',dict(source_geometry_sha256=DHASH,rows=reports,
        method='Six-neighbour voxel max-flow/min-cut; grid-face area divided by sqrt(3). '
        'Section modulus is a conservative cut-point proxy, not exact stress or FEA.',
        physical_strength_verified=False,manufacturing_release=False))


if __name__=='__main__':main()
