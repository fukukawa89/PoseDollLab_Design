"""O23B: replace free carrier spans by hollow anatomical load-bearing walls.

All lengths are mm. O22F7 release inputs are read-only. Unscaled joint libraries
are placed using a uniformly scaled FK; this is NOT a uniform scale of an STL.
The exact delivered meshes are used by the viewer, checks and renders.
"""
from pathlib import Path
import sys, json, copy, hashlib, argparse, struct, zipfile
from collections import Counter
import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.spatial import cKDTree
import manifold3d as md
import trimesh
import build_revo22_assembly as kin

R = Path(__file__).resolve().parents[1]
H = R / 'Hardware/PoseDoll44'
B = H / 'bench/revO23'
SRC = H / 'bench/revO22/O22F7_PLA_AssemblyRevision/assembly/tutorials/assembly-o22'
CFG = H / 'cad/revO23/parameters.json'
REV = json.loads(CFG.read_text('utf-8-sig'))['revision']
TAG = REV.split('-')[0]

def read(p): return json.loads(Path(p).read_text('utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def plain(v):
    if isinstance(v, np.ndarray): return v.tolist()
    if isinstance(v, np.generic): return v.item()
    raise TypeError(type(v).__name__)
def put(p, d):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2, default=plain,
                            allow_nan=False)+'\n', encoding='utf8')
def union(ss):
    ss = [s for s in ss if not s.is_empty()]
    return md.Manifold.batch_boolean(ss, md.OpType.Add) if ss else md.Manifold()
def move(s, M): return s.transform(np.asarray(M)[:3, :])
def vf(s):
    m = s.to_mesh64()
    return np.array(m.vert_properties,copy=True)[:, :3], np.array(m.tri_verts,copy=True)
def triangles(s):
    v,f=vf(s)
    return v[f]
def solid(v, f):
    m = md.Mesh64(np.asarray(v, np.float64), np.asarray(f, np.uint64))
    m.merge()
    s = md.Manifold(m)
    if str(s.status()) != 'Error.NoError': raise ValueError(str(s.status()))
    return s
def from_tri(t):
    v, idx = np.unique(np.asarray(t).reshape(-1, 3), axis=0, return_inverse=True)
    return solid(v, idx.reshape(-1, 3))
def box(lo, hi):
    lo, hi = np.array(lo), np.array(hi)
    return md.Manifold.cube(hi-lo).translate(lo)
def ball(p, r): return md.Manifold.sphere(r, 48).translate(p)
def capsule(a, b, r):
    a, b = np.asarray(a), np.asarray(b); d = b-a; length = np.linalg.norm(d)
    if length < 1e-7: return ball(a, r)
    z = d/length; x = np.cross(np.eye(3)[np.argmin(abs(z))], z); x /= np.linalg.norm(x)
    cylinder = md.Manifold.cylinder(length, r, circular_segments=24)
    return cylinder.transform(np.c_[x, np.cross(z, x), z, a]) + ball(a, r) + ball(b, r)
def token(mm):
    return 'f:'+mm['body'] if mm['owner']=='rigid_frame' else 'j:'+mm['module']+':'+mm['owner']
def frames(p, raw):
    ff = kin.forward(p, raw); out = {'f:'+k:v for k,v in ff.items()}
    for j in p['joints']:
        q = [raw[k] for k in j['raw_ids']]; kind = j['kind']
        mount = ff[j['parent']] @ np.array(j['parent_to_mount_mm'])
        if kind in ('tut','wide_tut'): fs = kin.b.b.L.tut.frames(q)
        elif kind=='three_axis': fs = kin.b.b.L.three_axis.frames(q)
        elif kind=='ankle_core': fs = {'C02':np.eye(3),'ring':kin.b.b.rot(1,-q[1]),'C01':kin.b.b.rot(1,-q[1])@kin.b.b.rot(0,q[0])}
        elif kind=='hinge': fs = {'parent':np.eye(3),'child':kin.b.b.rot(2,q[0])}
        else: raise ValueError(kind)
        for k,Q in fs.items():
            A = np.eye(4); A[:3,:3] = Q
            out['j:'+j['id']+':'+k] = mount @ A
    return out
