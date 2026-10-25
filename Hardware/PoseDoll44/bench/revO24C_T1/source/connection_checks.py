"""Exported-STL connection screening, exact defect probes and assembly checks.
Closed/connected meshes alone do not prove robust load paths. This is a geometry
review, not FEA, physical stiffness, creep or wear certification.
"""
from kit import *
from matplotlib.path import Path as PolygonPath
from scipy import ndimage
from validate import overlaps
import time

def solid(m):
    return md.Manifold(md.Mesh(m.vertices.astype('float32'),m.faces.astype('uint32')))

def core_screen(m,pitch=.25):
    # Rasterise exact sections rather than dilating surface voxels. Grid phase
    # and resolution still limit this to screening, not minimum-wall metrology.
    s=solid(m);lo=np.floor(m.bounds[0]/pitch)*pitch-pitch
    shape=np.ceil((m.bounds[1]-lo)/pitch).astype(int)+2
    xs=lo[0]+np.arange(shape[0])*pitch;ys=lo[1]+np.arange(shape[1])*pitch
    xx,yy=np.meshgrid(xs,ys,indexing='ij');grid=np.c_[xx.ravel(),yy.ravel()]
    vox=np.zeros(shape,dtype=bool)
    for iz,z in enumerate(lo[2]+np.arange(shape[2])*pitch):
        inside=np.zeros(len(grid),bool)
        for ring in s.slice(float(z)).to_polygons():inside^=PolygonPath(ring).contains_points(grid)
        vox[:,:,iz]=inside.reshape(shape[:2])
    distance=ndimage.distance_transform_edt(vox,sampling=pitch);checks=[]
    for radius in [.5,.75]:
        labels,n=ndimage.label(distance>radius);counts=np.bincount(labels.ravel());counts[0]=0;islands=[]
        for i in np.argsort(counts)[::-1][:12]:
            volume=float(counts[i]*pitch**3)
            if volume<2:continue
            points=lo+np.argwhere(labels==i)*pitch
            islands.append(dict(volume_mm3=volume,bounds_in_print_mm=[points.min(0),points.max(0)]))
        checks.append(dict(erosion_radius_mm=radius,substantial_cores=islands))
    return dict(pitch_mm=pitch,minimum_reported_core_mm3=2,checks=checks)

def canonical_stl(base,p):
    m=trimesh.load(base/p['stl'],process=True);m.apply_transform(np.linalg.inv(np.array(p['print_matrix'])))
    if p['station']=='R':m.apply_transform(rot(Y,-90))
    return solid(m)

def bracket_probes(base,rows):
    checks=[]
    for id in ['H04','H05','R04','R05']:
        s=canonical_stl(base,rows[id]);sign=-1 if id.endswith('04') else 1
        if sign<0:
            # Actual rail attachment footprint just beyond its end. Legacy
            # 0.20 x 18 mm edge fails this geometric (not strength) requirement.
            probe=box([-25.999,-25,-9],[-25.979,-13,9]);area=float((s^probe).volume()/.020)
            checks.append(dict(part=id,name='Rear rail to fixed plate attachment',measured_area_mm2=area,minimum_area_mm2=120,passed=area>=119.99))
        probe=tube([0,sign*18,9.2],[0,sign*18,10],3.2,1.71)
        retained=float((s^probe).volume()/probe.volume())
        checks.append(dict(part=id,name='Continuous shaft-clamp roof annulus',probe_outer_radius_mm=3.2,probe_inner_radius_mm=1.71,retained_fraction=retained,passed=retained>1-1e-4))
    return checks

