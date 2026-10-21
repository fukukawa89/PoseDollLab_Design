"""Functional voids for removable supports, in the frozen STL's body frame.

Includes all 33 documented tie tunnels, eight wire channels, nearby actual
hardware envelopes, and three-axis small closed-cavity section screening.
These masks affect slicer supports only; none is subtracted from the model.
"""
from optimize_revo23_print import *
from present_revo23 import load_current
from channel_revo23_harness import sweep

def save(path,s):
    v,f=vf(s);np.savez_compressed(path,v=v,f=f)

def prepare(revision=2):
    parts=load_current();p=read(B/'profiles/device_profile.json');N=frames(p,p['neutral_raw_deg'])
    hardware={}
    for k,x in parts.items():
        if x['role'] not in ('metal','sensor'):continue
        s=move(x['s'],N[x['token']]);hardware[k]=(x,s,np.array(s.bounding_box()))
    seats=read(B/'harness/wire_seats.json')['seats'];channels=read(B/'harness/wire_channels.json')['rows']
    rows=read(EXPORT_ROOT/'repair.json')['rows'];outdir=OUT/f'guards_v{revision}';outdir.mkdir(exist_ok=True)
    for row in rows:
        rid=row['id'];key=row['key'];dest=outdir/(rid+'.npz')
        meta=outdir/(rid+'.json')
        if dest.exists()and meta.exists()and read(meta).get('stl_sha256')==row['stl_sha256']:continue
        m=trimesh.load(B/row['staged_stl'],process=True);host=solid(m.vertices,m.faces)
        T=N[parts[key]['token']];Ti=np.linalg.inv(T);world=move(host,T);bb=np.array(world.bounding_box())
        owner=parts[key]['token'];body=parts[key]['body']
        joint_ids={j['id'] for j in p['joints'] if body in (j['parent'],j['child'])}
        if owner.startswith('j:'):joint_ids={owner.split(':')[1]}
        def related(item):
            return item['token']==owner or any(item['token'].startswith('j:'+jid+':') for jid in joint_ids)
        guards=[];records=[];features=[]
        def add(s,name,category):
            void=s-host
            if void.is_empty():return
            guards.append(void);records.append(dict(feature=name,category=category,volume_mm3=void.volume()))
        for r in seats:
            if r['part']!=key:continue
            M=np.array(r['transform_body_mm']);w=r['reserved_channel_width_mm'];h=r['reserved_channel_height_mm']
            legacy=r.get('minimum_roof_thickness_mm')==2.7;low,high=(1.3,3.3) if legacy else (.6,2.4)
            s=move(box([-w/2-3.1,low,-1.7],[w/2+3.1,high,1.7]),M)
            add(s,r['id']+'/strap_tunnel','tie_tunnel')
            W=M.copy();W[:3,3]=r['wire_center_body_mm'];half=4.5 if r['body'].startswith('forearm_') else 6.
            add(move(box([-w/2,-h/2,-half],[w/2,h/2,half]),W),r['id']+'/bundle_space','wire_space')
        for r in channels:
            if r['part']!=key:continue
            a=next(x for x in seats if x['id']==r['a']);M=np.array(a['transform_body_mm'])
            add(sweep(np.array(r['centerline_body_mm']),M[:3,0],M[:3,1],r['width_mm'],r['height_mm']),r['a']+' to '+r['b'],'wire_channel')
        clip=box(m.bounds[0]-.5,m.bounds[1]+.5)
        offsets=np.array([[x,y,z] for x in (-.08,.08) for y in (-.08,.08) for z in (-.08,.08)])
        for k,(item,s,hb) in (hardware.items() if revision==2 else []):
            if not related(item):continue
            sep=np.maximum(np.maximum(hb[:3]-bb[3:],bb[:3]-hb[3:]),0.)
            if np.linalg.norm(sep)>.6:continue
            if s.min_gap(world,.6)>.55:continue
            verts=vf(move(s,Ti))[0]
            env=md.Manifold.hull_points((verts[:,None,:]+offsets).reshape(-1,3))^clip
            add(env,k,'assembled_hardware')
        # Recover closed small apertures directly from final geometry, not old
        # O22 transforms. Scan perpendicular to each part-local Cartesian axis.
        loops=[];large=[];count=0
        for angles in ([0,-90,0],[90,0,0],[0,0,0]):
            rotated=host.rotate(angles);bounds=rotated.bounding_box()
            candidates=[]
            for z in np.arange(bounds[2]+.15,bounds[5],.75):
                for poly in rotated.slice(float(z)).to_polygons():
                    signed=float(np.sum(poly[:,0]*np.roll(poly[:,1],-1)-poly[:,1]*np.roll(poly[:,0],-1))/2)
                    if -180<signed<-1.0 and max(np.ptp(poly,axis=0))<23:
                        g=md.CrossSection([poly[::-1]]).offset(.08,circular_segments=12).extrude(.95).translate([0,0,float(z)-.475])
                        g=g.rotate([-x for x in angles])
                        if revision>=4 and (abs(signed)>60 or max(np.ptp(poly,axis=0))>9):large.append(g)
                        elif revision>=5:candidates.append(dict(z=float(z),area=abs(signed),center=poly.mean(0),solid=g))
                        else:loops.append(g);count+=1
            if revision>=5:
                # A large curved recess produces tiny loops at its poles. Do
                # not misidentify one sampled cap as a precision fastener bore.
                # Retain small apertures supported by three comparable sections
                # spanning1.5 mm; preserve the full matching sampled chain.
                keep=set()
                for i,a in enumerate(candidates):
                    groups=[]
                    for dz in (-.75,.75):
                        groups.append([j for j,b in enumerate(candidates) if abs(b['z']-a['z']-dz)<.001 and
                            min(a['area'],b['area'])/max(a['area'],b['area'])>.65 and np.linalg.norm(a['center']-b['center'])<1.5])
                    if all(groups):keep.update([i]+groups[0]+groups[1])
                for i,a in enumerate(candidates):
                    if i in keep:loops.append(a['solid']);count+=1
                    else:large.append(a['solid'])
        if loops:add(union(loops),'three_axis_small_closed_cavities','section_screen')
        guard=union(guards);save(dest,guard)
        if revision>=4:save(outdir/(rid+'_open_recesses.npz'),union(large)-host)
        # Keep explicit wire-only masks separately for stronger reporting.
        wire=union([g for g,r in zip(guards,records) if r['category'] in ('tie_tunnel','wire_space','wire_channel')])
        save(outdir/(rid+'_wire.npz'),wire)
        put(outdir/(rid+'.json'),dict(id=rid,key=key,stl_sha256=row['stl_sha256'],features=records,guard_revision=revision,related_joint_ids=sorted(joint_ids),
            section_count=count,mask_sha256=sha(dest),volume_mm3=guard.volume(),
            minimum_comparable_section_span_mm=1.5 if revision>=5 else None,
            scope=('Exact documented wiring voids; small closed apertures <=60 mm2 and <=9 mm span, identified by three comparable sections spanning1.5 mm, sampled in three axes every0.75 mm. This rejects the isolated tiny section at the pole of a large curved open recess. Larger/open recesses remain separately recorded for removal review. Not exhaustive manufacturing-tolerance proof.' if revision>=5 else 'Exact documented wiring voids and closed apertures with section area<=60 mm2 and span<=9 mm sampled in three axes every0.75 mm (M3/M4 fastener and small magnet apertures). Larger open assembly recesses are recorded separately for support-removal inspection, not treated as small bores. Exterior hardware occupancy is not a printing prohibition. Not exhaustive manufacturing-tolerance proof.' if revision>=4 else 'Exact documented wiring voids and small closed apertures sampled in three axes every0.75 mm. Exterior assembled washers/screw heads are not holes and do not forbid removable supports on the exposed mounting surface. Open sensor recesses require visual removal review. Not an exhaustive manufacturing-tolerance proof.' if revision==3 else 'Exact documented wiring voids; only own-frame and immediately connected-joint hardware convex envelopes +0.08 mm; small closed sections sampled every0.75 mm. Nonadjacent hardware at the neutral pose is excluded. Not an exhaustive manufacturing-tolerance proof.')))
        print('GUARD',rid,'features',len(records),'sections',count,'volume',round(guard.volume(),1),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--revision',type=int,default=2);a=ap.parse_args();prepare(a.revision)
