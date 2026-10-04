"""O4 A/C native placement experiment. Routing, waveform and supply tests are not simulated passes."""
from build_revo3_electronics import *
import build_revo3_electronics as o3
from revo4_evidence import run_paths,save,read,sha
PINOUT={1:'+3V3_REMOTE',2:'GND',3:'RS485_A',4:'RS485_B'}
MCU_PINS={1:None,2:'+3V3',3:'GND',4:'NRST',5:'RS485_DE',6:'CS6_REMOTE',7:'REMOTE_TX',8:'REMOTE_RX',9:'CS7_REMOTE',10:'LINK_SCK',11:'MISO_REMOTE_DRV',12:'LINK_MOSI',13:'CS8_REMOTE',14:None,15:None,16:'SWDIO',17:'SWCLK',18:'CS9_REMOTE',19:None,20:None}
BASE_CUSTOM=legacy.custom_symbol

def custom_symbol(name):
    if name!='TPS2553_DBV':return BASE_CUSTOM(name)
    defs=[(1,'IN','power_in'),(2,'GND','power_in'),(3,'EN','input'),(4,'FAULT_N','open_collector'),(5,'ILIM','passive'),(6,'OUT','power_out')]
    body=[]
    for j,(n,label,typ) in enumerate(defs):
        side=-1 if j<3 else 1;y=2.54-2.54*(j%3);angle=0 if side==-1 else 180
        body.append(f'(pin {typ} line (at {side*17.78} {y} {angle}) (length 5.08) (name "{label}" '+legacy.effect()+f') (number "{n}" '+legacy.effect()+'))')
    return '(symbol "TPS2553_DBV" (pin_names (offset 0.5)) (in_bom yes) (on_board yes) (property "Reference" "U" (at 0 10 0) '+legacy.effect()+') (property "Value" "TPS2553_DBV" (at 0 13 0) '+legacy.effect()+') (symbol "TPS2553_DBV_0_1" (rectangle (start -12.7 6) (end 12.7 -6) (stroke (width 0.254) (type default)) (fill (type background)))) (symbol "TPS2553_DBV_1_1" '+''.join(body)+'))'
legacy.custom_symbol=custom_symbol

def components(kind):
    proximal=kind.startswith('proximal');items=o3.components('proximal5' if proximal else 'distal4')
    # Keep the four per-sensor buffers until physical poweroff/SPI tests justify deleting them.
    remove={'J50','U50','U51','C50','C51','R530'}|{f'R{i}' for i in range(500,530)}
    items=[c for c in items if c['ref'] not in remove]
    def add(ref,lib,sym,value,fp,nets,back=True):
        c=part(ref,lib,sym,value,fp,nets);c['back']=back;items.append(c)
    def r(ref,value,a,b):add(ref,'Device','R',value,legacy.RFP,{1:a,2:b})
    def c(ref,value,a,b):add(ref,'Device','C',value,legacy.CFP,{1:a,2:b})
    # Four-wire runtime connection is identical at each end; satellites do not add CAN IDs.
    pins=PINOUT if proximal else {1:'+3V3',2:'GND',3:'RS485_A',4:'RS485_B'}
    add('J50','Connector_Generic','Conn_01x04','SM04B-SRSS-TB / SHR-04V-S / SSH-003T-P0.2-H','Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal',pins,False)
    add('U61','Interface_UART','THVD1400D','THVD1400DRLR','Package_TO_SOT_SMD:SOT-583-8',{1:'REMOTE_RX',2:'RS485_DE',3:'RS485_DE',4:'REMOTE_TX',5:'GND',6:'RS485_A',7:'RS485_B',8:'+3V3'})
    r('R610','10k reset DE=0','RS485_DE','GND');c('C610','100n X7R','+3V3','GND')
    # Optional split termination: DNP until line waveform/edge tests decide end population.
    r('R611','60R DNP termination option','RS485_A','TERM_MID');r('R612','60R DNP termination option','TERM_MID','RS485_B');c('C611','4.7n DNP','TERM_MID','GND')
    add('D60','PoseDoll','PESD5V0S2BT','PESD5V0S2BT provisional clamp; common-mode/TVS coordination NOT QUALIFIED','Package_TO_SOT_SMD:SOT-23',{1:'RS485_A',2:'RS485_B',3:'GND'})
    if proximal:
        m=next(c for c in items if c['ref']=='U1')
        # Former CS6/7/8/9 GPIO8/9/10/14 via ESP32 GPIO matrix. Five local ports unchanged.
        m['nets'].update({'12':'REMOTE_TX','17':'REMOTE_RX','18':'RS485_DE','22':'REMOTE_PWR_EN','8':'REMOTE_PWR_FAULT'})
        add('U62','PoseDoll','TPS2553_DBV','TPS2553DBVR','Package_TO_SOT_SMD:SOT-23-6',{1:'+3V3',2:'GND',3:'REMOTE_PWR_EN',4:'REMOTE_PWR_FAULT',5:'ILIM',6:'+3V3_REMOTE'})
        r('R620','100k 1% current-limit candidate','ILIM','GND');r('R621','100k default disabled','REMOTE_PWR_EN','GND');r('R622','10k','REMOTE_PWR_FAULT','+3V3')
        c('C620','100n X7R','+3V3','GND');c('C621','10u X7R footprint; derating pending','+3V3_REMOTE','GND')
    else:
        add('U60','MCU_ST_STM32C0','STM32C011F6Ux','STM32C011F6U6','Package_DFN_QFN:ST_UFQFPN-20_3x3mm_P0.5mm',MCU_PINS)
        c('C600','100n X7R','+3V3','GND');c('C601','4.7u X7R','+3V3','GND');c('C602','100n reset','NRST','GND');r('R600','10k','NRST','+3V3')
        for i in range(6,10):r(f'R60{i}','10k CS safe high',f'CS{i}_REMOTE','+3V3')
        for i,net in enumerate(('SWDIO','SWCLK','NRST','+3V3','GND'),60):add('TP'+str(i),'Connector','TestPoint',net,'TestPoint:TestPoint_Pad_D1.0mm',{1:net})
    if kind.endswith('_top'):
        j=next(c for c in items if c['ref']=='J50')
        j['value']='BM04B-SRSS-TB / SHR-04V-S / SSH-003T-P0.2-H'
        j['fp']='Connector_JST:JST_SH_BM04B-SRSS-TB_1x04-1MP_P1.00mm_Vertical'
    return items