def profile(scale):
    p = copy.deepcopy(kin.profile)
    p.update(profile_id='o23b_mt6701_proportioned_'+str(scale).replace('.','p'),
             status='DIGITAL_DESIGN_CANDIDATE_NOT_PHYSICALLY_QUALIFIED')
    matrices = [p['root_transform_mm']]
    matrices += [j[k] for j in p['joints'] for k in ('parent_to_mount_mm','rotor_to_child_mm')]
    matrices += [m['transform_mm'] for m in p['fixed_markers']]
    for A in matrices:
        for i in range(3): A[i][3] *= scale
    p['o23_design'] = dict(scale=scale, joint_hardware_scale=1.0,
        inherited_protocol='P21R/1', inherited_raw_channel_count=46,
        manufacturing_release=False, inherited_marker_note='O22 markers, not new skin extrema; see geometry report')
    if read(CFG).get('compact_wrist'):
        reference=read(H/'generated/revE/quinn/neutral_landmarks.json')['bone_landmarks_mm']
        old=kin.forward(p,p['neutral_raw_deg']);changes=[]
        for side in ('l','r'):
            flex=next(j for j in p['joints'] if j['id']=='hand_'+side+'.flex')
            dev=next(j for j in p['joints'] if j['id']=='hand_'+side+'.deviate')
            A=np.array(flex['parent_to_mount_mm']);G=np.array(flex['rotor_to_child_mm']);D=np.array(dev['parent_to_mount_mm']);E=np.array(dev['rotor_to_child_mm'])
            axis1=A[:3,2];axis2=(A@G@D)[:3,2]
            W=np.c_[axis2,-axis1,np.cross(axis2,-axis1)]
            assert np.max(abs(W.T@W-np.eye(3)))<1e-10 and np.linalg.det(W)>.999
            upper=np.linalg.norm(old['elbow_'+side][:3,3]-old['upperarm_'+side][:3,3])
            rupper=np.linalg.norm(np.array(reference['lowerarm_'+side])-reference['upperarm_'+side])
            rfore=np.linalg.norm(np.array(reference['hand_'+side])-reference['lowerarm_'+side])
            desired=upper/rupper*rfore
            elbow=old['elbow_'+side][:3,3];F=old['forearm_'+side];direction=old['hand_'+side][:3,3]-elbow;direction/=np.linalg.norm(direction)
            center=elbow+direction*desired;local=np.linalg.inv(F)@np.r_[center,1]
            mount=np.eye(4);mount[:3,:3]=W;mount[:3,3]=local[:3]
            rotor=np.eye(4);rotor[:3,:3]=W.T@(A@G@D@E)[:3,:3]
            joint=dict(id='wrist_'+side,kind='ankle_core',parent='forearm_'+side,child='hand_'+side,
                raw_ids=[dev['raw_ids'][0],flex['raw_ids'][0]],parent_to_mount_mm=mount.tolist(),rotor_to_child_mm=rotor.tolist(),
                measurement='MEASURED_COMPOSITION',design_note='Two intersecting wrist axes; ankle-core bearing family, MT6701 interfaces from final O22F7.')
            ix=p['joints'].index(flex);p['joints'][ix]=joint;p['joints'].remove(dev)
            changes.append(dict(side=side,old_elbow_to_hand_mm=float(np.linalg.norm(old['hand_'+side][:3,3]-elbow)),
                new_elbow_to_wrist_mm=float(desired),neutral_wrist_mm=center.tolist(),reference='Quinn mesh reference, scaled by preserved upper-arm length',
                axes_order=joint['raw_ids']))
        p['o23_design']['compact_wrists']=changes
    return p

def controller_corner(cfg):
    return np.asarray(cfg['controller_front_corner_neutral_mm'],float)

