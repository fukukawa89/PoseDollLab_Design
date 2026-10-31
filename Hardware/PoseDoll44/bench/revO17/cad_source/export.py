"""Export O17 printable solids, exact-source viewer and single-SKU inventory."""
from pathlib import Path
import copy,csv,hashlib,json,shutil,sys,collections,struct
import numpy as np
from geometry import H,OUT,BENCH,read,write,sha,move,homogeneous
from common import tri,from_tri_exact,pose,mesh_record
from fitted import build_fitted
from carriers_swept import ASSEMBLY_POSE
from export_print_batch import orient,signature
import print_io17 as print_io
PAGE=H/'tutorials/full-doll-o17';OLD=H/'bench/revO16'

def stl(path,shape):
    tt=tri(shape).astype('<f4')
    normals=np.cross(tt[:,1]-tt[:,0],tt[:,2]-tt[:,0]);length=np.linalg.norm(normals.astype(float),axis=1)
    # STL quantizes coordinates to float32. Drop only EXACT zero-area faces
    # introduced by quantization, preserving every nonzero face and boundary.
    mask=length>0;tt=tt[mask];normals=normals[mask]/length[mask,None]
    data=bytearray(b'PoseDoll O17 mm; design candidate; re-slice and test coupons'.ljust(80,b' '));data+=struct.pack('<I',len(tt))
    for t,n in zip(tt,normals):data+=struct.pack('<12fH',*n,*t.ravel(),0)
    path.write_bytes(data)

