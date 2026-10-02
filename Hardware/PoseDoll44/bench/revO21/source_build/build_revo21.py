"""Build independent O21 cost-down design dossier. Never edits O20."""
from pathlib import Path
import json, shutil, hashlib
R=Path(__file__).resolve().parents[1]; H=R/'Hardware/PoseDoll44'; B=H/'bench/revO21'; OLD=H/'bench/revO20'
def put(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    B.mkdir(parents=True,exist_ok=True)
    p=read(OLD/'profiles/device_profile.json')
    p.update(schema='POSEDOLL-O21-DEVICE/1',profile_id='o21_mt6701_usb_universal_v1',status='COST_DOWN_ENGINEERING_CANDIDATE_NOT_PHYSICALLY_CALIBRATED')
    p['transport']={'protocol':'P21R/1','packet_bytes':248,'sensor':'MT6701CT-STD-R','banks':[14,16,16],'wire_clock_hz_candidate':25000,'preserve_ssi_24bit':True,'legacy_P17R_compatible':False}
    put(B/'profiles/device_profile.json',p)
    order=p['raw_order']
    torso=[k for k in order if k.startswith(('waist/','chest/','head/','clavicle_'))]
    legs=[k for k in order if k.startswith(('thigh_','calf_','foot_','ball_'))]
    arms=[k for k in order if k not in torso+legs]
    assert [len(x) for x in [torso,arms,legs]]==[14,16,16]
    old_nodes={n['raw_id']:n for c in read(OLD/'profiles/wiring.json')['chains'] for n in c['nodes']}
    groups=[]
    for bank,ids in enumerate([torso,arms,legs]):
        nodes=[]
        for channel,k in enumerate(ids):
            length=200 if k.startswith(('waist/','chest/','clavicle_')) else 300 if k.startswith(('head/','upperarm_','thigh_')) else 450 if k.startswith(('elbow_','forearm_','calf_')) else 600
            nodes.append({'raw_id':k,'raw_index':order.index(k),'bank':bank,'mux_channel':channel,'connector':f'{"ABC"[bank]}{channel+1:02}','sensor_part_O20':old_nodes[k]['part'],'quote_allowance_mm':length,'cut_length_released':False})
        groups.append({'bank':bank,'count':len(ids),'nodes':nodes})
    wire={'schema':'POSEDOLL-O21-WIRING/1','status':'ELECTRICAL_BINDING_FIXED_PHYSICAL_LENGTHS_UNRELEASED',
          'topology':'One central carrier; three independent 16:1 DO muxes, shared slot address, broadcast CLK/CSN per bank',
          'banks':groups,'gpio':{'enable':1,'address':[2,4,5,6],'clk':7,'csn':43,'data':[8,9,44]},
          'sensor_pad_order':{'1':'GND','2':'SENSOR_3V3','3':'CLK','4':'DO','5':'CSN'},
          'harness':'46 five-core 30AWG fine-strand flexible pigtails, sensor-side factory soldered, main-side matched keyed 5P connectors; two spare complete sensor+pigtail assemblies',
          'not_reused':['AS5048A daisy chain','old 6P FFC transitions','old cut lengths'],
          'quote_total_active_cable_m':sum(n['quote_allowance_mm'] for g in groups for n in g['nodes'])/1000,
          'cable_length_warning':'Back carrier location is provisional. Route along bone surfaces, retain moving service loops; measure before production.'}
    put(B/'profiles/wiring.json',wire)
    categories=[
      ('sensor','MT6701CT-STD-R 芯片，46 用＋2 备＋2 贴片损耗/余料',50,7.25,430,'公开阶梯价参考；国内含税价待询','30+ 单价 $1.0355；50 件 $51.775；7.00 汇率仅预算假设，约 ¥362.43。不能自动视为国内含税到手价。'),
      ('sensor_pcba','48 块传感 PCB、无源器件、单面 SMT、工程/钢网/分板/电测',1,180,320,'待询价预算','不含上一项芯片，不含线束焊接；最小起订及所有工程费计入'),
      ('carrier','1 块中央采集载板及元件、贴装、电测',1,130,230,'待询价预算','含 3×CD74HC4067、2×SN74LVC244A、1×SN74LVC125A、连接器、PCB 工程费；不含主控和下一项电源'),
      ('mcu','XIAO ESP32-S3 普通版及排针装配',1,55,75,'待询价预算','成熟 USB 主控；无须 Sense 摄像头配件'),
      ('power','独立 5V→3.3V 电源、保护、接口及加工',1,35,65,'待询价预算','AP3429A 参考拓扑；传感 rail 与 USB MCU 不并联；不得与载板报价重复计费'),
      ('fasteners','O20 金属标准件，含原清单备件和袋装取整',1,215,350,'待询价预算','保留肩轴、碟簧、垫片、螺钉螺母；不靠未验证材料代换压价'),
      ('magnets','D6×2.5 径向充磁磁铁，46 用＋5 备',51,45/51,80,'待询价预算','不可买成轴向充磁'),
      ('harness','48 套五芯尾线＋插头压接＋板端焊接＋标号/导通检查',1,180,300,'待询价预算','包含两套备件线各 600mm；线长为询价估计；不把焊接工作转嫁给用户'),
      ('printing','打印材料，按购买 1kg 计算',1,80,100,'待询价预算','已有打印机；包含支撑、一般损耗及新控制器支架材料，非切片实测耗材'),
      ('logistics','5V 2A 适配器、USB 数据/电源线、扎带胶、标定夹具耗材、合单运费',1,100,160,'待询价预算','报含税到手价；额外进口税或拆单费用必须追加'),
      ('reserve','一次装配杂费与差价预留',1,100,100,'预算预留','不支付多轮 PCB 改板、商业计量仪器或外包角度标定')]
    budget={'schema':'POSEDOLL-O21-BUDGET/1','date':'2026-09-30','currency':'CNY','target_cny':1500,
            'scope':'单套；已有打印机；用户打印及机械总装；电子板和线束委托加工；计入必要备件/最小订单/工程费/运费',
            'confirmed_supplier_quote_count':0,'prices_are_target_allocations':True,
            'excluded':['打印机购买','自己的打印、总装与标定工时','多个失败开发迭代','外包精密计量或购置计量仪器'],
            'rows':[{'id':a,'item':b,'quantity':c,'target_unit_cny':d,'target_total_cny':round(c*d,2),'stress_total_cny':e,'evidence':f,'notes':g} for a,b,c,d,e,f,g in categories],
            'sensor_reference':{'mpn':'MT6701CT-STD-R','lcsc':'C3003196','quantity':50,'tier_min':30,'usd_each':1.0355,'usd_total':51.775,'cny_per_usd_assumption':7.0,'fx_is_live_quote':False,'cny_reference_ex_tax_shipping':362.425,'url':'https://www.lcsc.com/product-detail/C3003196.html'},
            'quote_rule':'取得每项含税到手加工报价后替换目标值。超 1500 时先查电子加工最低收费、线束、肩轴；不删除测量轴；估算不等于已实现成本。'}
    budget['target_total_cny']=round(sum(x['target_total_cny'] for x in budget['rows']),2)
    budget['stress_total_cny']=sum(x['stress_total_cny'] for x in budget['rows'])
    budget['headroom_cny']=round(1500-budget['target_total_cny'],2)
    put(B/'budget.json',budget)
    hardware=read(OLD/'procurement.json')
    retained=[r for r in hardware['characters'][0]['rows'] if r['category']=='金属/磁铁标准件']
    put(B/'mechanical_procurement_O20.json',{'source_O20_sha256':sha(OLD/'procurement.json'),'rows':retained,'note':'原数量包含备件；不得更改配合尺寸冒充降本。'})
    put(B/'mechanical_baseline.json',{'commit':'900f572','tag':'posedoll-o20-lightweight-20260930',
        'archive_sha256':sha(OLD/'PoseDoll_O20_Universal_Design.zip'),'kinematics_sha256':sha(OLD/'profiles/device_profile.json'),
        'unchanged':['joint centers','bone carriers','hip outward offset 16mm each','O11 friction principle','46 raw axes; 41 semantic DOF'],
        'height_mm_O20':492.14044050920376,'sensor_board_outline_target_mm':[12,10,1],
        'new_sensor_electronics_and_wiring_cad_verified':False,'new_carrier_mount_cad_verified':False,
        'legacy_controller_enclosure_reused':False,'new_complete_doll_part_count_claimed':False,
        'note':'O20 preview/prints are mechanical baseline only. New sensor envelope, cable loops and carrier enclosure require integration before fabrication.'})
    src=B/'source';src.mkdir(exist_ok=True)
    for f in ['device.py','test_device.py']:shutil.copy2(OLD/'source'/f,src/f)
    shutil.copy2(OLD/'target_adapter_contract.json',B/'target_adapter_contract_O20_reference.json')
    shutil.copy2(OLD/'profiles/device_profile.json',B/'profiles/mechanical_reference_O20.json')
    put(B/'DESIGN_STATUS.json',{'revision':'O21','stage':'COSTED_ELECTRONICS_ENGINEERING_CANDIDATE',
        'raw_channels':46,'semantic_dof':41,'target_unit_cny':1500,'budget_allocation_cny':budget['target_total_cny'],
        'firm_supplier_quotes':False,'functional_scope_preserved_by_design':True,'new_sensor_accuracy_measured':False,
        'manufacturing_release':False,'complete_doll_cad_integrated':False,'ue_end_to_end_tested':False,
        'calibration_transferred_from_AS5048A':False,'camera_required':False,'motors_required':False,'contact_correction':False})
    print(json.dumps({'budget':budget['target_total_cny'],'stress':budget['stress_total_cny'],'channels':[len(g['nodes']) for g in groups],'cable_m':wire['quote_total_active_cable_m']},ensure_ascii=False))
if __name__=='__main__':main()
