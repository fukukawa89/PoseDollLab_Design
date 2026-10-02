"""Re-layout proximal five-port and distal four-port boards using actual KiCad footprints.
Native unrouted studies, not released PCBs. Controller, port semantics and shared bus remain explicit.
"""
from pathlib import Path
import copy,sys,math,json,subprocess,xml.etree.ElementTree as ET
import pcbnew as pcb
from revo3_evidence import REPO,HW,run_paths,read,save,sha
sys.path.insert(0,str(HW/'tools'))
import build_regional_revM as legacy
CLI=Path('D:/ProgramFiles/KiCad/10.0/bin/kicad-cli.exe')
BQA='Package_DFN_QFN:DHWQFN-14-1EP_2.5x3mm_P0.5mm_EP1x1.5mm'
PINOUT={1:'GND',2:'LINK_SCK',3:'GND',4:'LINK_MOSI',5:'GND',6:'LINK_MISO',7:'CS6_REMOTE',8:'CS7_REMOTE',9:'GND',10:'CS8_REMOTE',11:'CS9_REMOTE',12:'GND',13:'+3V3',14:'+3V3'}
_original_symbol=legacy.custom_symbol
def custom_symbol(name):
    if name!='LVC125_BQA':return _original_symbol(name)
    raw=_original_symbol('LVC125_QUAD').replace('LVC125_QUAD','LVC125_BQA')
    pin='(pin power_in line (at 17.78 -10.16 180) (length 5.08) (name "EP_GND" '+legacy.effect()+') (number "15" '+legacy.effect()+'))'
    return raw[:-2]+pin+'))'
legacy.custom_symbol=custom_symbol

def part(ref,lib,sym,value,fp,nets,section='link'):
    return dict(ref=ref,lib=lib,sym=sym,value=value,fp=fp,nets={str(k):v for k,v in nets.items()},pcb=(100,100),angle=0,back=True,section=section)
def components(kind):
    legacy.comps=[];raw=copy.deepcopy(legacy.components());items=[]
    for c in raw:
        sec=c['section'];ref=c['ref']
        if sec=='usb' or ref in ('SW1','SW2','#FLG04'):continue
        port=int(sec[4:]) if sec.startswith('port') else None
        if kind=='proximal5' and port is not None and port>5:continue
        if kind=='distal4' and (port is None or port<6):continue
        if ref=='U1':
            for pin,net in list(c['nets'].items()):
                if net in ('USB_DM_IC','USB_DP_IC'):c['nets'][pin]=None
        c['pcb']=(100,100);c['angle']=0;c['back']=not(ref=='U1' or (ref.startswith('J') and ref!='JP1'))
        if ref=='JP1':c['fp']='Jumper:SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm'
        if ref=='J1':c['value']='5V protected N3/N4 branch; not 12V qualified'
        if port is not None and ref.startswith('U'):
            c.update(sym='LVC125_BQA',value='SN74LVC125ABQAR',fp=BQA);c['nets']['15']='GND'
        if kind=='distal4':
            replace={'SPI_SCK':'LINK_SCK','SPI_MOSI':'LINK_MOSI','SPI_MISO':'MISO_REMOTE_DRV',**{f'CS{i}_MCU':f'CS{i}_REMOTE' for i in range(6,10)}}
            c['nets']={k:replace.get(v,v) for k,v in c['nets'].items()}
        items.append(c)
    # The physical link is identical at both ends, including return conductors.
    link=part('J50','Connector_Generic','Conn_01x14','BM14B-SRSS-TB / SHR-14V-S / SSH-003T-P0.2-H','Connector_JST:JST_SH_BM14B-SRSS-TB_1x14-1MP_P1.00mm_Vertical',PINOUT)
    link['back']=False;items.append(link)
    def resistor(ref,value,a,b):items.append(part(ref,'Device','R',value,legacy.RFP,{1:a,2:b}))
    def capacitor(ref,value,a,b):items.append(part(ref,'Device','C',value,legacy.CFP,{1:a,2:b}))
    if kind=='proximal5':
        for i,net in enumerate(('EN','BOOT_N'),5):items.append(part('TP'+str(i),'Connector','TestPoint',net,'TestPoint:TestPoint_Pad_D1.0mm',{1:net},'control'))
        for ref,signals in [('U50',[('SPI_SCK','LINK_SCK'),('SPI_MOSI','LINK_MOSI'),('CS6_MCU','CS6_REMOTE'),('CS7_MCU','CS7_REMOTE')]),('U51',[('CS8_MCU','CS8_REMOTE'),('CS9_MCU','CS9_REMOTE'),(None,None),(None,None)])]:
            nets={7:'GND',14:'+3V3',15:'GND'}
            for g,(a,b) in enumerate(signals):
                oe,inp,out=[(1,2,3),(4,5,6),(10,9,8),(13,12,11)][g]
                nets[oe]='GND' if a else '+3V3';nets[inp]=a or 'GND';nets[out]=b+'_DRV' if b else None
                if b:resistor(f'R{500+(0 if ref=="U50" else 10)+g}','100R source damping candidate',b+'_DRV',b)
            items.append(part(ref,'PoseDoll','LVC125_BQA','SN74LVC125ABQAR',BQA,nets))
            capacitor('C'+ref[1:],'100n X7R','+3V3','GND')
        for i in range(6,10):resistor('R'+str(520+i),'10k','+3V3',f'CS{i}_MCU')
        # MISO is a shared tri-state return. Do not insert an always-enabled
        # return buffer that would fight proximal ports while distal CS is high.
        resistor('R530','0R option / direct tri-state return','LINK_MISO','SPI_MISO')
    else:
        resistor('R500','100R return source damping candidate','MISO_REMOTE_DRV','LINK_MISO')
        capacitor('C50','1u X7R','+3V3','GND')
        for i,net in enumerate(('+3V3','GND'),1):items.append(part('#FLG0'+str(i),'power','PWR_FLAG','PWR_FLAG','',{1:net},'power'))
    return items

