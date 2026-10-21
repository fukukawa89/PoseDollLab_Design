"""Export review meshes, traceable hardware deltas and measured proportions."""
from verify_revo23 import *
import csv, shutil
from revo23_export import export_stl

NAMES={'pelvis':'骨盆','waist':'腰腹','chest':'胸廓','head':'头部',
 'upperarm_l':'左上臂','upperarm_r':'右上臂','elbow_l':'左肘下段','elbow_r':'右肘下段',
 'forearm_l':'左前臂','forearm_r':'右前臂','hand_l':'左握拳','hand_r':'右握拳',
 'thigh_l':'左大腿','thigh_r':'右大腿','calf_l':'左小腿','calf_r':'右小腿',
 'foot_l':'左后脚','foot_r':'右后脚','ball_l':'左前脚掌','ball_r':'右前脚掌',
 'clavicle_l':'左锁骨外段','clavicle_r':'右锁骨外段',
 'clavicle_l.protract_frame':'左锁骨内段','clavicle_r.protract_frame':'右锁骨内段'}

def writecsv(path, fields, rows):
    path.parent.mkdir(exist_ok=True,parents=True)
    with path.open('w',encoding='utf-8-sig',newline='')as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def export_selection(parts):
    result=[(k,v,f'{TAG}-S{n:02d}') for n,(k,v) in enumerate(((k,v) for k,v in parts.items() if v['role']=='structure'),1)]
    for k,n in [('o22/controller_housing',1),('o22/backpack_support',2),('o22/controller_lid',3)]:
        if k in parts:result.append((k,parts[k],f'{TAG}-C{n:02d}'))
    result += [(k,v,f'{TAG}-W{n:02d}') for n,(k,v) in enumerate(((k,v) for k,v in parts.items() if k.startswith('wrist_r/') and v['role'] in ('print','frame')),1)]
    return result

