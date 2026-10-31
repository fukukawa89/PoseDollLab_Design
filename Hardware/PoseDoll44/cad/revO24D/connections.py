"""Screen actual exported printed bodies for weak connecting ligaments.
Not FEA: a morphological core screen catches a narrow bridge between bulk regions.
"""
from validate import *
from matplotlib.path import Path as PolygonPath
from scipy import ndimage

def core(s,pitch=.35):
    lo,hi=np.array(s.bounding_box()).reshape(2,3)
    lo=np.floor(lo/pitch)*pitch-pitch;shape=np.ceil((hi-lo)/pitch).astype(int)+2
    xs=lo[0]+np.arange(shape[0])*pitch;ys=lo[1]+np.arange(shape[1])*pitch
    xx,yy=np.meshgrid(xs,ys,indexing='ij');grid=np.c_[xx.ravel(),yy.ravel()]
    vox=np.zeros(shape,bool)
    for iz,z in enumerate(lo[2]+np.arange(shape[2])*pitch):
        inside=np.zeros(len(grid),bool)
        for polygon in s.slice(float(z)).to_polygons():inside^=PolygonPath(polygon).contains_points(grid)
        vox[:,:,iz]=inside.reshape(shape[:2])
    distance=ndimage.distance_transform_edt(vox,sampling=pitch);rows=[]
    for radius in [.5,.75]:
        labels,n=ndimage.label(distance>radius);counts=np.bincount(labels.ravel());counts[0]=0
        vol=sorted([float(v*pitch**3) for v in counts if v*pitch**3>=2],reverse=True)
        rows.append(dict(erosion_radius_mm=radius,substantial_core_volumes_mm3=vol))
    return rows

def main():
    parts,z,ss=read_assembly();rows=[];started=time.time()
    for p,s in zip(parts,ss):
        if p['role'] not in ['structure','rotor','shell']:continue
        # Principal coordinates keep a long oblique beam from wasting a huge grid.
        v=z[str(p['i'])+'v'];cent=v.mean(0);_,basis=np.linalg.eigh(np.cov(v.T));basis[:,0]*=np.linalg.det(basis)
        local=moved(s,T(-basis.T@cent,basis.T));screen=core(local)
        n=len(screen[0]['substantial_core_volumes_mm3']);locator='sensor_holder' in p['name'];fine=None
        if n!=1:
            # Resolve aliasing before judging a near-threshold cavity or curved wall.
            fine=core(local,.20);n=len(fine[0]['substantial_core_volumes_mm3'])
        rows.append(dict(part=p['name'],role='PCB_locator' if locator else 'load_or_shell',mesh_components=len(s.decompose()),screen=screen,refined_pitch_mm=.20 if fine else None,refined_screen=fine,status='PASS' if n==1 else 'REVIEW_REQUIRED',core_count_0_5=n))
        if len(rows)%25==0:print('connection',len(rows),'review',sum(r['status']!='PASS' for r in rows),flush=True)
    # Deliberately reproduce the reported 0.20 by 18 edge, not claimed as original H04.
    blocks=box([0,0,0],[10,18,6])+box([20,0,0],[30,18,6])
    weak=blocks+box([9,0,0],[21,18,.2]);strong=blocks+box([9,0,0],[21,18,3.2])
    negative=core(weak,.25);positive=core(strong,.25)
    controls=dict(synthetic_reported_edge_mm=[.2,18],synthetic_reported_area_mm2=3.6,weak_detected=len(negative[0]['substantial_core_volumes_mm3'])==2,strong_bridge_mm=[3.2,18],strong_single_core=len(positive[0]['substantial_core_volumes_mm3'])==1,weak=negative,strong=positive)
    # Newly designed rod and plate net sections are explicit design dimensions.
    sections=[dict(name='new fixed chassis rails',diameter_mm=6.4,area_mm2=math.pi*3.2**2),dict(name='new hip fixed risers',diameter_mm=7,area_mm2=math.pi*3.5**2),dict(name='new hip moving rails',diameter_mm=6,area_mm2=math.pi*3**2),dict(name='new H2 metal pressure-plate web',thickness_mm=2,width_mm=14,area_mm2=28,note='2 mm stainless plate; holes are outside this web section. Not a thin FDM edge.')]
    review=[r['part'] for r in rows if r['status']!='PASS']
    put(OUT/'verification/connections.json',dict(status='PASS_SCREEN' if not review and controls['weak_detected'] and controls['strong_single_core'] else 'REVIEW_REQUIRED',geometry_sha256=sha(OUT/'assembly_meshes.npz'),pitch_mm=.35,minimum_substantial_core_mm3=2,controls=controls,parts=rows,review_parts=review,new_nominal_sections=sections,seconds=time.time()-started,scope='Every exported structure/rotor/shell. Exact manifold sections rasterized in principal coordinates, Euclidean erosion 0.5/0.75 mm, 6-neighbour cores. Detects narrow bridges between substantial regions, not a proof of stiffness, minimum wall, FDM anisotropy, fatigue or inter-part fastener adequacy. No pass inferred from mesh watertightness.'))
    print('CONNECTION REVIEW',review,flush=True)
if __name__=='__main__':main()