def rect(f):
    bb=[g.GetBoundingBox() for g in f.GraphicalItems() if g.GetLayer() in (pcb.F_CrtYd,pcb.B_CrtYd)]
    if not bb:bb=[f.GetBoundingBox(False,False)]
    return [pcb.ToMM(min(b.GetLeft() for b in bb)),pcb.ToMM(min(b.GetTop() for b in bb)),pcb.ToMM(max(b.GetRight() for b in bb)),pcb.ToMM(max(b.GetBottom() for b in bb))]
def overlap(a,b):return min(a[2],b[2])-max(a[0],b[0])>1e-7 and min(a[3],b[3])-max(a[1],b[1])>1e-7
def carve(free,used):
    result=[]
    for a in free:
        if not overlap(a,used):result.append(a);continue
        if used[0]>a[0]:result.append([a[0],a[1],used[0],a[3]])
        if used[2]<a[2]:result.append([used[2],a[1],a[2],a[3]])
        if used[1]>a[1]:result.append([a[0],a[1],a[2],used[1]])
        if used[3]<a[3]:result.append([a[0],used[3],a[2],a[3]])
    result=[a for a in result if a[2]-a[0]>.2 and a[3]-a[1]>.2]
    return [a for i,a in enumerate(result) if not any(i!=j and all([b[0]<=a[0],b[1]<=a[1],b[2]>=a[2],b[3]>=a[3]]) and (b!=a or j<i) for j,b in enumerate(result))]
def move_corner(f,x,y,rotate=0):
    f.SetOrientationDegrees(rotate);b=rect(f)
    f.SetPosition(f.GetPosition()+pcb.VECTOR2I(pcb.FromMM(x-b[0]),pcb.FromMM(y-b[1])))
    return rect(f)
