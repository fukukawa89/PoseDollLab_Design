"""Export real compact-joint STEP and printed fit coupons; never release full-body manufacture."""
from pathlib import Path
import sys, json
import cadquery as cq
from compact_joint import *
OUT=ROOT/'generated/revO'
VERIFY=ROOT/'verification/revO'

def export_mesh(rows,path):
    meshes=[]
    for row in rows:
        if row['role']=='reservation':continue
        verts,triangles=row['shape'].tessellate(.35,.3)
        meshes.append({'name':row['name'],'color':COLORS.get(row['material'],'#929ead'),
                       'vertices':[[round(v.x,4),round(v.y,4),round(v.z,4)] for v in verts],'triangles':triangles})
    save(path,meshes)

def main():
    summary={}
    for fam in SPECS['joint_families']:
        rows,meta=module(fam);folder=OUT/'joints'/fam;folder.mkdir(parents=True,exist_ok=True)
        ass=cq.Assembly(name=f'RevO_{fam}_DESIGN_STUDY')
        for q in rows:
            if q['role']!='reservation':ass.add(q['shape'],name=q['name'])
            cq.exporters.export(q['shape'],str(folder/(q['name']+'.step')))
        ass.save(str(folder/(fam+'_joint_study.step')))
        journal_radius=meta['journal_mm']/2
        housing_entry=2*(journal_radius+1)
        rotor_entry=2*max(4.2,journal_radius+1.5)
        meta['coaxial_insertion_check']={'status':'FAIL' if rotor_entry>housing_entry else 'NOT_RUN', 'fixed_eye_opening_diameter_mm':housing_entry,'integral_rotor_entry_diameter_mm':rotor_entry,'reason':'Integral magnet boss/collar cannot pass the one-piece bearing eye. Split bearing cartridge or removable retained collar must be designed before prototype B.'}
        meta['unresolved'].append(meta['coaxial_insertion_check']['reason'])
        meta['parts']=[dict(name=q['name'],material=q['material'],role=q['role'],bounds_mm=bounds(q['shape']),
                           volume_mm3=q['shape'].Volume(),note=q['note']) for q in rows]
        # Small threshold; report reservations independently. No blanket "reservation" bypass.
        solid_hits=[];reserve_hits=[]
        for i,a in enumerate(rows):
            for b in rows[i+1:]:
                if a['role']==b['role']=='reservation':continue
                ba,bb=bounds(a['shape']),bounds(b['shape'])
                if not all(min(ba[k+3],bb[k+3])-max(ba[k],bb[k])>1e-6 for k in range(3)):continue
                v=a['shape'].intersect(b['shape']).Volume()
                if v>.001:
                    (reserve_hits if 'reservation' in (a['role'],b['role']) else solid_hits).append({'a':a['name'],'b':b['name'],'volume_mm3':round(v,5)})
        meta['solid_intersections']=solid_hits;meta['reservation_intersections']=reserve_hits
        meta['digital_intersection_status']='FAIL' if solid_hits else 'PASS'
        meta['reservation_check_status']='FAIL' if reserve_hits else 'PASS'
        meta['source_sha256']={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),Path(__file__).with_name('compact_joint.py'),ROOT/'mechanical_manifest/desktop_revO.json',ROOT/'electronics/sensor_revM_side/sensor_revM_side.step']}
        save(folder/'manifest.json',meta);export_mesh(rows,folder/'mesh.json');summary[fam]=meta
        print(fam,'mass subset',round(meta['modeled_mass_g_excluding_spring_fasteners_plug'],2),'g; solid intersections',len(solid_hits),'reservation intersections',len(reserve_hits),flush=True)
    # User-printable A-stage coupons only. Separate columns labelled in the companion map.
    folder=OUT/'prototypes';folder.mkdir(parents=True,exist_ok=True)
    coupon=box(74,28,5,(0,0,2.5))
    holes=[]
    for j,diam in enumerate((4.0,4.1,4.2,6.0,6.1,6.2)):
        x=-30+j*12
        coupon=coupon.cut(cylinder(diam/2,-.1,5.1).translate((x,0,0)))
        holes.append({'x_mm':x,'nominal_diameter_mm':diam})
    cq.exporters.export(coupon,str(folder/'A01_journal_fit_coupon.step'))
    cq.exporters.export(coupon,str(folder/'A01_journal_fit_coupon.stl'),tolerance=.025,angularTolerance=.1)
    # Board slot coupon tests only board edge / handling; no sensor gap release.
    boardcoupon=box(54,32,3,(0,0,1.5))
    slots=[]
    for i,width in enumerate((1.0,1.1,1.2)):
        x=-18+i*18
        ledge=box(14,12,6,(x,0,6)).cut(box(12.2,width,6.2,(x,0,6)))
        boardcoupon=boardcoupon.fuse(ledge);slots.append({'x_mm':x,'slot_width_mm':width})
    cq.exporters.export(boardcoupon,str(folder/'A02_board_edge_coupon.step'))
    cq.exporters.export(boardcoupon,str(folder/'A02_board_edge_coupon.stl'),tolerance=.025,angularTolerance=.1)
    save(folder/'coupon_map.json',{'status':'FIT_TEST_ONLY_NOT_LOAD_BEARING','A01':holes,'A02':slots,'print_orientation':'Flat base at Z=0 on bed','physical_tested':False,'full_body_print_release':False})
    save(VERIFY/'joint_study.json',summary)
    print('STEP studies and two printable A-stage coupons exported.')

if __name__=='__main__':main()