def controller_shell():
    # Independent source geometry from O22 build_revo22_assembly.model().
    bb=kin.b.b
    floor=box([-3,-3,-.3],[83,97,2])
    wall=box([-3,-3,1],[83,97,25])-box([-1,-1,.9],[81,95,25.1])
    wall=wall-box([8,-4,8],[32,0,22])-box([40,94,8],[77,98,23])
    posts=union([(bb.cyl(2.8,1.9,5)-bb.cyl(.85,.5,10)).translate([x,y,0]) for x,y in [(3,3),(77,3),(3,91),(77,91)]])
    return floor+wall+posts

def load_baseline():
    sc = read(SRC/'scene.json'); meta = read(SRC/'assembly_metadata_c7.json')['meta']
    verts = np.fromfile(SRC/sc['geometry_url'], dtype='<f4').reshape(-1,6)
    target = read(H/'bench/revO22/profiles/default_pose.json')['raw_deg']
    ff = frames(kin.profile, target); cache = {}; parts = {}
    for o in sc['objects']:
        key = o['label']; mid = o['mesh']
        if mid not in cache:
            m = sc['meshes'][mid]
            cache[mid] = from_tri(verts[m['first']:m['first']+m['count'],:3].reshape(-1,3,3).astype(float))
        t = token(meta[key]); A = np.array(o['matrix']).reshape(4,4)
        local = np.linalg.inv(ff[t]) @ A
        parts[key] = dict(s=move(cache[mid],local), token=t, role=o['role'],
                          sku=o.get('sku'), old_id=o.get('print_id'), body=meta[key]['body'])
    return parts, meta, sc

def loft(stations, wall=0):
    """Stations: z, forward centre, lateral centre, AP radius, lateral radius.
    PCHIP avoids the bulging/oscillating contours of an unconstrained spline.
    Radial wall offset is a design parameter, not a certified normal thickness.
    """
    a=np.array(stations,float); a=a[np.argsort(a[:,0])]
    z=np.linspace(a[0,0],a[-1,0],max(12,int((a[-1,0]-a[0,0])/2)+1))
    f=PchipInterpolator(a[:,0],a[:,1:],axis=0)(z)
    angle=np.linspace(0,2*np.pi,64,endpoint=False); v=[]
    for zz,(cx,cy,rx,ry) in zip(z,f):
        v.extend(np.c_[cx+np.maximum(.3,rx-wall)*np.cos(angle),cy+np.maximum(.3,ry-wall)*np.sin(angle),np.full(64,zz)])
    v=np.array(v); triangles=[]
    for row in range(len(z)-1):
        for i in range(64):
            j=(i+1)%64; a0=row*64+i;b0=row*64+j;c0=(row+1)*64+i;d0=(row+1)*64+j
            triangles.extend([[a0,b0,c0],[b0,d0,c0]])
    v=np.vstack([v,[f[0,0],f[0,1],z[0]],[f[-1,0],f[-1,1],z[-1]]])
    for i in range(64):
        j=(i+1)%64; triangles.extend([[len(v)-2,j,i],[len(v)-1,(len(z)-1)*64+i,(len(z)-1)*64+j]])
    return solid(v,triangles)