def place(board,width,height,kind):
    free={False:[[.55,.55,width-.55,height-.55]],True:[[.55,.55,width-.55,height-.55]]}
    fps={f.GetReference():f for f in board.GetFootprints()};used=[];unplaced=[]
    def occupy(f,b):
        back=f.GetLayer()==pcb.B_Cu
        free[back]=carve(free[back],[b[0]-.15,b[1]-.15,b[2]+.15,b[3]+.15]);used.append((f.GetReference(),back,b))
    if 'U1' in fps:
        f=fps.pop('U1');f.SetOrientationDegrees(0);f.SetPosition(pcb.VECTOR2I(pcb.FromMM(width/2),pcb.FromMM(6.8)))
        # The library courtyard includes 15 mm of antenna air keepout.
        # Place the antenna beyond the board edge; preserve its complete polygon.
        # Only the supported body portion occupies the board surface.
        occupy(f,[width/2-9.775,0,width/2+9.775,20.275])
        thermal=[p for p in f.Pads() if p.GetNumber()=='41' and p.GetDrillSize().x>0]
        for p in thermal:
            p.SetDrillSize(pcb.VECTOR2I(pcb.FromMM(.3),pcb.FromMM(.3)));p.SetSize(pcb.VECTOR2I(pcb.FromMM(.65),pcb.FromMM(.65)))
            x,y=pcb.ToMM(p.GetPosition().x),pcb.ToMM(p.GetPosition().y)
            free[True]=carve(free[True],[x-.65,y-.65,x+.65,y+.65])
        # Overhanging module outline belongs to fabrication, not printed board silkscreen.
        for g in list(f.GraphicalItems()):
            if g.GetLayer()==pcb.F_SilkS and g.GetBoundingBox().GetTop()<0:g.SetLayer(pcb.F_Fab)
    f=fps.pop('J50');b=rect(f);w,h=b[2]-b[0],b[3]-b[1]
    occupy(f,move_corner(f,(width-w)/2,height-.55-h))
    for f in sorted(fps.values(),key=lambda f:(-(rect(f)[2]-rect(f)[0])*(rect(f)[3]-rect(f)[1]),f.GetReference())):
        b=rect(f);w,h=b[2]-b[0],b[3]-b[1];back=f.GetLayer()==pcb.B_Cu;options=[]
        for a in free[back]:
            for angle,ww,hh in [(0,w,h),(90,h,w)]:
                if ww<=a[2]-a[0] and hh<=a[3]-a[1]:options.append((min(a[2]-a[0]-ww,a[3]-a[1]-hh),a[1],a[0],angle))
        if not options:unplaced.append(f.GetReference());continue
        _,y,x,angle=min(options);occupy(f,move_corner(f,x,y,angle))
    collisions=[{'a':a[0],'b':b[0]} for i,a in enumerate(used) for b in used[i+1:] if a[1]==b[1] and overlap(a[2],b[2])]
    return used,unplaced,collisions