def main():
    parts=load_current();base,_,_=load_baseline();p=read(B/'profiles/device_profile.json')
    geometry=read(B/'verification/geometry.json');motion=read(B/'verification/daily_motion.json')
    assert geometry['geometry_sha256']==sha(B/'assembly.npz'),'Re-run checks on current geometry before packaging.'
    assert motion['geometry_sha256']==sha(B/'assembly.npz'),'Re-run motion checks before packaging.'
    assert motion['complete_policy'] and motion['passed'],'Pass the complete ordinary-motion policy before packaging.'
    edge=read(B/'verification/edge_paths.json')
    assert edge['geometry_sha256']==sha(B/'assembly.npz') and edge['passed'],'Complete the repaired-region transition check before packaging.'
    for name in ('fixed_interfaces','fixed_all_interfaces','magnet_seat_restoration'):
        fixed=read(B/'verification'/f'{name}.json')
        assert fixed['geometry_sha256']==sha(B/'assembly.npz') and fixed['passed'],f'Pass current {name} before packaging.'
    current=Counter(x['sku']for x in parts.values()if x['sku']);bom=[]
    source=H/'bench/revO22/O22F7_PLA_AssemblyRevision/五金采购清单.csv'
    with source.open(encoding='utf-8-sig',newline='')as f:
        for r in csv.DictReader(f):
            old=int(r['装机数量']);purchase=int(r['含备件合计']);new=current[r['型号']]
            bom.append({'SKU':r['型号'],'规格':r['规格'],'O22F7装机':old,TAG+'装机':new,
                '净新增':max(0,new-old),'原含备件建议采购':purchase,'若已买足含备件仍短缺':max(0,new-purchase)})
    writecsv(B/'五金变化表.csv',list(bom[0]),bom)
    rows=[];grows={r['key']:r for r in geometry['geometry']['rows']}
    for n,(key,part) in enumerate(((k,v)for k,v in parts.items()if v['role']=='structure'),1):
        rid=f'{TAG}-S{n:02d}';stem=key.split('/',1)[1].replace('.','_');out=B/'review_stl'/f'{rid}_{stem}.stl'
        export_stl(out,key,part['s']);g=grows[key]
        rows.append(dict(ID=rid,部位=NAMES.get(part['body'],part['body']),装配键=key,
            STL=str(out.relative_to(B)),实体连通块=g['components'],封闭网格=g['watertight'],
            材料体积_cm3=round(g['volume_mm3']/1000,3),
            PLA实体等效_g=round(g['solid_PLA_equivalent_g'],2),已制造放行='否'))
    writecsv(B/'结构件清单.csv',list(rows[0]),rows)
    accessories=[]
    for key,part,rid in export_selection(parts):
        if part['role']=='structure':continue
        title={'o22/controller_housing':'可拆背盒','o22/backpack_support':'背盒支撑架','o22/controller_lid':'背盒检修盖'}.get(key,'右腕镜像件 '+key.split('/',1)[1])
        stem=key.split('/',1)[1].replace('.','_')
        filename=f'review_stl/{rid}_{stem}.stl';export_stl(B/filename,key,part['s']);case=grows[key]
        accessories.append(dict(ID=rid,部位=title,装配键=key,STL=filename,实体连通块=case['components'],封闭网格=case['watertight'],
            PLA实体等效_g=round(case['solid_PLA_equivalent_g'],2),已制造放行='否'))
    if accessories:writecsv(B/'附件清单.csv',list(accessories[0]),accessories)
    f=kin.forward(p,p['neutral_raw_deg']);ref=read(H/'generated/revE/quinn/neutral_landmarks.json')['bone_landmarks_mm']
    scale=np.linalg.norm(f['elbow_l'][:3,3]-f['upperarm_l'][:3,3])/np.linalg.norm(np.array(ref['lowerarm_l'])-ref['upperarm_l'])
    comparisons=[]
    for title,a,b,ra,rb in [('上臂','upperarm_l','elbow_l','upperarm_l','lowerarm_l'),
        ('前臂（肘到腕）','elbow_l','hand_l','lowerarm_l','hand_l'),('大腿','thigh_l','calf_l','thigh_l','calf_l'),
        ('小腿','calf_l','foot_l','calf_l','foot_l'),('肩关节间距','upperarm_l','upperarm_r','upperarm_l','upperarm_r'),
        ('股骨参考点间距','thigh_l','thigh_r','thigh_l','thigh_r')]:
        actual=np.linalg.norm(f[b][:3,3]-f[a][:3,3]);target=np.linalg.norm(np.array(ref[rb])-ref[ra])*scale
        comparisons.append({'部位':title,TAG+'_mm':round(float(actual),4),'UE等比例目标_mm':round(float(target),4),'误差_mm':round(float(actual-target),6)})
    hip_centers=[]
    for side in ('l','r'):
        j=next(j for j in p['joints'] if j['id']=='thigh_'+side)
        hip_centers.append((f[j['parent']]@np.array(j['parent_to_mount_mm']))[:3,3])
    actual=float(np.linalg.norm(hip_centers[0]-hip_centers[1]))
    target=float(np.linalg.norm(np.array(ref['thigh_l'])-ref['thigh_r'])*scale)
    comparisons.append({'部位':'实际髋旋转中心间距',TAG+'_mm':round(actual,4),
        'UE等比例目标_mm':round(target,4),'误差_mm':round(actual-target,6)})
    writecsv(B/'UE比例对照.csv',list(comparisons[0]),comparisons)
    pose=read(B/'profiles/default_pose.json')
    for k in ('collision_clearance','solver_matrix_residuals'):pose.pop(k,None)
    pose['frames_mm']={k:v.tolist()for k,v in kin.forward(p,pose['raw_deg']).items()}
    pose['profile_id']=p['profile_id'];pose['manufacturing_release']=False
    pose['notes']=[f'O22F7 raw angles retained. {TAG} FK recalculated. Consult daily_motion.json.']
    put(B/'profiles/default_pose.json',pose)
    boards=sum(x['role']=='sensor' and k.endswith('/pcb')for k,x in parts.items())
    summary=dict(revision=REV,height_mm=geometry['geometry']['height_mm'],structure_count=len(rows),
        printed_instance_count=sum(x['role']in('structure','print','frame')for x in parts.values()),new_accessory_prints=[a['ID']for a in accessories],
        sensor_board_count=boards,raw_channels=len(p['raw_order']),joint_modules=len(p['joints']),
        quinn_reference_scale=float(scale),proportions=comparisons,hardware_changes=bom,
        actual_hip_centers_mm=hip_centers,upper_torso_raise_mm=p['o23_design'].get('upper_torso_raise_mm',0),
        structures_and_backpack_PLA_solid_equivalent_g=sum(x['solid_PLA_equivalent_g']for x in grows.values()),
        kinematics=geometry['kinematics'],invalid_parts=geometry['geometry']['invalid_parts'],
        daily_pose_count=motion['pose_count'],daily_required_contact_records=len(motion['blocking_contacts']),
        daily_nonadjacent_advisory_records=len(motion['nonadjacent_advisory']),
        additional_transition_pose_count=edge['pose_count'],transition_passed=edge['passed'],
        transition_required_contact_records=len(edge['blocking_contacts']),
        motion_policy=motion['policy_id'],motion_passed=motion['passed'],continuous_motion_proven=False,manufacturing_release=False,
        source_geometry_sha256=sha(B/'assembly.npz'),profile_sha256=sha(B/'profiles/device_profile.json'),
        configuration_sha256=sha(CFG),
        step_export_available=False,stl_purpose='Review and controlled trials only; not a released print package.')
    put(B/'DELIVERY.json',summary)
    (B/'review_stl/先读我.txt').write_text(f'这些 STL 是 {TAG} 设计评审用实体，单位 mm，使用各骨段局部坐标。\n尚未制造放行；先查看上一级 DESIGN.zh-CN.md 与 verification。\n实物装配、持姿和切片尚待验证。\n原 O22F7 打印文件没有修改。\n',encoding='utf8')
    print(json.dumps({k:summary[k]for k in ['height_mm','structure_count','printed_instance_count','sensor_board_count','joint_modules','invalid_parts','daily_required_contact_records']},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