def anatomy(body, F, scale, cfg):
    """Original designed silhouettes, located on the measured O22 neutral frames.
    No third-party robot artwork or CAD is incorporated.
    """
    S=scale/1.4; o=F[:3,3]; side=1 if body.endswith('_l') else -1
    def loc(rows):
        return [[o[2]+z*S,o[0]+x*S,o[1]+y*S,rx*S,ry*S] for z,x,y,rx,ry in rows]
    rows=None
    if body.startswith('upperarm_'):
        rows=loc([[-91,0,0,14,14],[-75,1,0,20,19],[-47,2,0,24,22],[-21,1,0,23,22],[-5,0,0,16,17]])
    elif body.startswith('thigh_'):
        rows=loc([[-154,1,0,20,21],[-128,4,0,27,25],[-85,5,0,34,30],[-42,1,2*side,35,33],[-14,-1,2*side,26,28]])
    elif body.startswith('calf_'):
        rows=loc([[-140,0,0,14,14],[-118,-2,0,17,17],[-78,-6,0,27,23],[-43,-5,0,29,25],[-15,0,0,21,21]])
    elif body.startswith('elbow_'):
        rows=loc([[-40,0,0,22,21],[-25,1,0,24,22],[-5,0,0,19,19]])
    elif body.startswith('forearm_'):
        rows=loc([[-52,0,0,17,15],[-37,1,0,20,18],[-17,1,0,23,21],[-3,0,0,22,21]])
    elif body.startswith('hand_') and '.flex_frame' in body:
        rows=loc([[-43,0,0,14,13],[-29,1,0,16,14],[-8,0,0,17,15]])
    elif body.startswith('hand_'):
        rows=loc([[-43,2,0,11,13],[-38,5,0,17,19],[-21,4,0,19,21],[-7,0,0,13,15],[0,0,0,10,11]])
    elif body=='head':
        rows=loc([[-4,7,0,15,18],[8,10,0,24,28],[27,7,0,33,33],[56,3,0,36,34],[80,0,0,28,27],[93,0,0,5,7]])
    elif body=='pelvis':
        rows=loc([[-29,-1,0,25,37],[-11,-3,0,36,62],[13,-4,0,42,72],[37,-1,0,34,62],[50,1,0,27,48]])
    elif body=='waist':
        rows=loc([[4,1,0,28,46],[20,2,0,30,46],[40,1,0,34,49],[57,-1,0,36,52]])
    elif body=='chest':
        rows=loc([[22,0,0,35,49],[46,0,0,43,57],[76,-3,0,42,61],[99,-6,0,33,51],[112,-8,0,20,29]])
    elif body.startswith('clavicle_'):
        # Short moving collar bones remain open. They receive a structural
        # oval bridge between retained interface pads in make_carrier().
        return None, None, []
    elif body.startswith('foot_'):
        # Loft in the foot's long X direction: rotate the z-loft into X.
        # The ankle and toe hinges remain distinct, with a gap at the ball.
        rows=[[-24,17,0,13,16],[-16,20,0,17,21],[7,20,0,20,23],[35,18,0,16,24],[49,16,0,11,24]]
        A=np.array([[0,0,1],[0,1,0],[-1,0,0.]])
        outer=loft([[z*S,x*S,y*S,rx*S,ry*S] for z,x,y,rx,ry in rows])
        inner=loft([[z*S,x*S,y*S,rx*S,ry*S] for z,x,y,rx,ry in rows],cfg['wall_mm'])
        inner=inner^box([-200,-200,rows[0][0]*S+cfg['wall_mm']],[200,200,rows[-1][0]*S-cfg['wall_mm']])
        M=np.eye(4);M[:3,:3]=A;M[:3,3]=o
        return move(outer-inner,M),move(outer,M),[]
    elif body.startswith('ball_'):
        rows=[[-4,15,0,10,24],[8,14,0,11,24],[23,13,0,10,22],[34,11,0,4,16]]
        A=np.array([[0,0,1],[0,1,0],[-1,0,0.]])
        outer=loft([[z*S,x*S,y*S,rx*S,ry*S] for z,x,y,rx,ry in rows]);inner=loft([[z*S,x*S,y*S,rx*S,ry*S] for z,x,y,rx,ry in rows],cfg['wall_mm'])
        inner=inner^box([-200,-200,rows[0][0]*S+cfg['wall_mm']],[200,200,rows[-1][0]*S-cfg['wall_mm']])
        M=np.eye(4);M[:3,:3]=A;M[:3,3]=o
        return move(outer-inner,M),move(outer,M),[]
    if rows is None: raise ValueError(body)
    adjustment=cfg.get('contour_adjustments',{}).get(body,{})
    if adjustment:
        z0,z1=rows[0][0],rows[-1][0]
        extension=adjustment.get('longitudinal_extension_mm',0)
        rows=[[z+extension*(z-z0)/(z1-z0),x,y,rx,ry] for z,x,y,rx,ry in rows]
        rows=[[z,x,y,rx*adjustment.get('ap_scale',1)+adjustment.get('ap_add_mm',0),
               ry*adjustment.get('lateral_scale',1)+adjustment.get('lateral_add_mm',0)] for z,x,y,rx,ry in rows]
    outer=loft(rows); inner=loft(rows,cfg['wall_mm'])
    if body=='head' or (body.startswith('hand_') and '.flex_frame' not in body):
        inner=inner^box([-1000,-1000,rows[0][0]+cfg['wall_mm']],[1000,1000,rows[-1][0]-cfg['wall_mm']])
    shell=outer-inner
    if body.startswith('hand_') and '.flex_frame' not in body:
        # One simple thumb mass, fused with the fist. No individual fingers.
        thumb=md.Manifold.sphere(1,48).scale([10*S,10*S,18*S]).translate(o+[10*S,side*15*S,-20*S])
        shell= shell+thumb
        outer=outer+thumb
    return shell,outer,rows