def review(id):
    b=id[:3]
    if b in ['W04','W05']:return 'Intentional removable liner: shell 0.70/0.60/0.50 mm; retaining arm D1.5, pad 1.2 mm. Thin material is distributed across the liner, not a massive plate attached by a thin edge. Cup supports friction load; tabs locate liner. Handle gently and inspect after support removal.'
    if b in ['W06','W07']:return 'One core at 0.5 mm erosion. At 0.75 mm, outer M2 retaining-nut regions separate across intentional 1.25 mm pocket floors. These locate the liner, not the main M3 preload path. Main arms D4.2; cup radial wall 2.25 mm. Actual cracks/creep remain physical checks.'
    if b in ['H04','R04']:return 'S2 continuous fixed-plate web and enlarged shaft-clamp boss. Exact rail attachment and roof probes below.'
    if b in ['H05','R05']:return 'S2 enlarged shaft-clamp boss; original rail/diagonal supports. Exact roof probe below.'
    if b in ['H01','H02','R01','R02']:return 'Continuous load lever into rotor hub; bolted half shells. Bearing seats, nut recesses and loading-hole ligaments reviewed, including all bearing allowance options.'
    if b in ['H03','R03']:return '5 mm floating pressure plate, continuous between preload screws and friction face; axial movement is intentional.'
    if b in ['H06','H07','R06','R07']:return 'OD10/ID4.6 annular spacer, radial wall 2.7 mm; no separate narrow attachment.'
    if b in ['H08','R08']:return 'Non-load-bearing scale ring 1.6 mm thick; marks leave nominal 1.05 mm. Not a clamp handle.'
    if b in ['W01','W02']:return 'Continuous D6 neck and square key, bolted halves. S1 captured metal guide stack retained; spherical roof over washer pocket about 1.08 mm is a retainer, not a preload annulus.'
    if b=='W08':return 'D14 pillar meets both broad blocks with full circular cross section; no thin-edge attachment.'
    if b=='W09':return 'Continuous lever/socket overlap; square key transmits torsion; external nut avoids thinning socket with nut pocket.'
    if b=='W03':return 'Solid magnet dummy, not a structural connector.'
    if b=='C01':return '5 mm fit coupon; local blind-hole floors 1 mm, not a structural fixture.'
    raise ValueError(id)

def main():
    started=time.time();data=json.loads((OUT/'assembly.json').read_text('utf8'));rows={p['id']:p for p in data['parts']}
    options=json.loads((OUT/'fit_options.json').read_text('utf8'))['parts'];scans=[]
    for p in [r for r in data['parts'] if r['printable']]+options:
        m=trimesh.load(OUT/p['stl'],process=True);screen=core_screen(m);thin=p['id'][:3] in ['W04','W05']
        ncore=len(screen['checks'][0]['substantial_cores']);ok=bool(m.is_watertight and len(m.split())==1 and (thin or ncore==1))
        scans.append(dict(part=p['id'],stl=p['stl'],stl_sha256=sha(OUT/p['stl']),intentional_thin_liner=thin,review=review(p['id']),passed=ok,**screen))
        print('CONNECTION',p['id'],ok,'cores@0.5',ncore,flush=True)
    probes=bracket_probes(OUT,rows)
    arrays=np.load(OUT/'assembly_meshes.npz')
    parts={p['id']:solid(trimesh.Trimesh(arrays['v'+str(p['index'])],arrays['f'+str(p['index'])],process=False)) for p in data['parts']}
    insertion=[]
    for st in ['H','R']:
        direction=(rot(Y,90)[:3,:3]@X) if st=='R' else X
        for sign in [-1,1]:
            nutid=st+'shaft_clamp_nut_'+str(sign);worst=0
            for d in np.linspace(0,12,49):
                s=parts[nutid].translate(direction*d)
                for p in data['parts']:
                    if p['station']!=st or not p['printable']:continue
                    t=parts[p['id']]
                    if overlaps(s,t):worst=max(worst,float((s^t).volume()))
            insertion.append(dict(nut=nutid,travel_mm=12,steps=49,max_intersection_mm3=worst,passed=worst<.02))
    baseline=json.loads((OUT/'verification/S1_baseline_hashes.json').read_text('utf8'))
    delta=[p['part'] for p in scans if p['stl_sha256']!=baseline['stl_files'][p['stl']]]
    oldbase=ROOT/'output/o24ct1-s2-reinforcement/before';regression=[]
    if (oldbase/'assembly.json').exists():
        oldrows={p['id']:p for p in json.loads((oldbase/'assembly.json').read_text('utf8'))['parts']}
        regression=bracket_probes(oldbase,oldrows)
        assert all(not p['passed'] for p in regression),regression
    bom_unchanged=sha(OUT/'BOM.json')==baseline['bom_json_sha256']
    passed=all(p['passed'] for p in scans+probes+insertion) and set(delta)=={'H04','H05','R04','R05','W06','W07'} and bom_unchanged
    result=dict(revision=REVISION,geometry_sha256=sha(OUT/'assembly_meshes.npz'),verification_source_sha256=sha(Path(__file__)),passed=passed,
        scope='26 base and 12 optional exported STL: exact attachment probes, 0.25 mm core screening and feature review. Not a global minimum-wall guarantee, FEA or physical certification.',
        scans=scans,bracket_probes=probes,shaft_nut_insertion=insertion,legacy_S1_probes=regression,changed_base_parts=delta,unchanged_optional_parts=12,hardware_bom_unchanged=bom_unchanged,elapsed_s=time.time()-started)
    put(OUT/'verification/connections.json',result)
    print('CONNECTIONS RESULT',passed,'changed',delta,'seconds',round(time.time()-started,1),flush=True)
    if not passed:raise SystemExit(1)

if __name__=='__main__':main()