def main():
    changes=read(OUT/'changes.json')
    if changes['bad_solids'] or max(r['added_outside_old_mm3'] for r in changes['replacements'] if r['kind']!='magnet_cartridge')>1e-5:raise ValueError('invalid replacement geometry')
    p,m,st,fail,pr,prov=build_fitted('quinn',ASSEMBLY_POSE)
    if fail:raise ValueError(fail)
    changed={k:from_tri_exact(v).simplify(1e-4) for k,v in np.load(OUT/'changed_parts.npz').items()}
    anchor={r['part']:r['anchor'] for r in changes['replacements']}
    deleted={k for r in changes['replacements'] for k in r['replaces']}|set(changes['removed_parts'])
    omitted_fixtures={'fixture/gateway_base','fixture/gateway_lid'}
    newmeta={k:copy.deepcopy(m[anchor[k]]) for k in changed}
    folder=BENCH/'print_batch';folder.mkdir(parents=True,exist_ok=True);rows=[];print_ids={}
    for oldrow in read(OLD/'print_batch/manifest.json')['rows']:
        row=copy.deepcopy(oldrow);instances=[i for i in row['instances'] if i['part'] not in deleted|omitted_fixtures]
        if not instances:continue
        row['instances']=instances;row['quantity_by_character']={'universal':len(instances)}
        row['geometry_source']='O16 unchanged';rows.append(row)
        for i in instances:print_ids[i['part']]=row['id']
        for ext in ('stl','3mf'):shutil.copy2(OLD/'print_batch'/(row['id']+'.'+ext),folder/(row['id']+'.'+ext))
    unique=[];grouping=[]
    change_by_part={r['part']:r for r in changes['replacements']}
    for k,source in changed.items():
        M=np.asarray(newmeta[k]['transform']);S=np.asarray(change_by_part[k].get('local_service_frame',M));Q=S[:3,:3].copy()
        if np.linalg.det(Q)<0:Q=Q@np.diag([1,-1,1])
        basis=homogeneous(Q,S[:3,3]);s=move(source,np.linalg.inv(basis)@M).simplify(1e-4)
        match=None;error=0.
        for candidate in unique:
            t=candidate['shape']
            if abs(s.volume()-t.volume())>.01 or np.max(abs(np.array(s.bounding_box())-np.array(t.bounding_box())))>.0002:continue
            difference=max(0.,float((s-t).volume()))+max(0.,float((t-s).volume()))
            if difference<=.005:match=candidate;error=difference;break
        if match is None:
            match={'id':f'N{len(unique)+1:03}','shape':s,'instances':[]};unique.append(match)
        match['instances'].append({'character':'universal','part':k,'body':newmeta[k]['body'],'print_id':match['id']});print_ids[k]=match['id']
        grouping.append({'part':k,'print_id':match['id'],'symmetric_volume_difference_mm3':error})
    write(OUT/'print_grouping.json',{'scope':'Numerically equivalent service-frame shapes, not visually guessed duplication','maximum_bbox_delta_mm':.0002,'maximum_symmetric_volume_mm3':.005,'instances':grouping})
    for u in unique:
        s,bed=orient(u['shape']);s=s.simplify(1e-4);bed['mesh_cleanup_tolerance_mm']=0.0001;pid=u['id'];stl(folder/(pid+'.stl'),s);print_io.write_3mf(folder/(pid+'.3mf'),{pid:s})
        assert bed['components']==1
        rows.append({'id':pid,'instances':u['instances'],'quantity_by_character':{'universal':len(u['instances'])},
            'stl':'print_batch/'+pid+'.stl','stl_sha256':sha(folder/(pid+'.stl')),'bed':bed,'geometry_source':'O17 redesigned',
            'material_note':'PETG prototype; cassette leaf thickness 0.8 mm, real deflection/creep/holding tests required'})
        print('PRINT',pid,'x',len(u['instances']),flush=True)
    count=sum(r['quantity_by_character']['universal'] for r in rows)
    manifest={'schema':'POSEDOLL-O17-PRINT/1','status':'DIGITAL_CANDIDATE_TEST_COUPONS_FIRST','units':'mm','hardware_model':'universal',
        'rows':rows,'print_types':len(rows),'print_pieces':count,'physical_tested':False,'source_snapshot':'posedoll-o16-saved-20260930'}
    write(folder/'manifest.json',manifest)
    with (BENCH/'PRINT_UNIVERSAL.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f);w.writerow(['print_id','quantity','supports_required','file','parts'])
        for r in rows:w.writerow([r['id'],r['quantity_by_character']['universal'],r['bed']['supports_required'],r['stl'],'; '.join(i['part'] for i in r['instances'])])
    # Clear only obsolete files produced by earlier O17 export attempts.
    expected={r['id']+'.'+ext for r in rows for ext in ('stl','3mf')}
    assert folder.resolve().is_relative_to((H/'bench/revO17').resolve())
    for oldfile in folder.iterdir():
        if oldfile.suffix in ('.stl','.3mf') and oldfile.name not in expected:oldfile.unlink()
    # Count physical procurement deltas, including the deleted desktop G0.
    delta=collections.Counter(m[k]['sku'] for k in changes['removed_parts'] if m[k]['sku'] is not None)
    delta.update({'XIAO_ESP32S3':1,'SEEED_FPC_A02_65MM':1,'SCREW_M2_L8':4,'NUT_M2':4})
    proc=read(OLD/'procurement.json');newrows=[]
    for r in proc['characters'][0]['rows']:
        r=copy.deepcopy(r);r['net_quantity']-=delta[r['sku']]
        if r['net_quantity']<0:raise ValueError(r)
        if not r['net_quantity']:continue
        if r['sku']=='XIAO_ESP32S3':r['name_zh']='Seeed XIAO ESP32S3 普通版 ×1，USB直接采集；无G0、无摄像头'
        if r['sku']=='C1_CENTRAL_PCBA':r['name_zh']='C1-U装配变体：原C1裸板，D1必须不装；USB供主控，J7独立5V供传感器'
        r['optional_spares']=min(r['optional_spares'],max(0,int(np.ceil(r['net_quantity']*.1))))
        r['suggested_total']=r['net_quantity']+r['optional_spares'];newrows.append(r)
    for sku,label in [('MAGNET_BOND_ADHESIVE','少量非导电双组分胶，按厂家工艺固化；填磁铁侧壁间隙，保持底面就位；先做粘接与磁读数小样'),('USB_TETHER_TIES','USB线应力释放扎带2根，宽≤2.5 mm、厚≤1.2 mm；穿控制盒新开槽'),('USB_DATA_XIAO','电脑至XIAO的USB数据线；带数据导线，按实际插头与应力释放检查'),('USB_5V_2A_SUPPLY','独立稳压5V、额定至少2A的USB电源适配器；不是裸PD触发9V/12V'),('USB_5V_TO_PH2_CABLE','5V电源至J7的USB转PH2电源线，J7-1=5V、J7-2=GND；与数据线分开')]:
        newrows.append({'sku':sku,'name_zh':label,'category':'电子/线束','net_quantity':1,'optional_spares':0,'suggested_total':1})
    proc['characters'][0]['rows']=newrows;proc['status']='O17_CANDIDATE_C1_U_D1_DNP_REQUIRED';write(BENCH/'procurement.json',proc)
    write(OUT/'bom_comparison.json',{'O16_print_pieces':273,'O17_print_pieces':count,'removed_print_pieces':273-count,
        'reduction_percent':(273-count)/273*100,'O16_print_types':214,'O17_print_types':len(rows),'integrated_pairs':68,
        'removed_stock_quantities':dict(delta),'added_external_supply_and_cables':3,'added_adhesive_consumable':1,'added_tether_tie_pair':1,
        'raw_channels_before':46,'raw_channels_after':46,'semantic_dof_before':41,'semantic_dof_after':41,
        'C1_component_change':'D1 omitted from assembly BOM and placement; Gerber copper retained',
        'mechanical_joint_fasteners_removed':0,'accessory_fasteners_removed':16})
    # The raw FK and channel order are intentionally identical to O16.
    shutil.copytree(OLD/'profiles',BENCH/'profiles',dirs_exist_ok=True)
    profile=read(BENCH/'profiles/device_profile.json');profile['schema']='POSEDOLL-O17-DEVICE/1';profile['profile_id']='o17_usb_universal_v1'
    profile['source_geometry']={'revision':'O17','base':'O16 / Quinn lineage','raw_joint_centres_unchanged':True,'changes_file':'verification/changes.json'}
    profile['transport']={'schema':'P17R/1','type':'USB_SERIAL_JTAG','raw_channels':46,'nominal_scan_period_ms':100,'maximum_scan_duration_ms':60,'external_gateway':False}
    write(BENCH/'profiles/device_profile.json',profile)
    sys.path.insert(0,str(H/'cad/revO16'));from device import digest
    cal=read(BENCH/'profiles/calibration_INCOMPLETE.json');cal['schema']='POSEDOLL-O17-CALIBRATION/1';cal['profile_sha256']=digest(profile);write(BENCH/'profiles/calibration_INCOMPLETE.json',cal)
    # Remove the copied synthetic measurement: its digest belongs to O16.
    # The package manifest below excludes it; never treat it as O17 evidence.
    write(BENCH/'profiles/measurement_SYNTHETIC.json',{'status':'NO_O17_HARDWARE_CAPTURE','note':'Use source/test_device.py for synthetic checks; calibrate O17 before capture.'})
    wire=read(BENCH/'profiles/wiring.json');wire['schema']='POSEDOLL-O17-WIRING/1';wire['transport']='USB direct; six internal SPI chains unchanged';write(BENCH/'profiles/wiring.json',wire)
    shutil.copytree(OLD/'harness',BENCH/'harness',dirs_exist_ok=True)
    harness=read(BENCH/'harness/cut_and_binding_plan.json');harness['status']='INTERNAL_SENSOR_CHAIN_LENGTHS_RETAINED_USB_TETHER_REQUIRES_PHYSICAL_ROUTING';harness['o17_note']='Old battery/radio power notes are superseded by POWER_AND_USB.zh-CN.md. USB tethers are external and not covered by old length calculations.';write(BENCH/'harness/cut_and_binding_plan.json',harness)
    target=read(OLD/'target_adapter_contract.json');target['o17_note']='Same 41 semantic DOF and physical FK. P17R transport needs its own decoder; O16 firmware is not interchangeable.';write(BENCH/'target_adapter_contract.json',target)
    # Full-body viewer uses the actual O16 assemblies with exact replacement solids.
    PAGE.mkdir(parents=True,exist_ok=True);data=read(H/'tutorials/full-doll-o16/scene_universal.json');oldraw=np.fromfile(H/'tutorials/full-doll-o16/geometry_universal.bin',dtype='<f4').reshape(-1,6)
    first={o['label']:o for o in data['scenes'][0]['objects']};mesh_arrays={k:oldraw[v['first']:v['first']+v['count']] for k,v in data['meshes'].items()}
    new_mesh_ids={};centers={};locals_for_view={}
    for idx,(k,s) in enumerate(changed.items()):
        a=anchor[k];V=np.asarray(first[a]['matrix']).reshape(4,4);M=m[a]['transform'];shape=move(s,np.linalg.inv(V)@M)
        locals_for_view[k]=shape;mid='new'+str(idx);new_mesh_ids[k]=mid
        tt=tri(shape.simplify(.015)).astype(np.float32);normal=np.cross(tt[:,1]-tt[:,0],tt[:,2]-tt[:,0]);normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-30)
        mesh_arrays[mid]=np.concatenate([tt,np.repeat(normal[:,None,:],3,axis=1)],axis=2).reshape(-1,6)
        centers[k]=np.array(mesh_record(shape)['COM_mm'])
    bounds_neutral=None
    for scene in data['scenes']:
        orig={o['label']:o for o in scene['objects']};objects=[o for o in scene['objects'] if o['label'] not in deleted]
        for k in changed:
            o=copy.deepcopy(orig[anchor[k]]);M=np.asarray(o['matrix']).reshape(4,4);o.update(label=k,mesh=new_mesh_ids[k],print_id=print_ids[k],follows_part=k)
            o['center']=(M[:3,:3]@centers[k]+M[:3,3]).tolist();objects.append(o)
        scene['objects']=objects;scene['caption']='O17实际CAD：绿色为可拆打印件，蓝灰为骨架。姿势示意不等于实物可达：保留的O16干涉见验证报告。'
        if scene['pose']=='neutral':
            bb=[]
            for o in objects:
                vv=mesh_arrays[o['mesh']][:,:3];M=np.asarray(o['matrix']).reshape(4,4);world=vv@M[:3,:3].T+M[:3,3];bb.append(np.r_[world.min(0),world.max(0)])
            bb=np.array(bb);lo=bb[:,:3].min(0);hi=bb[:,3:].max(0);bounds_neutral={'min_mm':lo.tolist(),'max_mm':hi.tolist(),'size_mm':(hi-lo).tolist(),'source':'render mesh; exact height checked separately'}
    # Actual CAD comparison views, with separated O16 components at left.
    # These are service illustrations, not another full-body pose/collision test.
    for kind,label in [('sensor_cassette','托夹合一 · 零件对照'),('magnet_cartridge','磁铁座盖合一 · 零件对照')]:
        rr=next(r for r in changes['replacements'] if r['kind']==kind and '/C0' not in r['part'])
        key=rr['part'];A=np.asarray(rr['local_service_frame']);I=np.linalg.inv(A);objects=[]
        items=[]
        for j,oldkey in enumerate(rr['replaces']):items.append(('O16 / '+oldkey,move(p[oldkey],I),[-32,0,j*6],None))
        items.append(('O17 / '+key,move(changed[key],I@m[anchor[key]]['transform']),[32,0,0],print_ids[key]))
        for j,(name,shape,offset,pid) in enumerate(items):
            mid='detail_'+kind+'_'+str(j);tt=tri(shape.simplify(.005)).astype(np.float32);nn=np.cross(tt[:,1]-tt[:,0],tt[:,2]-tt[:,0]);nn/=np.maximum(np.linalg.norm(nn,axis=1)[:,None],1e-30)
            mesh_arrays[mid]=np.concatenate([tt,np.repeat(nn[:,None,:],3,axis=1)],axis=2).reshape(-1,6)
            M=homogeneous(np.eye(3),offset);objects.append({'mesh':mid,'label':name,'role':'print','color':[.28,.42,.57] if j==2 else [.42,.63,.49],'group':'all','print_id':pid,'sku':None,'matrix':M.ravel().tolist(),'center':(np.array(mesh_record(shape)['COM_mm'])+offset).tolist(),'explode':[0,0,j*4],'body':'detail'})
        data['scenes'].append({'pose':'detail_'+kind,'label':label,'objects':objects,'reference_bones':[],'view_center':[0,0,16],'view_radius':65,
            'caption':'左：O16两件分离；右：O17一体件。'+('PCB从开口滑入，释放弹片后可取出；M3拆卸口保留。' if kind=='sensor_cassette' else '磁铁侧向装入并粘接侧壁；原M2螺钉防脱，整只磁铁总成可更换。')})
    used={o['mesh'] for s in data['scenes'] for o in s['objects']};meshes={};arrays=[];offset=0
    for mid,arr in mesh_arrays.items():
        if mid not in used:continue
        meshes[mid]={'first':offset,'count':len(arr)};offset+=len(arr);arrays.append(arr)
    data['meshes']=meshes;data['status']='O17 简化小样候选 · '+str(count)+'件打印件 · 保留O16既有整机干涉，不能整机制造放行'
    data['print_index']=rows;data.pop('mass_budget_kg',None)
    data['coverage']=['整机仍有已知干涉：中立姿势前臂与骨盆架重叠，沿用O16；回归通过只说明未新增所查碰撞。','O16已冻结：26255df / posedoll-o16-saved-20260930。','34组传感板托夹合一，34组磁铁座盖合一；移除电池盖和G0两件外壳。',
        '保留46路测量和41个语义旋转自由度；没有减少可表达的关节姿态。',
        '保留原关节、磁铁与传感器的名义位置；一体件须做新装配检查，O16仍缺少连续全域避碰证明。',
        'USB数据直连，独立5V USB电源供传感器；C1-U板D1不装。无需摄像头。',
        '卡扣的形变、疲劳、打印误差和磁铁角向保持必须先做小样。','根部与手指仍未测量；目标角色的接触和穿模留给UE后期。']
    write(PAGE/'scene_universal.json',data);(PAGE/'geometry_universal.bin').write_bytes(np.concatenate(arrays).astype('<f4').tobytes())
    write(OUT/'viewer_geometry.json',{'status':'EXPORTED','mesh_count':len(meshes),'scenes':len(data['scenes']),'parts_per_scene':len(data['scenes'][0]['objects']),'neutral_bounds':bounds_neutral,'actual_cad':True})
    app=(H/'tutorials/full-doll-o16/app.js').read_text(encoding='utf-8-sig').replace('revO16','revO17').replace('O16','O17')
    app=app.replace("'质量预算约 '+data.mass_budget_kg.toFixed(2)+' kg · 尚未称重'","'打印件 273 → '+manifest.print_pieces+' · 保留46路测量'")
    app=app.replace("let center=[-15,0,245],radius=285;","let center=scene.view_center||[-15,0,245],radius=scene.view_radius||285;")
    app=app.replace("state.scene=Number(e.target.value);draw()","state.scene=Number(e.target.value);state.group='all';$('#group').value='all';state.zoom=1;partOptions();draw()")
    app=app.replace("const terms=[","const terms=[['sensor_cassette','一体传感板托夹'],['magnet_cartridge','侧装一体磁铁座盖'],")
    app=app.replace('data.scenes[0].objects','data.scenes[state.scene].objects').replace("state.scene=Number(e.target.value);state.group", "state.scene=Number(e.target.value);$('#group').disabled=!!data.scenes[state.scene].view_radius;state.group")
    app=app.replace('colors[o.role]||colors.print','o.color||colors[o.role]||colors.print')
    (PAGE/'app.js').write_text(app,encoding='utf-8');shutil.copy2(H/'tutorials/full-doll-o16/style.css',PAGE/'style.css')
    html=(H/'tutorials/full-doll-o16/index.html').read_text(encoding='utf-8-sig').replace('revO16','revO17').replace('REVO16','REVO17').replace('O16','O17')
    html=html.replace('273 件',str(count)+' 件').replace('214种打印件',str(len(rows))+'种打印件')
    html=html.replace('一个人偶，<br>记录你摆出的姿态。','更少零件，<br>保留完整姿态测量。')
    html=html.replace('一套机械，一份测量真值。','68组零件合并，装配通道保留。')
    html=html.replace('保留O15已有Quinn机械几何，统一为Universal，不再生成另一体型。新建实际机械轴与偏移的数字骨架；原始读数、标定、实体姿态分别留存。','O16已保存。O17将传感板托夹与磁铁座盖分别合一，移除电池和桌面网关。保留所有关节中心、传感器位置和46路测量，以USB直接采集。')
    html=html.replace('包含原有桌面附件与治具；所有几何沿用O15，当前仍是待验证候选。材料、支撑、配合与装配详见设计包。','保留焊接间距治具，去掉G0桌面网关。N编号为O17新件，P编号为沿用件。先打印小样验证卡扣和磁铁座，再决定整机加工。')
    html=html.replace('继承O15零件规格与电子方案，不把另一体型的数量相加。当前清单用于设计评审与样机验证，未自动下单。','主控由2块减为1块，去掉电池与两副天线。C1-U必须不装D1，USB数据与传感器5V供电分开接入。当前是样机清单。')
    html=html.replace('本轮检查单一型号数量、实际机械FK、数据故障处理、实体高度和查看器。','本轮检查一体件可打印实体、装配通道、外形包含关系、保留的机械FK、USB协议与查看器。')
    html=html.replace('几何来源可追溯','68组实际CAD合并 / 几何来源可追溯')
    (PAGE/'index.html').write_text(html,encoding='utf-8')
    print('O17',len(rows),'types',count,'pieces',len(changed),'changed shapes',flush=True)
if __name__=='__main__':main()