def interface_anchors(body, p, ff):
    out=[]
    for j in p['joints']:
        if body not in (j['parent'],j['child']): continue
        A=ff['f:'+j['parent']]@np.array(j['parent_to_mount_mm'])
        radius={'hinge':17,'tut':27,'wide_tut':30,'three_axis':26,'ankle_core':25}[j['kind']]
        out.append(dict(joint=j['id'],point=A[:3,3],guard_radius=radius,kind=j['kind']))
    return out

def span_web(original, anchors, scale):
    """Preserve endpoint lands; lengthen only the cross sections between them.
    Voronoi cuts are translated rigidly. Matching cut faces are extruded across
    the added length, giving a real internal web instead of assumed infill.
    """
    if len(anchors)<2:return md.Manifold()
    cells=[];spans=[]
    for i,a in enumerate(anchors):
        cell=original;pt=a['point']
        for j,b in enumerate(anchors):
            if i==j:continue
            d=b['point']-pt;d/=np.linalg.norm(d);mid=(b['point']+pt)/2
            cell=cell.split_by_plane(d,float(d@mid))[1]
        cells.append(cell.translate((scale-1)*pt))
        for j,b in enumerate(anchors):
            if j<=i:continue
            d=b['point']-pt;length=np.linalg.norm(d);z=d/length
            x=np.cross(np.eye(3)[np.argmin(abs(z))],z);x/=np.linalg.norm(x)
            mid=(pt+b['point'])/2;A=np.eye(4);A[:3,:3]=np.c_[x,np.cross(z,x),z];A[:3,3]=mid
            section_source=original
            for n,c in enumerate(anchors):
                if n in (i,j):continue
                normal=c['point']-pt;normal/=np.linalg.norm(normal)
                section_source=section_source.split_by_plane(normal,float(normal@((pt+c['point'])/2)))[1]
            section=move(section_source,np.linalg.inv(A)).slice(0)
            if section.is_empty():continue
            web=section.extrude((scale-1)*length+.02).translate([0,0,-.01])
            A[:3,3]+=(scale-1)*pt;spans.append(move(web,A))
    return union(cells+spans)