def main():
    verify,out=run_paths();reports=[];library_hashes={}
    from revo3_evidence import verify_artifacts
    import shutil
    origin=HW/'verification/revO3/runs/o3_20260924_r3/electronics_execution.json'
    source_record=read(origin)['artifacts'];verify_artifacts(source_record,'o3_20260924_r3')
    for oldkind,kind in [('proximal5','A_proximal5'),('distal4','A_distal4')]:
        source=HW/'generated/revO3/runs/o3_20260924_r3/electronics'/oldkind;dest=out/'electronics'/kind
        shutil.copytree(source,dest);layout=read(dest/'layout.json');layout['kind']=kind;layout['origin_artifact_set']=source_record;layout['origin_layout_sha256']=sha(source/'layout.json');layout['run_id']=run_paths()[0].name
        save(dest/'layout.json',layout);reports.append(layout)
    verify_artifacts(source_record,'o3_20260924_r3')
    version=subprocess.check_output([str(CLI),'version']).decode().strip()
    for kind,dims in [('proximal5_rs485',(36,48)),('distal4_rs485',(26,30)),('distal4_rs485_stretch',(20,30)),('distal4_rs485_top',(20,30))]:
        directory=out/'electronics'/kind;directory.mkdir(parents=True,exist_ok=True)
        name='PoseDoll_RevO4_'+kind;legacy.OUT=directory;legacy.NAME=name;legacy.comps=components(kind)
        for component in legacy.comps:
            if component['fp']:
                libname,item=component['fp'].split(':',1);inputfile=Path('D:/ProgramFiles/KiCad/10.0/share/kicad/footprints')/(libname+'.pretty')/(item+'.kicad_mod')
                if inputfile.is_file():library_hashes[str(inputfile)]=sha(inputfile)
            symbolfile=Path('D:/ProgramFiles/KiCad/10.0/share/kicad/symbols')/(component['lib']+'.kicad_sym')
            if symbolfile.is_file():library_hashes[str(symbolfile)]=sha(symbolfile)
        rid=legacy.schematic();legacy.board(rid)
        b=pcb.LoadBoard(str(directory/'placement.kicad_pcb'));b.GetDesignSettings().SetBoardThickness(pcb.FromMM(1.2));used,unplaced,collisions=place(b,*dims,kind)
        for d in list(b.GetDrawings()):
            if d.GetLayer()==pcb.Edge_Cuts:b.Remove(d)
        corners=[(0,0),(dims[0],0),dims,(0,dims[1])]
        for a,z in zip(corners,corners[1:]+corners[:1]):
            q=pcb.PCB_SHAPE();q.SetShape(pcb.SHAPE_T_SEGMENT);q.SetStart(pcb.VECTOR2I(*[pcb.FromMM(v) for v in a]));q.SetEnd(pcb.VECTOR2I(*[pcb.FromMM(v) for v in z]));q.SetLayer(pcb.Edge_Cuts);q.SetWidth(pcb.FromMM(.05));b.Add(q)
        # Store the changed module as an explicit local library variant.
        lib=directory/'RevO4.pretty';lib.mkdir(exist_ok=True)
        for f in b.GetFootprints():
            if f.GetReference()=='U1':
                f.SetFPID(pcb.LIB_ID('RevO4','ESP32-S3-WROOM-1_thermal030'));pcb.PCB_IO_MGR.FindPlugin(pcb.PCB_IO_MGR.KICAD_SEXP).FootprintSave(str(lib),f)
            f.Reference().SetVisible(False)
            for model in f.Models():
                if model.m_Filename.endswith('/Texas_DSG0008A_WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm.step'):
                    model.m_Filename=model.m_Filename.replace('Texas_DSG0008A_','')
                candidate=Path(model.m_Filename.replace('${KICAD10_3DMODEL_DIR}','D:/ProgramFiles/KiCad/10.0/share/kicad/3dmodels'))
                if candidate.suffix=='.wrl' and candidate.with_suffix('.step').exists():candidate=candidate.with_suffix('.step')
                if candidate.is_file():library_hashes[str(candidate)]=sha(candidate)
        (directory/'fp-lib-table').write_text('(fp_lib_table (lib (name RevO4) (type KiCad) (uri ${KIPRJMOD}/RevO4.pretty) (options "") (descr "0.3 mm drill / 0.65 mm pad thermal candidate; qualification pending")))',encoding='utf-8')
        target=directory/(name+'.kicad_pcb');pcb.SaveBoard(str(target),b)
        stepcmd=[str(CLI),'pcb','export','step','--subst-models','-o',str(directory/(name+'.step')),str(target)]
        stepresult=subprocess.run(stepcmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(directory/'step_export.log').write_bytes(stepresult.stdout)
        parts=[]
        for f in b.GetFootprints():
            parts.append({'ref':f.GetReference(),'value':f.GetValue(),'footprint':str(f.GetFPID().GetLibNickname())+':'+str(f.GetFPID().GetLibItemName()),'courtyard_xy_mm':rect(f),'center_xy_mm':[pcb.ToMM(f.GetPosition().x),pcb.ToMM(f.GetPosition().y)],'rotation_deg':f.GetOrientationDegrees(),'component_frame_datum':'KiCad footprint origin; not courtyard centroid','fab_lines_xy_mm':[[[pcb.ToMM(g.GetStart().x),pcb.ToMM(g.GetStart().y)],[pcb.ToMM(g.GetEnd().x),pcb.ToMM(g.GetEnd().y)]] for g in f.GraphicalItems() if g.GetLayer() in (pcb.F_Fab,pcb.B_Fab) and hasattr(g,"GetShape") and g.GetShape()==pcb.SHAPE_T_SEGMENT],'back':f.GetLayer()==pcb.B_Cu,'pads':[{'pin':p.GetNumber(),'net':p.GetNetname(),'x_mm':pcb.ToMM(p.GetPosition().x),'y_mm':pcb.ToMM(p.GetPosition().y)} for p in f.Pads()]})
        checks={}
        for what,args in [('erc',['sch','erc']),('drc',['pcb','drc'])]:
            source=directory/(name+('.kicad_sch' if what=='erc' else '.kicad_pcb'))
            command=[str(CLI),*args,'--format','json','--severity-all','-o',str(directory/(what+'.json')),str(source)]
            proc=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(directory/(what+'.log')).write_bytes(proc.stdout)
            data=read(directory/(what+'.json')) if (directory/(what+'.json')).exists() else None
            violations=[] if data is None else data.get('violations',[])+[v for s in data.get('sheets',[]) for v in s.get('violations',[])]
            counts={level:sum(v.get('severity')==level for v in violations) for level in ('error','warning')}
            checks[what]={'command':command,'exit_code':proc.returncode,'status':'PASS' if data is not None and proc.returncode==0 and not violations and not data.get('unconnected_items',[]) else 'FAIL','severity_counts':counts,'unconnected_items':0 if data is None else len(data.get('unconnected_items',[])),'violations_by_type':{typ:sum(v.get('type')==typ for v in violations) for typ in sorted(set(v.get('type','unknown') for v in violations))}}
        layout={'schema':'revo4-pcb-v1','kind':kind,'board_mm':[*dims,pcb.ToMM(b.GetDesignSettings().GetBoardThickness())],'thermal_via_design':{'drill_mm':.3,'pad_mm':.65,'pitch_mm':.7,'annular_ring_mm':.175,'rule_relaxation':False,'supplier_thermal_solder_wicking_and_filling_qualification':'NOT_RUN'} if kind.startswith('proximal5') else None,'components':parts,'placement_source':'Entirely new deterministic courtyard packing, original XY coordinates discarded','unplaced':unplaced,'courtyard_collisions':collisions,'placement_status':'PASS_XY_ONLY' if not unplaced and not collisions else 'FAIL','link_pinout':PINOUT,'logical_nodes':['N3','N4'],'sensor_ports':[1,2,3,4,5] if kind.startswith('proximal5') else [6,7,8,9],'checks':checks,'step_export':{'exit_code':stepresult.returncode,'file':name+'.step','log':'step_export.log','missing_models_must_be_checked':True},'routing':'NOT_RUN_PENDING_ENCLOSURE_AND_HARNESS','poweroff_signal_state':'NOT_QUALIFIED_LVC125_NO_IOFF_GUARANTEE_IN_REVIEWED_DATASHEET','mating_plug_source':'JST SH dimensioned drawing; separate mating geometry follows, not inferred from courtyard','antenna':{'module_overhang_mm':6.0,'keepout_beyond_top_mm':20.95,'keepout_width_mm':48.05,'body_placement':'Antenna over PCB top edge; complete library keepout retained; chest metal exclusion and RF qualification pending'} if kind.startswith('proximal5') else None,'firmware_GPIO_changed':True,'new_driver_status':'NOT_IMPLEMENTED_OR_FLASHED','MCU_pinmap':MCU_PINS if kind.startswith('distal') else {'GPIO8':'UART_TX','GPIO9':'UART_RX','GPIO10':'DE','GPIO14':'REMOTE_PWR_EN','GPIO15':'REMOTE_PWR_FAULT'},'protection_status':'COMPONENT_CANDIDATE_NOT_BOARD_QUALIFIED','physical_tested':False,'manufacturing_released':False}
        save(directory/'layout.json',layout);reports.append(layout);print(kind,layout['placement_status'],'unplaced',unplaced,checks,flush=True)
    for filename,digest in library_hashes.items():
        if not Path(filename).is_file() or sha(filename)!=digest:raise RuntimeError('KiCad source library changed during producer: '+filename)
    network=read(HW/'mechanical_manifest/network_revO.json');partition=[]
    for n in network['nodes']:
        partition.append({'node':n['id'],'ports':n['ports'],'pcb_types':['proximal5_rs485','distal4_rs485'] if len(n['ports'])==9 else ['legacy_candidate_'+str(len(n['ports']))],'full_node_qualified':False})
    save(verify/'electronics.json',{'schema':'revo4-electronics-v1','boards':reports,'expected_new_board_types':['proximal5_rs485','distal4_rs485','distal4_rs485_stretch','distal4_rs485_top'],'distal_options_are_alternatives_not_extra_nodes':True,'logical_node_mapping':partition,'physical_acquisition_pcb_count':8,'processor_count':9,'fixed_CAN_node_count':7,'J50_conductors':4,'all_other_sensor_wires_retained':True,'CAN_physical_nodes':7,'measured_axes':41,'library_input_sha256':library_hashes,'toolchain':{'version':version,'kicad_cli_sha256':sha(CLI),'pcbnew_version':pcb.Version()},'status':'PLACEMENT_STUDY_NOT_ROUTED','physical_tested':False})
if __name__=='__main__':main()
