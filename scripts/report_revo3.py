"""Data-driven gates. Successful execution is not manufacturing acceptance."""
from revo3_evidence import *
ROLES={'G0','N1','N2','N3','N4','N5','N6'}
BOARDS={'proximal5','distal4','distal4_narrow','proximal5_side','distal4_side'}
REPORTS={'baseline':['baseline'],'offline':['offline'],'joint':['joint'],'assembly':['assembly'],'lifecycle':['lifecycle'],'electronics':['electronics'],'pcba_geometry':['pcba_geometry'],'mass_mechanics':['mass_properties_revO3','mechanics_analysis'],'packaging':['packaging'],'firmware':['firmware_builds']}

def exact_set(rows,key,expected):
    found=[r[key] for r in rows]
    if len(found)!=len(set(found)) or set(found)!=set(expected):raise ValueError('Missing/duplicate/extra '+key+' identity')

def assess(data,rid):
    issues=[]
    for name in [n for values in REPORTS.values() for n in values]:
        if name not in data or data[name].get('run_id')!=rid:issues.append('Missing/current run identity: '+name)
    if issues:return {'run_id':rid,'gates':{'V0':{'status':'FAIL','blocking':issues}},'evidence_issues':issues,'manufacturing_released':False}
    j=data['joint'];a=data['assembly'];life=data['lifecycle'];mass=data['mass_properties_revO3'];firmware=data['firmware_builds'];electronics=data['electronics']
    try:
        exact_set(firmware['builds'],'role',ROLES);exact_set(electronics['boards'],'kind',BOARDS);exact_set(data['pcba_geometry']['boards'],'kind',BOARDS)
        axes=read(HW/'mechanical_manifest/network_revM.json')['protocol_order'][3:]
        if set(mass['characters'])!={'manny','quinn'}:raise ValueError('Missing character')
        for ch in mass['characters'].values():
            exact_set(ch['load_rows'],'axis_id',axes)
            if ch['mass_policy']['hard_max_g'] is not None or ch['mass_policy']['exceedance_fails_design']:raise ValueError('User mass override not applied')
        partids={p['part_id'] for p in j['parts']};exact_set(j['parts'],'part_id',partids)
        if set(a['coverage']['assembled_part_ids'])!=partids or not a['coverage']['exact_identity_set'] or not a['coverage']['final_identity_set']:raise ValueError('Assembly BOM identity incomplete')
        if set(life['constraint_graph']['parts'])!=partids or life['constraint_graph']['unconnected_part_ids']:raise ValueError('Constraint graph part coverage incomplete')
        cfg=read(HW/'mechanical_manifest/lifecycle_states_revO3.json');expected={tuple(w+c) for w in cfg['wear_pairs_mm'] for c in cfg['compression_pairs_mm']};actual=[tuple(q[k] for k in ('front_wear_mm','rear_wear_mm','front_compression_mm','rear_compression_mm')) for q in life['states']]
        if set(actual)!=expected or len(actual)!=len(expected):raise ValueError('Lifecycle state set incomplete/duplicated')
    except (ValueError,KeyError,TypeError) as e:issues.append(str(e))
    if data['baseline']['status']!='PASS' or data['offline']['status']!='PASS':issues.append('Baseline or offline tests failed')
    if any(q['status']!='PASS' for q in firmware['builds']):issues.append('One or more firmware builds did not pass')
    nominal=j['cad_valid'] and j['single_connected_solid_per_part'] and not j['solid_intersections'] and not j['tool_solid_intersections'] and a['status']=='PASS_SAMPLED_NOMINAL_ONLY' and life['status']=='PASS_SCOPED_LIFE_GEOMETRY'
    gates={
      'V0':{'status':'FAIL' if issues else 'PASS','scope':'Current-run core reports, exact identities, sealed producer/consumer files, offline tests and seven role builds. Browser and final immutable run manifest are separate records.','blocking':issues},
      'V1':{'status':'PARTIAL' if nominal and not issues else 'FAIL_OR_BLOCKED','scope':'Single-joint nominal assembly and scoped wear geometry only','blocking':['摩擦层与钢背板结合强度未取得；最大实际弹簧力未知','输出接头、小螺钉工具、轴套固定与受载滑移仍待完成','公差叠加、生产螺纹、预紧变形和样件精度未验证']},
      'V2':{'status':'BLOCKED','blocking':['原生 PCB 仍有未连接网络；完整保护与失电隔离未闭合','PCBA 包络已由实际模型驱动，但部分器件与配合公差仍缺失','胸肩多轴、N2 与完整单臂线束尚未形成共同总装']},
      'V3':{'status':'NOT_RUN','blocking':['没有实物关节保持力、手感、精度与寿命测试']},
      'V4':{'status':'PARTIAL_OFFLINE_ONLY','blocking':['七角色构建与离线协议反例可验证；未烧录或做 CAN 台架','退避仍占用专门维护帧，不能宣称 99.9% 健康节点台架指标通过','8 ms 需要原始 END；严格 14 ms 需要共时钟总线 trace']},
      'V5':{'status':'BLOCKED','blocking':['完整多轴机构、真实偏置 profile、带线动作和 UE 联调未完成']}}
    changes=[{'id':'O3-01','status':'SCOPED_GEOMETRY_FIXED' if all(q['status']=='PASS_INTEGRAL_BASE_GEOMETRY' for q in life['constraint_graph']['sensor_towers']) else 'FAIL','result':'传感板支柱并入各自半盒，约束图按本轮 BOM 建立'}, {'id':'O3-02','status':life['status'],'result':'取消工作环内销；外耳钢背板；保留 0.6 mm 总磨损与非对称、压缩状态'}, {'id':'O3-03','status':'PARTIAL','result':'完整扭矩链条件计算；粘接、输出连接和实际最大预紧力阻塞制造'}, {'id':'O3-04','status':'MODEL_FIXED_PHYSICAL_CONTACTS_UNRESOLVED','result':'悬空点强制零反力；无壳体接触时不出反力和定型选簧'}, {'id':'O3-05','status':'LEDGER_RECONCILED_PROVISIONAL','result':'取消硬质量门槛；按明细移交已计入的 L6 紧固件/弹簧分配'}, {'id':'O3-06','status':'PARTIAL','result':'五种原生板方案，实际 PCBA、配合包络、服务区和 RF 区分开；完整多轴/单臂尚未建成'}, {'id':'O3-07','status':'BOUNDED_DEGRADED_RECOVERY','result':'有限快重试、逐节点指数退避、公平轮询与超时清理；仍有显式维护损失'}, {'id':'O3-08','status':'OFFLINE_SEMANTICS_FIXED','result':'8/14 ms 分层，时间戳帧率与长暂停，显式会话分段'}, {'id':'O3-09','status':'PRODUCER_CONSUMER_SEAL_IMPLEMENTED','result':'整套输出即时锁定；单 STEP、工具、配合头、板文件变异会阻塞下游'}]
    return {'schema':'revo3-gates-v1','run_id':rid,'gates':gates,'review_items':changes,'evidence_issues':issues,'fallback_91cm_preserved':data['baseline']['status']=='PASS','mass_policy':{'hard_max_g':None,'lightweight_preference_g':1200,'exceedance_fails_design':False},'physical_tested':False,'manufacturing_released':False}

def main():
    v,o=run_paths();data={};receipts=[]
    for producer,names in REPORTS.items():
        r=ArtifactReader(producer)
        for name in names:data[name]=r.json(v/(name+'.json'))
        receipts.append(r.receipt())
    status=assess(data,os.environ['REVO3_RUN_ID']);initial=ArtifactReader('baseline').json(v/'inputs.json')
    if sources()!=initial['source_sha256']:
        status['evidence_issues'].append('Sources changed after immutable run began');status['gates']['V0']['status']='FAIL'
    status['consumed_inputs']=receipts;save(v/'status.json',status)
    print(json.dumps(status['gates'],ensure_ascii=False),flush=True)
    if status['gates']['V0']['status']!='PASS':raise SystemExit(1)
if __name__=='__main__':main()
