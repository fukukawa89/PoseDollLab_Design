"""F3 exploration: preserve prior files, score uncovered support surface and layer growth."""
from pathlib import Path
import numpy as np, json, sys, time
import trimesh,shapely
from scipy.spatial import cKDTree
from build_revo22_fins import solid,union,polygon,vf,box,protected
import build_revo22_fins_v3 as builder
R=Path(__file__).resolve().parents[1];B=R/'Hardware/PoseDoll44/bench/revO22';O=B/'a1mini_fins_v3';OLD=B/'a1mini_fins_v2'

def surface_samples(v,f):
    tr=v[f];c=np.cross(tr[:,1]-tr[:,0],tr[:,2]-tr[:,0]);area=np.linalg.norm(c,axis=1)/2;normal=c/np.maximum(2*area[:,None],1e-20)
    # Critical horizontal/low-angle faces; also large sloping panels for distributed bracing.
    grouped={}
    for i in np.where((normal[:,2]<-.3)&(tr[:,:,2].max(axis=1)>.5))[0]:
        key=tuple(np.round(np.r_[normal[i],np.dot(normal[i],tr[i,0])],3))
        grouped[key]=grouped.get(key,0)+area[i]
    selected=[i for i in range(len(f)) if normal[i,2]<-.707 or (normal[i,2]<-.3 and grouped.get(tuple(np.round(np.r_[normal[i],np.dot(normal[i],tr[i,0])],3)),0)>150)]
    pts=[];weights=[];critical=[];faces=[]
    for i in selected:
        if area[i]<.0001:continue
        count=max(1,int(np.ceil(np.sqrt(area[i]/2.))))
        for j in range(count):
            for k in range(count-j):
                u=(j+1/3)/count;w=(k+1/3)/count
                q=tr[i,0]*(1-u-w)+tr[i,1]*u+tr[i,2]*w
                if q[2]>.5:
                    pts.append(q);weights.append(area[i]/(count*(count+1)/2));critical.append(normal[i,2]<-.707);faces.append(int(i))
    return np.asarray(pts).reshape(-1,3),np.asarray(weights),np.asarray(critical,dtype=bool),np.asarray(faces,dtype=int)

def audit(pid,folder,save=True):
    n=np.load(folder/'parts'/f'{pid}.npz');r=json.loads((folder/'design'/f'{pid}.json').read_text())
    s=solid(n['v'],n['f']);b=solid(n['fin_v'],n['fin_f']);t=solid(n['teeth_v'],n['teeth_f']);whole=union([s,b,t])
    points,weights,crit,fi=surface_samples(n['v'],n['f'])
    cp=np.array([q['contact_point_mm'] for q in r['teeth']])
    distances=cKDTree(cp).query(points)[0] if len(cp) and len(points) else np.full(len(points),999.)
    tm=trimesh.Trimesh(n['v'],n['f'],process=False)
    # Vertical visibility from bed. Only potential fin routes, not a final collision proof.
    blocked=np.zeros(len(points),bool)
    if len(points):
        hit,ri,_=tm.ray.intersects_location(points-np.array([0,0,.04]),np.tile([0,0,-1.],(len(points),1)),multiple_hits=False)
        blocked[ri]=True
    missed=(distances>4.)&(~blocked)
    bed=s.slice(.1).area()
    prev=whole.slice(.1);islands=[];overhangs=[]
    for z in np.arange(.3,whole.bounding_box()[5],.2):
        curr=whole.slice(float(z))
        for cc in curr.decompose():
            if cc.area()>.03 and (cc^prev.offset(.025)).area()<.001:
                islands.append({'z_mm':round(float(z),3),'area_mm2':cc.area(),'bounds_mm':list(cc.bounds())})
        outside=s.slice(float(z))-prev.offset(2.)
        if outside.area()>.05:
            overhangs.append({'z_mm':round(float(z),3),'area_mm2':outside.area(),'bounds_mm':list(outside.bounds())})
        prev=curr
    result={'id':pid,'bed_part_section_mm2':bed,'height_mm':float(s.bounding_box()[5]),
        'support_surface_sampling':'approx 2 mm2 per barycentric point; down faces nz < -0.707 plus planar groups >150mm2 with nz < -0.3; above 0.5mm',
        'contact_radius_mm':4.,'sample_count':len(points),'sampled_area_mm2':float(weights.sum()),
        'bed_visible_uncovered_area_mm2':float(weights[missed].sum()),'critical_visible_uncovered_area_mm2':float(weights[missed&crit].sum()),
        'blocked_critical_area_mm2':float(weights[blocked&crit].sum()),
        'missed_points_mm':points[missed].tolist(),'missed_weights_mm2':weights[missed].tolist(),
        'layer_islands':islands,'long_overhang_layers':overhangs,'max_long_overhang_area_mm2':max([q['area_mm2'] for q in overhangs],default=0),
        'max_fin_height_mm':max([q['height_mm'] for q in r['segments']],default=0),
        'max_fin_height_to_width':max([q['height_mm']/max(q.get('blade_width_mm',0),1) for q in r['segments']],default=0),
        'support_volume_mm3':r['support_volume_mm3'],'teeth_count':len(r['teeth'])}
    if save:
        (folder/'verification').mkdir(exist_ok=True)
        (folder/'verification'/f'{pid}_coverage.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(pid,folder.name,'h',round(result['height_mm'],1),'uncovered',round(result['bed_visible_uncovered_area_mm2'],1),
          'blocked',round(result['blocked_critical_area_mm2'],1),'islands',len(islands),'long',round(result['max_long_overhang_area_mm2'],1),'fins_h',round(result['max_fin_height_mm'],1),flush=True)
    return result

def candidates(pid):
    items={i['id']:i for p in json.loads((B/'a1mini/manifest.json').read_text())['plates'] if not p['optional'] for i in p['items']}
    vols={x['part']:x['volumes'] for x in json.loads((B/'a1mini_supports/design/all_protected_volumes.json').read_text())['objects']}
    rank=json.loads((OLD/'orientation'/f'{pid}.json').read_text())['ranked_candidates']
    oldori=json.loads((OLD/'design'/f'{pid}.json').read_text())['orientation']
    candidates=[('F2_angle',oldori)]
    candidates += [('axis_'+str(j),q) for j,q in enumerate(rank) if max(map(abs,q['gravity_in_source']))>.999999]
    records=[{'label':'F2_original','metrics':audit(pid,OLD,False)}]
    for label,ori in candidates:
        if len(sys.argv)>2 and label not in sys.argv[2:]:continue
        label=label+'_trim'
        dest=O/'candidates'/pid/label
        for d in ['parts','design','verification']:(dest/d).mkdir(parents=True,exist_ok=True)
        builder.O=dest;builder.choose=lambda _:ori
        before=time.time();builder.make(pid,items[pid],vols.get(items[pid]['part'],[]))
        stats=audit(pid,dest);stats['elapsed_s']=time.time()-before
        records.append({'label':label,'orientation':ori,'metrics':stats})
        (O/'candidates'/pid/'comparison_trim.json').write_text(json.dumps(records,indent=2),encoding='utf8')
if __name__=='__main__':
    candidates(sys.argv[1])