def make_carrier(key, part, oldff, newff, pnew, cfg, baseline):
    body=part['body']; scale=cfg['scale']; oldF=oldff[part['token']];newF=newff[part['token']]
    original=move(part['s'],oldF)
    housing=None
    if body=='chest':
        oldcontroller=np.array(read(H/'bench/revO22/mechanical/assembly_metadata.json')['controller_frame'])
        original=solid(*vf(original-move(controller_shell(),oldcontroller)))
    anchors=interface_anchors(body,kin.profile,oldff)
    custom=[]
    if cfg.get('compact_wrist') and (body.startswith('forearm_') or (body.startswith('hand_') and '.flex_frame' not in body)):
        side=body[-1];anchors=[a for a in anchors if not a['joint'].startswith('hand_')]
        joint=next(j for j in pnew['joints'] if j['id']=='wrist_'+side)
        M=newff['f:'+joint['parent']]@np.array(joint['parent_to_mount_mm'])
        which='C02' if body.startswith('forearm_') else 'C01'
        # Use the released F7 interface, including its final sensor revisions.
        donor_key='frame/calf_l' if which=='C02' else 'frame/foot_l'
        donor=baseline[donor_key];donor_joint=next(j for j in kin.profile['joints'] if j['id']=='foot_l')
        donor_M=oldff['f:'+donor_joint['parent']]@np.array(donor_joint['parent_to_mount_mm'])
        patch=move(donor['s'],np.linalg.inv(donor_M)@oldff[donor['token']])^ball([0,0,0],35)
        if which=='C01':
            core_box=np.asarray(kin.b.b.L.libraries()['ankle_core'][0]['C01'].bounding_box())
            patch=patch^box(core_box[:3]-.25,core_box[3:]+.25)
        custom.append(move(patch,M))
        anchors.append(dict(joint='wrist_'+side,point=M[:3,3]/scale,guard_radius=25,kind='ankle_core',custom=True))
    shell,outer,stations=anatomy(body,newF,scale,cfg)
    saved=[]; guards=[]; records=[]
    for a in anchors:
        pt=a['point']; r=a['guard_radius']; region=ball(pt,r+cfg['interface_overlap_mm'])
        if a.get('custom'):
            guards.append(ball(pt*scale,r));records.append(dict(joint=a['joint'],center_mm=pt*scale,guard_radius_mm=r,new_compact_interface=True));continue
        # Each old piece belongs to the closest attachment centre; do not
        # duplicate the old zig-zag middle when its two neighbourhoods overlap.
        for other in anchors:
            q=other['point'];v=q-pt;L=np.linalg.norm(v)
            if L<1e-5:continue
            z=v/L;x=np.cross(np.eye(3)[np.argmin(abs(z))],z);x/=np.linalg.norm(x)
            A=np.eye(4);A[:3,:3]=np.c_[x,np.cross(z,x),z];A[:3,3]=(pt+q)/2
            region=region^move(box([-500,-500,-1000],[500,500,0]),A)
        patch=original^region
        delta=(scale-1)*pt; patch=patch.translate(delta);guard=ball(pt*scale,r)
        if not patch.is_empty(): saved.append(patch)
        guards.append(guard)
        records.append(dict(joint=a['joint'],center_mm=pt*scale,guard_radius_mm=r,
                            inherited_patch_volume_mm3=patch.volume()))
    saved.extend(custom)
    protected=union(guards); interfaces=union(saved)
    if body=='chest' and housing is not None:
        saved.append(housing);interfaces=interfaces+housing
    interfaces=solid(*vf(interfaces))
    interface_mesh=vf(move(interfaces,np.linalg.inv(newF)))
    # Supply structural webs from retained joint lands to the new outer wall.
    # They are joined in the actual print solid, not separate cosmetic pieces.
    ribs=[]
    if shell is not None:
        ov,_=vf(outer);tree=cKDTree(ov)
        for patch in saved:
            pv,_=vf(patch)
            if len(pv)==0:continue
            dist,idx=tree.query(pv)
            candidates=np.argsort(dist)
            chosen=[]
            for n in candidates:
                q=pv[n]
                if any(np.linalg.norm(q-v)<7 for v in chosen):continue
                # Select real boundary points outside the protected centre.
                if any(np.linalg.norm(q-a['point']*scale)<a['guard_radius']+.5 for a in anchors):continue
                chosen.append(q);ribs.append(capsule(q,ov[idx[n]],cfg['rib_radius_mm']))
                if len(chosen)>=6:break
        addition=(shell+union(ribs))-protected
    else:
        # The collar bridge is still a load-bearing closed section, oval
        # rather than the original chain of bent rods.
        pts=[a['point']*scale for a in anchors]
        if len(pts)>1:
            bridge=capsule(pts[0],pts[-1],7)-capsule(pts[0],pts[-1],3.8)
            addition=bridge-protected
        else:addition=md.Manifold()
    if not any(a.get('custom') for a in anchors):
        web_source=original
        web=solid(*vf(span_web(web_source,anchors,scale)))
        addition=addition+web
    addition=solid(*vf(addition))
    result=solid(*vf(interfaces+addition))
    # A retained installation land can lie entirely inside the coarse spherical
    # opening. Connect it by explicit ribs, retaining a smaller precision core.
    # Exact moving-part checks, below, are required in addition to these cores.
    precision=union([ball(a['point']*scale, a['guard_radius']*.65) for a in anchors])-interfaces
    bridges=[]
    for attempt in range(8):
        components=sorted([s for s in result.decompose() if s.volume()>1e-4],key=lambda s:-s.volume())
        if len(components)<2:break
        main=components[0];mv,_=vf(main)
        def usable(v):
            keep=np.ones(len(v),bool)
            for a in anchors:keep &= np.linalg.norm(v-a['point']*scale,axis=1)>a['guard_radius']*.65+1
            return v[keep]
        mv=usable(mv)
        if not len(mv):break
        tree=cKDTree(mv);added=[]
        for comp in components[1:]:
            cv,_=vf(comp);cv=usable(cv)
            if not len(cv):continue
            distances,idx=tree.query(cv); order=np.argsort(distances)
            # Two separated web roots resist twisting better than a point stem.
            chosen=[]
            for n in order:
                if any(np.linalg.norm(cv[n]-q)<6 for q in chosen):continue
                chosen.append(cv[n]);added.append(capsule(cv[n],mv[idx[n]],cfg['rib_radius_mm'])-precision)
                if len(chosen)==2:break
        if not added:break
        bridge=union(added);bridges.append(bridge);result=result+bridge
    addition=addition+union(bridges)
    return move(result,np.linalg.inv(newF)),dict(body=body,source_part=key,
        interfaces=records,stations_world_mm=stations,wall_radial_offset_mm=cfg['wall_mm'],
        original_free_span_rebuilt_as_internal_web=True,exterior_is_structural=True,
        material_components=len([s for s in result.decompose() if s.volume()>1e-4]),
        connection_bridge_count=len(bridges),
        volume_mm3=result.volume(),added_structure_mm3=addition.volume()),move(addition,np.linalg.inv(newF)),interface_mesh

