from common import *
import io
from export_stock import orientation,LABELS

COLORS={'structure':[.67,.77,.75],'metal':[.38,.41,.46],'spring':[.2,.4,.65],'friction':[.5,.4,.28],'bearing':[.5,.5,.5],'electronics':[.10,.45,.32],'magnet':[.8,.23,.20],'insulator':[.9,.8,.3]}

def run():
    a=load(OUT/'production_assembly.json');z=np.load(OUT/'production_meshes.npz');zz={};report=[];scene=trimesh.Scene()
    oldkit=load(BASE/'kit.json');old={p['part_number']:p for p in oldkit['structural_parts']+oldkit['hardware']};kit=dict(revision='O24E_LArm_Sensing_R5',structural_parts=[],hardware=[],electronics=[],soft_parts=[],inventory_on_hand='UNKNOWN',custom_machined_metal_count=0,cut_metal_count=0,source_production_sha256=sha(BASE/'production_meshes.npz'))
    for p in a['parts']:
        i=str(p['i']);m=trimesh.Trimesh(z[i+'v'],z[i+'f'],process=False);p['label']=LABELS.get(p['name'],p['label']);record={k:v for k,v in p.items() if k not in ['bounds_mm']};record['kit_label']=p['label'];record['spec']=old.get(p.get('source'),{}).get('spec',p.get('sku') or p['label'])
        if p['name'] in ['RP_keeper','RU_keeper','RF_keeper']:record['spec']='R4原件直接复用。先装W6L及内部金属，再合压盖；每处M3×16/W3/两颗普通M3螺母对顶，不使用NL3压盖锁母。与转子保持原间隙。'
        revised_specs={'SHOULDER_PITCH':'R4肩俯仰转子与外展固定叉；新增RP板托固定座和侧入口，保留原摩擦座、防脱结构及工具装入路径。','UPPER_ARM':'R4上臂转子与肘固定叉；新增RU板托固定座、圆角侧入口与连续加厚，避让肘最大屈曲和原装配工具。','FOREARM':'R4前臂转子与腕固定叉；新增RF板托固定座、圆角侧入口；原腕轴承、预紧和防脱不变。','KEEP_E-P018':'一体腕输出叉与手掌；复用磁铁盲座，恢复M2压片螺钉及锁母入口，保留原摩擦耳。','KEEP_E-P019':'R4双轴腕中心的四面摩擦座与定位筋保留；一体新增WD传感板支架和后盖，原内垫片入口可达。'}
        if p.get('reprint'):record['spec']=revised_specs[p['name']]
        if p['role']=='structure':
            before=m.volume;reused=bool(p.get('baseline_name') and not p.get('reprint'));rel=f'stl_print/{p["part_number"]}.stl';o=old.get(p.get('source'))
            if reused:
                shutil.copyfile(BASE/o['stl'],OUT/rel);R=np.array(o['print_matrix']);pm=trimesh.load(OUT/rel,process=True)
            else:
                if o:
                    R=np.array(o['print_matrix']);R[:3,3]=-(np.asarray(m.vertices)@R[:3,:3].T).min(0)
                else:R=orientation(np.asarray(m.vertices))
                solid=md.Manifold(md.Mesh64(np.array(m.vertices,copy=True),np.array(m.faces,dtype=np.uint64,copy=True)))
                tolerances=[0,.00002,.00005,.0001,.0002,.0005] if p['name']=='SHOULDER_PITCH' else [.002,.005,.01,.02]
                for tol in tolerances:
                    v,f=e.base.a.mesh_data(solid.as_original().simplify(tol));pm=trimesh.Trimesh(v,f,process=False);pm.apply_transform(R);blob=pm.export(file_type='stl');pm=trimesh.load(io.BytesIO(blob),file_type='stl',process=True)
                    if not pm.is_watertight:
                        mesh=md.Mesh64(np.array(pm.vertices,dtype=np.float64,copy=True),np.array(pm.faces,dtype=np.uint64,copy=True),tolerance=.0001);mesh.merge();fixed=md.Manifold(mesh)
                        if str(fixed.status())=='Error.NoError':
                            v,f=e.base.a.mesh_data(fixed.simplify(min(.001,max(tol,.00002))));candidate=trimesh.Trimesh(v,f,process=True);blob=candidate.export(file_type='stl');pm=trimesh.load(io.BytesIO(blob),file_type='stl',process=True)
                    if pm.is_watertight:break
                assert pm.is_watertight,p['name'];(OUT/rel).write_bytes(blob)
            chunks=list(pm.split());major=[c for c in chunks if abs(c.volume)>.01]
            assert pm.is_watertight and len(major)==1,p['name']
            if len(chunks)>1:
                assert not reused and sum(abs(c.volume) for c in chunks if abs(c.volume)<=.01)<.01
                pm=major[0];pm.export(OUT/rel)
            m=pm.copy();m.apply_transform(np.linalg.inv(R));m.export(OUT/'parts_assembly'/f'{p["part_number"]}.stl')
            record.update(stl=rel,assembly_stl=f'parts_assembly/{p["part_number"]}.stl',sha256=sha(OUT/rel),print_matrix=R.tolist(),print_bounds_mm=pm.bounds.tolist(),material='PLA',process='A1 mini / 0.4 mm / 0.12 mm / 5 walls / 100% infill',reuse_R4_byte_identical=reused,new_accessory=not bool(p.get('baseline_name')))
            kit['structural_parts'].append(record);report.append(dict(part_number=p['part_number'],name=p['name'],watertight=True,components=1,volume_delta_mm3=float(m.volume-before),byte_identical_R4=p.get('source') if reused else None,stl_sha256=record['sha256']))
        elif p['role']=='electronics':kit['electronics'].append(record)
        elif p['role']=='insulator':kit['soft_parts'].append(record)
        else:kit['hardware'].append(record)
        p.update(bounds_mm=m.bounds.tolist(),volume_mm3=float(m.volume),components=1,mass_centroid_mm=m.center_mass.tolist());zz[i+'v']=np.asarray(m.vertices);zz[i+'f']=np.asarray(m.faces)
        mm=m.copy();mm.apply_scale(.001);mm.visual.vertex_colors=np.array([*COLORS.get(p['role'],[.5]*3),1])*255;mat=FA[p['frame']].copy();mat[:3,3]*=.001;scene.add_geometry(mm,node_name=p['part_number']+' '+p['name'],transform=mat)
    np.savez_compressed(OUT/'production_meshes.npz',**zz);put(OUT/'production_assembly.json',a);put(OUT/'kit.json',kit);scene.export(OUT/'O24E_R5_sensing_arm.glb')
    shutil.copytree(BASE/'profiles',OUT/'profiles',dirs_exist_ok=True);shutil.copytree(BASE/'tooling',OUT/'tooling',dirs_exist_ok=True)
    put(OUT/'verification/stl_export.json',dict(status='PASS',geometry_sha256=sha(OUT/'production_meshes.npz'),parts=report,baseline_mechanical_test='User accepted R4 friction/pose holding on 2026-10-30; no R5 physical test yet.'))
    print('EXPORT',len(report),'printed bodies; R4 reused',sum(r['byte_identical_R4'] is not None for r in report),flush=True)

if __name__=='__main__':run()
