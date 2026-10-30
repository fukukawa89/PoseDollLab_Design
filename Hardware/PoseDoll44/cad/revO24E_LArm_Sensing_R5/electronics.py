from common import *

def prepare():
    target=OUT/'electronics';target.mkdir(exist_ok=True)
    origin=H/'bench/revO22';files={}
    for folder in ['sensor','carrier']:
        dst=target/'O22_reference'/folder;shutil.copytree(origin/'electronics'/folder,dst,dirs_exist_ok=True)
        for p in dst.rglob('*'):
            if p.is_file():files[p.relative_to(target).as_posix()]=sha(p)
    src=target/'firmware_source';shutil.copytree(origin/'firmware_source',src,dirs_exist_ok=True)
    p=src/'session.c';s=p.read_text('utf8').replace('>3000000','>60000000').replace('scan->start_us+100000','scan->start_us+20000').replace('scan->valid_mask!=P21_MASK','(scan->valid_mask & UINT64_C(0x77000)) != UINT64_C(0x77000) || !r5_tm_valid(scan->tm)');p.write_text(s,encoding='utf8')
    shutil.copyfile(HERE/'scanner_r5.inc',src/'main/scanner.inc')
    p=src/'raw46.h';s=p.read_text('utf8').replace('P21_BYTES=248','P21_BYTES=280').replace('words[46];','words[46],tm[8];')
    s=s.replace('#endif','uint8_t r5_crc4(uint32_t w);\nbool r5_tm_crc_ok(uint32_t w);\nuint16_t r5_tm_data(uint32_t w);\nbool r5_tm_valid(const uint32_t*t);\n#endif');p.write_text(s,encoding='utf8')
    p=src/'raw46.c';s=p.read_text('utf8').replace('{14,16,16,0,0,0}','{6,3,1,0,0,0}').replace('P21R','R5AR')
    s=s.replace('p+244','p+276').replace('p21_crc(p,244)','p21_crc(p,276)')
    s=s.replace('put(out+244,p21_crc(out,244),4);','for(unsigned j=0;j<8;j++)put(out+244+4*j,m->tm[j],4);put(out+276,p21_crc(out,276),4);')
    s=s.replace('if(!valid(&m))','for(unsigned j=0;j<8;j++)m.tm[j]=(uint32_t)get(p+244+4*j,4);\n if(!valid(&m))')
    s+='\n'+(HERE/'protocol_r5.c.inc').read_text('utf8');p.write_text(s,encoding='utf8')
    p=src/'main/main.c';s=p.read_text('utf8').replace('P21R','R5AR').replace('/* O21 prototype only. New SSI carrier required; never flash onto O20 wiring. */','/* R5 mixed six SSI + one TMAG, O22 carrier with dedicated GPIO3 CS jumper. */');p.write_text(s,encoding='utf8')
    # Keep project basename for compatibility with the inherited build.ps1; final binaries get a descriptive release name.
    shutil.copytree(H/'bench/revO24E/electronics/inherited_D/sensors/S1',target/'WD_TMAG5170A1',dirs_exist_ok=True)
    for name in ['arm_reader.py','calibrate.py','pose_bridge.py']:shutil.copyfile(HERE/name,target/name)
    limits={c['id']:next(a['limits_deg'] for a in PROFILE['axes'] if a['id']==c['axis']) for c in load(OUT/'channels.json')};measurements=[]
    for key,(lo,hi) in limits.items():
        for run,count in [('calibration',11),('validation_forward',5),('validation_reverse',5),('coupled',9) if key=='WD' else ('cross_joint',3)]:
            grid=[(f,d) for f in [-65,0,70] for d in [-20,0,30]] if run=='coupled' else [(None,float(q)) for q in np.linspace(lo,hi,count)]
            if run=='validation_reverse':grid=grid[::-1]
            for i,(flex,q) in enumerate(grid):
                row=dict(axis=key,run=run,reference_deg=q,capture=f'captures/{key}_{run}_{i+1:02}.json',reference_instrument='填写机械角度尺型号/读数依据',other_joints_pose='填写其余关节实际姿态；cross_joint 使用不同极限组合')
                if flex is not None:row['wrist_flex_deg']=flex
                measurements.append(row)
    put(target/'measurement_manifest_TEMPLATE.json',dict(status='TEMPLATE_NO_MEASUREMENTS',limits_deg=limits,measurements=measurements))
    rows=load(origin/'harness/routing_plan.json')['rows'];cs=load(OUT/'channels.json');raw={'RP':12,'HS':13,'RU':14,'HE':16,'RF':17,'WF':18};mapping=[]
    for c in cs:
        if c['id']=='WD':continue
        r=next(x for x in rows if x['raw_index']==raw[c['id']]);mapping.append(dict(id=c['id'],axis=c['axis'],raw_index=r['raw_index'],bank='B',mux_channel=r['mux_channel'],connector=r['connector'],carrier_reference=r['carrier_reference'],pcb='PoseDoll_O22_MT6701CT 12 x 10 x 1 mm',magnet='D6 x 2.5 mm diametric',pins=['GND black','VCC red: O22 SENSOR_3V45','CLK blue','DO green','CSN yellow']))
    mapping.append(dict(id='WD',axis='l_wrist_deviation',connector='A01 / J10 + GPIO3 / J1 pin3',pcb='S1 TMAG5170A1 12 x 10 x 0.8 mm',pins={'S1.1 GND':'A01.1 GND black','S1.2 VCC':'A01.2 SENSOR_3V45 red','S1.3 SCK':'A01.3 CLK_A blue','S1.4 SDO':'A01.4 DO_A green','S1.5 CS_N':'XIAO D2 GPIO3 / J1.3 white; add 10k pull-up to MCU_3V3','S1.6 SDI':'A01.5 CS_A yellow'},magnet='O22 D6 x 2.5 mm diametric'))
    put(target/'pinmap.json',dict(channels=mapping,unused='B04/B08 empty. A01 is specially wired for TMAG: pin5=SDI, not CS. Never plug an MT sensor into this six-wire adapter.',board_ref_source_hashes=files,logic='CS_MCU is time-multiplexed as WD MOSI. Only SSI read transactions are disturbed; they are discarded. Restore high and wait 20 us before the next six SSI reads. EN remains high so A01 mux remains connected.',physical_bus_qualification=False))
    put(target/'calibration_TEMPLATE_UNMEASURED.json',dict(schema='R5_7_AXIS_CALIBRATION/1',status='EMPTY_NOT_A_CALIBRATION',channels={c['id']:dict(reference_raw_deg=None,reference_joint_deg=45 if c['id']=='HS' else 0,sign=None,direction_verified=False,range_verified=False,limits_deg=next(a['limits_deg'] for a in PROFILE['axes'] if a['id']==c['axis']),correction_lut=[]) for c in cs}))
    cal=load(target/'calibration_TEMPLATE_UNMEASURED.json');cal['channels']['WD']=dict(kind='TMAG_1D_VECTOR_LUT',limits_deg=[-20,30],direction_verified=False,range_verified=False,coupled_wrist_verified=False,forward_reverse_verified=False,max_residual_mT=None,lut=[]);put(target/'calibration_TEMPLATE_UNMEASURED.json',cal)
    put(target/'datasheet_requirements.json',dict(source='https://www.magntek.com.cn/upload/pdf/202407/MT6701_Rev.1.8.pdf',TMAG_source='https://www.ti.com/lit/ds/symlink/tmag5170.pdf',source_date='2026-10-30',pages=[3,9,25,26,33,34],magnet_mm=[6,2.5],magnetization='diametric, two poles',pcb_mm=[12,10,1],nominal_surface_air_gap_mm=2.0,permitted_surface_air_gap_mm=[.5,2],maximum_axis_offset_mm=.3,required_field_at_IC_surface_mT=[20,100],nominal_axis_offset_mm=0,physical_field_and_accuracy_verified=False,zero_rule='Any preload screw adjustment or magnetic reference removal invalidates six MT zeros. WD magnet follows the hand, not an adjustable screw.'))
    print('ELECTRONICS: 6 MT + 1 TMAG, R5AR 280-byte protocol; no hardware flashed',flush=True)

if __name__=='__main__':prepare()