def stl(p,s):
    v,f=vf(s);mesh=trimesh.Trimesh(v,f,process=False);Path(p).parent.mkdir(parents=True,exist_ok=True)
    mesh.export(p,file_type='stl')

def main():
    cfg=read(CFG); B.mkdir(parents=True,exist_ok=True)
    if cfg.get('backpack_mount_revision') in ('detachable_rear_access_v2','compact_direct_v3'):
        raise RuntimeError('Current B2 is the checked B snapshot plus deepen_revo23_backpack.py. Use that continuation; this legacy whole-body builder does not reproduce the reviewed B2 refinements.')
    baseline,meta,scene=load_baseline();print('BASELINE',len(baseline),flush=True)
    p=profile(cfg['scale']);raw=kin.profile['neutral_raw_deg'];oldff=frames(kin.profile,raw);newff=frames(p,raw)
    new={};reports=[];adds={};keeps={}
    for key,part in baseline.items():
        if cfg.get('compact_wrist') and (key.startswith(('hand_l.flex/','hand_l.deviate/','hand_r.flex/','hand_r.deviate/')) or key in ('frame/hand_l.flex_frame','frame/hand_r.flex_frame')):continue
        if key.startswith('frame/'):
            s,report,added,keep=make_carrier(key,part,oldff,newff,p,cfg,baseline)
            new[key]=dict(part,s=s,role='structure');reports.append(dict(key=key,**report));adds[key]=added;keeps[key]=keep
            print('CARRIER',key,'components',report['material_components'],'cm3',round(s.volume()/1000,2),flush=True)
        else:
            new[key]=dict(part)
            if part['token'].startswith('f:'):
                # Controller pack and C7 split-joint fasteners stay unscaled.
                # Their owner coordinates are shifted as one assembly.
                if key.startswith('o22/'):
                    center=np.array(read(H/'bench/revO22/mechanical/assembly_metadata.json')['controller_frame'])[:3,3]
                    shift=oldff[part['token']][:3,:3].T@(controller_corner(cfg)-center-(newff[part['token']][:3,3]-oldff[part['token']][:3,3]))
                    new[key]['s']=part['s'].translate(shift)
                elif key.startswith('revision/clavicle_l.'):
                    joint=next(j for j in kin.profile['joints'] if j['id']=='clavicle_l.protract')
                    center=(oldff['f:'+joint['parent']]@np.array(joint['parent_to_mount_mm']))[:3,3]
                    shift=oldff[part['token']][:3,:3].T@((cfg['scale']-1)*(center-oldff[part['token']][:3,3]))
                    new[key]['s']=part['s'].translate(shift)
    if cfg.get('compact_wrist'):
        for side in ('l','r'):
            for key,part in baseline.items():
                if not key.startswith('foot_l/'):continue
                suffix=key[len('foot_l/'):];newkey='wrist_'+side+'/'+suffix
                owner=part['token'].split(':')[-1]
                new[newkey]=dict(part,token='j:wrist_'+side+':'+owner,body='hand_'+side,
                                old_id=part.get('old_id'),source_key=key)
    data={};items=[]
    for i,(key,part) in enumerate(new.items()):
        v,f=vf(part['s']);data[str(i)+'v']=v;data[str(i)+'f']=f
        items.append(dict(index=i,key=key,**{k:v for k,v in part.items() if k!='s'}))
    np.savez_compressed(B/'assembly.npz',**data)
    indexed={}
    for k,s in adds.items():indexed[k+'|v'],indexed[k+'|f']=vf(s)
    np.savez_compressed(B/'added_structure.npz',**indexed)
    indexed={}
    for k,(v,f) in keeps.items():indexed[k+'|v']=v;indexed[k+'|f']=f
    np.savez_compressed(B/'retained_interfaces.npz',**indexed)
    put(B/'assembly.json',dict(revision=REV,items=items));put(B/'profiles/device_profile.json',p)
    pose=read(H/'bench/revO22/profiles/default_pose.json')
    pose={k:v for k,v in pose.items() if k not in ('frames_mm','collision_clearance','solver_matrix_residuals')}
    pose['frames_mm']={k:v.tolist() for k,v in kin.forward(p,pose['raw_deg']).items()}
    pose['notes']=['O22F7 raw angles retained; O23B frame translations recalculated. Consult O23B verification, not O22 clearance.']
    pose['profile_id']=p['profile_id'];pose['manufacturing_release']=False
    put(B/'profiles/default_pose.json',pose)
    put(B/'design/carriers.json',reports)
    put(B/'design/baseline.json',dict(revision=REV,source=str(SRC.relative_to(R)),
        source_scene_sha256=sha(SRC/'scene.json'),source_geometry_sha256=sha(SRC/scene['geometry_url']),
        source_metadata_sha256=sha(SRC/'assembly_metadata_c7.json'),configuration_sha256=sha(CFG),
        baseline_part_count=len(baseline),baseline_prints=sum(x['role'] in ('frame','print') for x in baseline.values()),
        hardware=Counter(x['sku'] for x in baseline.values() if x['sku']),
        scale=cfg['scale'],joint_hardware_scale=1,manufacturing_release=False))
    print('SAVED',B,flush=True)

if __name__=='__main__': main()