def main():
    verify,out=run_paths();reports=[];library_hashes={};version=subprocess.check_output([str(CLI),'version']).decode().strip()
    for kind,dims in [('proximal5',(36,48)),('distal4',(26,30)),('distal4_narrow',(20,36)),('proximal5_side',(36,48)),('distal4_side',(26,30))]:
        directory=out/'electronics'/kind;directory.mkdir(parents=True,exist_ok=True)
        name='PoseDoll_RevO3_'+kind;legacy.OUT=directory;legacy.NAME=name;legacy.comps=components('proximal5' if kind.startswith('proximal5') else 'distal4')
        if kind.endswith('_side'):
            for component in legacy.comps:
                if component['ref']=='J50':component['fp']='Connector_JST:JST_SH_SM14B-SRSS-TB_1x14-1MP_P1.00mm_Horizontal';component['value']='SM14B-SRSS-TB / SHR-14V-S / SSH-003T-P0.2-H'
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
        lib=directory/'RevO3.pretty';lib.mkdir(exist_ok=True)
        for f in b.GetFootprints():
            if f.GetReference()=='U1':
                f.SetFPID(pcb.LIB_ID('RevO3','ESP32-S3-WROOM-1_thermal030'));pcb.PCB_IO_MGR.FindPlugin(pcb.PCB_IO_MGR.KICAD_SEXP).FootprintSave(str(lib),f)
            f.Reference().SetVisible(False)
            for model in f.Models():
                if model.m_Filename.endswith('/Texas_DSG0008A_WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm.step'):
                    model.m_Filename=model.m_Filename.replace('Texas_DSG0008A_','')
                candidate=Path(model.m_Filename.replace('${KICAD10_3DMODEL_DIR}','D:/ProgramFiles/KiCad/10.0/share/kicad/3dmodels'))
                if candidate.suffix=='.wrl' and candidate.with_suffix('.step').exists():candidate=candidate.with_suffix('.step')
                if candidate.is_file():library_hashes[str(candidate)]=sha(candidate)
        (directory/'fp-lib-table').write_text('(fp_lib_table (lib (name RevO3) (type KiCad) (uri ${KIPRJMOD}/RevO3.pretty) (options "") (descr "0.3 mm drill / 0.65 mm pad thermal candidate; qualification pending")))',encoding='utf-8')
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
        layout={'schema':'revo3-pcb-v1','kind':kind,'board_mm':[*dims,pcb.ToMM(b.GetDesignSettings().GetBoardThickness())],'thermal_via_design':{'drill_mm':.3,'pad_mm':.65,'pitch_mm':.7,'annular_ring_mm':.175,'rule_relaxation':False,'supplier_thermal_solder_wicking_and_filling_qualification':'NOT_RUN'} if kind.startswith('proximal5') else None,'components':parts,'placement_source':'Entirely new deterministic courtyard packing, original XY coordinates discarded','unplaced':unplaced,'courtyard_collisions':collisions,'placement_status':'PASS_XY_ONLY' if not unplaced and not collisions else 'FAIL','link_pinout':PINOUT,'logical_nodes':['N3','N4'],'sensor_ports':[1,2,3,4,5] if kind.startswith('proximal5') else [6,7,8,9],'checks':checks,'step_export':{'exit_code':stepresult.returncode,'file':name+'.step','log':'step_export.log','missing_models_must_be_checked':True},'routing':'NOT_RUN_PENDING_ENCLOSURE_AND_HARNESS','poweroff_signal_state':'NOT_QUALIFIED_LVC125_NO_IOFF_GUARANTEE_IN_REVIEWED_DATASHEET','mating_plug_source':'JST SH dimensioned drawing; separate mating geometry follows, not inferred from courtyard','antenna':{'module_overhang_mm':6.0,'keepout_beyond_top_mm':20.95,'keepout_width_mm':48.05,'body_placement':'Antenna over PCB top edge; complete library keepout retained; chest metal exclusion and RF qualification pending'} if kind.startswith('proximal5') else None,'firmware_GPIO_changed':False,'physical_tested':False,'manufacturing_released':False}
        save(directory/'layout.json',layout);reports.append(layout);print(kind,layout['placement_status'],'unplaced',unplaced,checks,flush=True)
    for filename,digest in library_hashes.items():
        if not Path(filename).is_file() or sha(filename)!=digest:raise RuntimeError('KiCad source library changed during producer: '+filename)
    network=read(HW/'mechanical_manifest/network_revO.json');partition=[]
    for n in network['nodes']:
        partition.append({'node':n['id'],'ports':n['ports'],'pcb_types':['proximal5','distal4'] if len(n['ports'])==9 else ['legacy_candidate_'+str(len(n['ports']))],'full_node_qualified':False})
    save(verify/'electronics.json',{'schema':'revo3-electronics-v1','boards':reports,'expected_new_board_types':['proximal5','distal4','distal4_narrow','proximal5_side','distal4_side'],'distal_options_are_alternatives_not_extra_nodes':True,'logical_node_mapping':partition,'physical_acquisition_pcb_count':8,'CAN_physical_nodes':7,'measured_axes':41,'library_input_sha256':library_hashes,'toolchain':{'version':version,'kicad_cli_sha256':sha(CLI),'pcbnew_version':pcb.Version()},'status':'PLACEMENT_STUDY_NOT_ROUTED','physical_tested':False})
if __name__=='__main__':main()
