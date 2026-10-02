"""Build the O22 plate-aware assembly guide from released mechanical/electrical inputs.
Run from any directory using the repository Python environment. No CAD is modified.
"""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib, html, json, re, zipfile
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
H=ROOT/'Hardware/PoseDoll44';B=H/'bench/revO22';OUT=H/'tutorials/assembly-o22'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
E=html.escape
PM=read(B/'a1mini/manifest.json');META=read(B/'mechanical/assembly_metadata.json')['meta']
PROFILE=read(B/'profiles/device_profile.json');ROUTING=read(B/'harness/routing_plan.json')
PROC=read(B/'procurement.json')['characters'][0]['rows'];BOM=read(B/'manufacturing/electronic_bom.json')
STOCK={r['sku']:r for r in PROC if r['category']=='金属/磁铁标准件'}
PARTS={i['part']:{**i,'plate':p['id'],'address':f"{p['id']}-{i['number']:02}",'optional':p['optional']} for p in PM['plates'] for i in p['items']}
FRAMES={f['body']:f['replaces'] for f in read(H/'generated/revO15/runs/o15_20260929_r1/carriers_refined/quinn_routing.json')['frames']}
ORDER=['waist','chest','head']+[j for s in ('l','r') for j in (f'clavicle_{s}.protract',f'clavicle_{s}.elevate',f'upperarm_{s}',f'elbow_{s}.flex',f'forearm_{s}.twist',f'hand_{s}.flex',f'hand_{s}.deviate')]+[j for s in ('l','r') for j in (f'thigh_{s}',f'calf_{s}.flex',f'foot_{s}',f'ball_{s}.flex')]
TERMS=[('clavicle_l.protract_frame','左锁骨前后中间架'),('clavicle_r.protract_frame','右锁骨前后中间架'),('hand_l.flex_frame','左腕屈伸中间架'),('hand_r.flex_frame','右腕屈伸中间架'),('sensor_cassette','传感板托夹'),('magnet_cartridge','侧装磁铁座盖'),('clavicle_l.protract','左锁骨前后'),('clavicle_r.protract','右锁骨前后'),('clavicle_l.elevate','左锁骨升降'),('clavicle_r.elevate','右锁骨升降'),('upperarm_l','左肩／上臂'),('upperarm_r','右肩／上臂'),('forearm_l','左前臂'),('forearm_r','右前臂'),('elbow_l','左肘'),('elbow_r','右肘'),('hand_l','左手腕'),('hand_r','右手腕'),('thigh_l','左髋／大腿'),('thigh_r','右髋／大腿'),('calf_l','左膝／小腿'),('calf_r','右膝／小腿'),('foot_l','左踝／脚掌'),('foot_r','右踝／脚掌'),('ball_l','左脚趾'),('ball_r','右脚趾'),('clavicle_l','左锁骨'),('clavicle_r','右锁骨'),('controller_lid','背盒盖'),('xiao_spacing_gauge','XIAO 焊接间距量规'),('head','头颈'),('chest','胸部'),('waist','腰部'),('pelvis','骨盆'),('pcb_clip','板夹'),('magnet_cap','磁铁端盖'),('case_minus','固定半壳'),('case_plus','活动半壳'),('radial_pad','径向摩擦块'),('base_sensor_half','固定侧关节座'),('lever_cup','旋转侧叉耳'),('C14','下环'),('C15','上环盖'),('C01','下叉'),('C02','上叉'),('frame/','骨架／'),('fixture/','工具／'),('.protract_frame','前后中间架'),('.flex_frame','屈伸中间架'),('.flex','屈伸'),('.deviate','侧摆'),('.twist','扭转')]
def zh(s):
    for a,b in TERMS:s=s.replace(a,b)
    return s

def part(k):
    i=PARTS[k];return f"盘 {i['address']} · {i['id']}（{zh(k)}）"

def resolve(k):
    if k in PARTS:return k
    for body,replaces in FRAMES.items():
        if k in replaces:return 'frame/'+body
    raise ValueError(('Missing integrated part',k))

def role(k):
    if k.startswith('frame/'):
        return '一体骨架；已包含 '+ '、'.join(zh(x) for x in FRAMES[k[6:]])
    if k.endswith('sensor_cassette'):return '固定传感 PCB；先滑入板，再装到关节'
    if k.endswith('magnet_cartridge'):return '侧面装入并粘固磁铁；旋转侧用 2 枚 M2×5 固定'
    if '_pcb_clip_' in k:return '端轴传感 PCB 的一侧板夹，与另一板夹成对使用'
    if k.endswith('radial_pad'):return '端轴径向摩擦块；凹面朝轴，M3×8 顶压外侧'
    if k.endswith('magnet_cap'):return '端轴磁铁端盖；2 枚 M2×4 固定'
    if k.endswith('case_plus'):return '端轴可拆半壳；4 枚 M2×20 合壳'
    if k.endswith('/C14'):return '十字关节下环；先装内部螺母和 M3 反力垫'
    if k.endswith('/C15'):return '十字关节上环盖；4 枚 M1.6×6 合环'
    if k.endswith(('/C01','/C02')):return '十字关节叉臂；与另一叉臂正交穿装'
    if k=='o22/controller_lid':return '完成接线和功能检查后盖背盒；用扎带固定'
    return 'XIAO 焊接定位工具，焊完取出，不装在人偶内'

STEPS=[];FIRST={}
for n,jid in enumerate(ORDER,1):
    j=next(j for j in PROFILE['joints'] if j['id']==jid)
    keys=sorted([k for k in PARTS if META.get(k,{}).get('module')==jid],key=lambda k:PARTS[k]['address'])
    keys=['frame/'+j['parent'],'frame/'+j['child']]+keys
    keys=list(dict.fromkeys(keys));fresh=[]
    for k in keys:
        if k not in FIRST:FIRST[k]=f'S{n:02}';fresh.append(k)
    metal=Counter(v['sku'] for k,v in META.items() if v.get('module')==jid and v.get('sku') in STOCK)
    STEPS.append({**j,'step':f'S{n:02}','title':zh(jid),'parts':keys,'new_parts':fresh,'plates':sorted({PARTS[k]['plate'] for k in keys}),'stock':dict(metal),'objects':[k for k,v in META.items() if v.get('module')==jid]+keys})
for k in ('fixture/xiao_spacing_gauge','o22/controller_lid'):FIRST[k]='S26'
STEPS.append({'step':'S26','id':'controller','title':'中央板、XIAO 与背盒','kind':'controller','parts':['frame/chest','o22/controller_lid','fixture/xiao_spacing_gauge'],'new_parts':['o22/controller_lid','fixture/xiao_spacing_gauge'],'plates':['A01','A02','A03'],'stock':{'SELF_TAP_M2_L6':4},'objects':['frame/chest']+[k for k in META if k.startswith('o22/')]})
ROUTES=[]
for r in ROUTING['rows']:
    k=r['sensor_part_O20'];stem=k.removesuffix('sensor_PCB');jid=k.split('/')[0]
    if stem.endswith(('P_','D_')):
        mounts=[stem+'pcb_clip_-14',stem+'pcb_clip_+14'];mag=stem+'magnet_cap'
    else:mounts=[stem+'sensor_cassette'];mag=stem+'magnet_cartridge'
    assert all(x in PARTS for x in mounts+[mag]),(k,mounts,mag)
    ROUTES.append({**r,'module':jid,'mounts':mounts,'magnet_mount':mag,'step':next(s['step'] for s in STEPS if s['id']==jid)})

# Cross-check final native KiCad pin exports, never the older placement JSON.
NATIVE={b:read(OUT/f'evidence/{b}_native_pads.json') for b in ('carrier','sensor')}
for b,d in NATIVE.items():assert sha(ROOT/d['source'])==d['sha256']
COMP={b:{c['ref']:c for c in d['components']} for b,d in NATIVE.items()}
for r in ROUTES:
    c=COMP['carrier'][r['carrier_reference']];pins={p['pin']:p['net'] for p in c['pads']}
    bank=r['connector'][0]
    assert c['value'].startswith(r['connector']+' ')
    assert [pins[str(i)] for i in range(1,6)]==['GND','SENSOR_3V45','CLK_'+bank,r['connector']+'_DO','CS_'+bank]
assert [p['net'] for p in COMP['sensor']['J1']['pads']]==['GND','+3V3','CLK','DO','CS_N']
assert {p['pin']:p['net'] for p in COMP['carrier']['J3']['pads'] if p['pin'] in ('1','2')}=={'1':'EXT5V','2':'GND'}
assert sum((Counter(s['stock']) for s in STEPS),Counter())==Counter({k:r['net_quantity'] for k,r in STOCK.items()})
assert set(FIRST)=={k for k,i in PARTS.items() if not i['optional']}
assert len(FIRST)==186 and len(ROUTES)==46

# A tiny dual writer keeps printable HTML and Markdown exactly in agreement.
def inline(s):
    s=E(str(s))
    s=re.sub(r'`([^`]+)`',r'<code>\1</code>',s)
    s=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',s)
    s=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'<a href="\2">\1</a>',s)
    return s
class Doc:
    def __init__(self):self.h=[];self.m=[]
    def heading(self,level,title,anchor):
        self.h.append(f'<h{level} id="{anchor}">{E(title)}</h{level}>');self.m.append(f'<a id="{anchor}"></a>\n\n'+ '#'*level+' '+title+'\n')
    def p(self,s,cls=''):self.h.append(f'<p class="{cls}">{inline(s)}</p>');self.m.append(s+'\n')
    def listing(self,rows,ordered=False):
        tag='ol' if ordered else 'ul';self.h.append('<'+tag+'>'+''.join('<li>'+inline(s)+'</li>' for s in rows)+'</'+tag+'>');self.m.append('\n'.join((f'{i}. ' if ordered else '- ')+s for i,s in enumerate(rows,1))+'\n')
    def table(self,heads,rows):
        self.h.append('<div class="table-wrap"><table><thead><tr>'+''.join('<th>'+inline(v)+'</th>' for v in heads)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+inline(v)+'</td>' for v in row)+'</tr>' for row in rows)+'</tbody></table></div>')
        self.m.append('| '+' | '.join(heads)+' |\n| '+' | '.join('---' for _ in heads)+' |\n'+'\n'.join('| '+' | '.join(str(v).replace('|','／').replace('\n',' ') for v in row)+' |' for row in rows)+'\n')
    def img(self,url,caption,cls='diagram'):
        self.h.append(f'<figure class="{cls}"><a href="{url}" target="_blank"><img src="{url}" alt="{E(caption)}" loading="lazy"></a><figcaption>{E(caption)}</figcaption></figure>');self.m.append(f'![{caption}]({url})\n')
    def code(self,s):self.h.append('<pre><code>'+E(s)+'</code></pre>');self.m.append('```powershell\n'+s+'\n```\n')
    def raw(self,s):self.h.append(s)
D=Doc()

def svgfile(name,w,h,items):
    (OUT/'images'/name).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img"><style>text{{font-family:Segoe UI,Microsoft YaHei,sans-serif;fill:#233e3d}}.tiny{{font-size:13px}}.body{{font-size:16px}}.title{{font-size:24px;font-weight:650}}</style><rect width="100%" height="100%" fill="#f7f5ed"/>'+''.join(items)+'</svg>',encoding='utf8')
def txt(x,y,s,size=16,fill=None):return f'<text x="{x}" y="{y}" font-size="{size}"'+(f' style="fill:{fill}"' if fill else '')+'>'+E(s)+'</text>'
def rect(x,y,w,h,fill,stroke='#adc1b7',rx=4):return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}"/>'
def line(x1,y1,x2,y2,c='#637d73',width=2):return f'<path d="M{x1},{y1} L{x2},{y2}" stroke="{c}" stroke-width="{width}" fill="none"/>'

def diagrams():
    a=[txt(24,35,'G1 · 每一个轴肩摩擦支点：从固定侧向螺钉头看',24),txt(24,62,'顺序示意，不按比例；一处 8 件标准件，活动叉耳夹在两片 M4 大垫之间。',15)]
    labels=[('M3 螺母','1 枚','#97a6af'),('M3 反力垫','Ø9 × 0.8 · 1 片','#b8c1c4'),('固定座反力壁','打印件','#759ba0'),('M4 大垫','Ø12 × 1 · 1 片','#b8c1c4'),('旋转叉耳','打印件','#e4a268'),('M4 大垫','Ø12 × 1 · 1 片','#b8c1c4'),('A8 碟簧 ×2','相对、非同向套叠','#d4b984'),('M4 普通垫','Ø9 × 0.8 · 1 片','#b8c1c4'),('轴肩螺钉','Φ4×8 / M3 螺纹6','#97a6af')]
    for i,(title,sub,color) in enumerate(labels):
        x=24+i*112;a.extend([rect(x,106,100,92,color),txt(x+4,135,title,12),txt(x+4,167,sub,10)])
        if i<8:a.append(txt(x+101,155,'→',14))
    a.extend([txt(24,238,'先装螺母与反力垫，再装活动件；轴肩光杆穿活动叉耳，M3 螺纹进入捕获螺母。',17),txt(24,272,'铰链做 1 处；十字核心做 4 处。两只传感器不等于只有两处支点。',17),txt(24,310,'沿用已验证的 O11 垫片与碟簧方向，按手感调紧；本教程不增加冗余摩擦件。',16)])
    svgfile('friction-stack.svg',1050,344,a)
    a=[txt(24,38,'G4 · 磁铁与传感板安装朝向',24),txt(24,66,'侧剖示意；目标间隙指磁铁表面到 IC 封装顶面，不是 PCB 表面。',15)]
    a.extend([rect(65,110,230,48,'#d98e65'),txt(81,140,'旋转件 + Φ6×2.5 径向磁铁',15),rect(121,218,118,32,'#444e57'),txt(131,239,'MT6701',16,'#fff'),rect(55,253,250,14,'#75a39a'),txt(325,267,'PCB：12 × 10 × 1 mm',16),line(181,159,181,216,'#aa5b31'),txt(201,188,'1.00–1.75 mm',17),txt(60,302,'器件面朝磁铁，中心轴对齐',18),txt(480,125,'磁铁侧壁少量非导电胶：防止磁铁自转',16),txt(480,165,'胶完全固化后再固定磁铁座盖',16),txt(480,205,'板托夹滑入口保持通畅，线从开口端引出',16),txt(480,245,'不要把胶涂到芯片顶面或运动间隙',16),txt(480,285,'卡扣让位后滑入；不靠压弯 PCB 强塞',16)])
    svgfile('sensor-section.svg',960,340,a)
    # Exact connector locations and pad-one direction from final native PCB.
    scale=6.3;fx=lambda x:40+(x-75)*scale;fy=lambda y:60+(y-75)*scale
    a=[txt(40,30,'中央板 · 元件面朝向你 / USB 在上',22),rect(40,60,80*scale,94*scale,'#e4eee5')]
    for x,y in [(78,78),(152,78),(78,166),(152,166)]:a.append(f'<circle cx="{fx(x)}" cy="{fy(y)}" r="6" fill="#f7f5ed" stroke="#abc0b2"/>')
    a+=[rect(fx(91),fy(77),18*scale,21*scale,'#aecac0'),txt(fx(96),fy(80),'USB ↑',11),txt(fx(94),fy(88),'XIAO',15),txt(fx(94),fy(92),'ESP32S3',10)]
    for ref in ['J1','J2']:
        c=COMP['carrier'][ref]
        for p in c['pads']:
            x,y=p['at_mm'];a.append(f'<circle cx="{fx(x)}" cy="{fy(y)}" r="2.5" fill="#ae7342"/>')
        a.append(txt(fx(c['at_mm'][0])+(-20 if ref=='J1' else 8),fy(99),ref,12))
    for r in ROUTES:
        c=COMP['carrier'][r['carrier_reference']];x,y=c['at_mm'];clr={'A':'#92b2a0','B':'#94bbcf','C':'#d2b68b'}[r['connector'][0]]
        a.extend([rect(fx(x-4),fy(y-2.5),8*scale,4.3*scale,clr,rx=2),txt(fx(x-3.6),fy(y-.5),r['connector']+' '+r['carrier_reference'],9)])
        for p in c['pads']:
            if p['pin'] not in ('1','2','3','4','5'):continue
            px,py=p['at_mm'];a.append(f'<circle cx="{fx(px)}" cy="{fy(py)}" r="1.8" fill="'+['#202b2d','#b8453d','#3c75b5','#3a8a58','#c49620'][int(p['pin'])-1]+'"/>')
    for ref in ('J3','U7','F5'):
        c=COMP['carrier'][ref];x,y=c['at_mm'];a.extend([rect(fx(x-4),fy(y-2.7),8*scale,5*scale,'#ebd6bc'),txt(fx(x-3.5),fy(y),ref,11)])
    for p in COMP['carrier']['J3']['pads']:
        if p['pin'] not in ('1','2'):continue
        x,y=p['at_mm'];a.append(f'<circle cx="{fx(x)}" cy="{fy(y)}" r="3" fill="'+('#b8453d' if p['pin']=='1' else '#263231')+'"/>');a.append(txt(fx(x)-3,fy(y)+13,p['pin'],9))
    a.extend([txt(590,90,'J3：外部稳压 5V / 2A',20),txt(590,122,'PH 2P，2.0 mm 间距',16),txt(590,154,'1 = +5V，2 = GND',18),txt(590,208,'A01–A14 → J10–J23',18),txt(590,240,'B01–B16 → J26–J41',18),txt(590,272,'C01–C16 → J42–J57',18),txt(590,325,'各 SH 5P 的焊盘，从图左到右：',16),txt(590,356,'1 黑 GND / 2 红 SENSOR_3V45',16),txt(590,387,'3 蓝 CLK / 4 绿 DO / 5 黄 CSN',16),txt(590,438,'插头背面与插座正面可能左右相反。',15),txt(590,468,'以针号和导通测试为准，不凭线色猜。',15),txt(590,520,'这是接线定位图，省略其余贴片器件。',15),txt(590,550,'位置与网络取自最终原生 KiCad PCB。',15),txt(590,604,'J2.7（XIAO 5V）保持 NC，不跨接 J3。',16)])
    svgfile('carrier-map.svg',960,695,a)
    a=[txt(24,36,'五芯线束 · 传感板元件面朝向你，焊线边朝下',23),rect(40,90,360,260,'#cfdfd1'),rect(150,145,140,93,'#405753'),txt(165,198,'MT6701',22,'#fff')]
    for i,(name,col) in enumerate(zip(['1 GND','2 VDD','3 CLK','4 DO','5 CSN'],['#263231','#bd5048','#437aac','#4b9367','#c9a131'])):
        x=95+i*62;a.extend([rect(x-12,312,24,18,'#c2a66f'),line(x,330,x,430,col,5),txt(x-23,465,name,12)])
    a.extend([txt(465,120,'1 → 黑 → 中央端口 pin 1（GND）',18),txt(465,165,'2 → 红 → pin 2（SENSOR_3V45）',18),txt(465,210,'3 → 蓝 → pin 3（CLK）',18),txt(465,255,'4 → 绿 → pin 4（该轴独立 DO）',18),txt(465,300,'5 → 黄 → pin 5（CSN）',18),txt(465,365,'PCB 上旧网络名 +3V3 = 受控的 3.45V 轨',15),txt(465,400,'板端由工厂焊接；插头由工厂压接与标号',15),txt(465,435,'传感板没有 SH 插座，不另买 46 个板端插头',15)])
    svgfile('wire-pinout.svg',930,495,a)
    a=[txt(24,38,'两路供电，共用地；信号经中央板缓冲和选通',24)]
    nodes=[(30,90,230,65,'电脑 USB','XIAO 逻辑 / 数据'),(350,90,245,65,'XIAO ESP32S3','MCU_3V3 → U6'),(30,228,230,70,'外部稳压 5V / 2A','J3.1 正 / J3.2 地'),(350,228,245,70,'F4 → D1 → U7 → F5','SENSOR_3V45 ≈ 3.451V'),(700,228,260,70,'46 路 MT6701','并联电源，独立 DO 回线')]
    for x,y,w,h,t,s in nodes:a.extend([rect(x,y,w,h,'#e1e9db'),txt(x+12,y+27,t,18),txt(x+12,y+53,s,15)])
    a.extend([line(260,121,347,121),txt(292,115,'→',20),line(260,264,347,264),txt(292,257,'→',20),line(595,264,697,264),txt(638,257,'→',20),line(824,218,824,121),line(824,121,600,121),txt(638,106,'DO → MUX → U6',16),txt(350,356,'U1/U2：CLK / CS 缓冲；U3–U5：三组 16:1 选通；U6：回到 3.3V',16),txt(30,412,'XIAO 的 5V 引脚不接传感电源。不要把两个 5V 电源互相短接。',18)])
    svgfile('power-flow.svg',1000,447,a)

USES={
'A8_SS':'52 个轴肩支点，每点 2 片，相对安装',
'MAGNET_D6_T2P5_DIAMETRIC':'34 个侧装磁铁座盖 + 12 个 P/D 端轴，各 1 颗',
'NUT_M1P6':'9 个十字核心合环，每处 4 枚',
'NUT_M2':'侧装磁铁 68；端轴合壳 48；端轴磁铁盖 24；端轴板夹 24',
'NUT_M3':'轴肩支点 52；传感板托夹 34；端轴摩擦调节 12',
'SCREW_M1P6_L6':'C14 / C15 合环，每核心 4 枚',
'SCREW_M2_L20':'12 个 P/D 端轴合壳，每端 4 枚',
'SCREW_M2_L4':'12 个 P/D 磁铁端盖，每端 2 枚',
'SCREW_M2_L5':'34 个侧装磁铁座盖，每个 2 枚',
'SCREW_M2_L8':'12 个 P/D 端轴 PCB 板夹，每端 2 枚',
'SCREW_M3_L8':'34 个传感板托夹 + 12 个端轴摩擦调节，各 1 枚',
'SHOULDER_D4_L8_M3_L6':'52 个轴肩摩擦支点，各 1 枚',
'W_M3_D9_T0P8':'52 个支点的固定座内侧反力垫，各 1 片',
'W_M4_D12_T1':'52 个支点的旋转叉耳两侧，各 2 片',
'W_M4_D9_T0P8':'52 个支点的螺钉头下，各 1 片',
'SELF_TAP_M2_L6':'中央板四角，直接拧入打印柱；不用金属螺母'}

LOCAL_USE={
'A8_SS':'每个轴肩支点 2 片，相对安装',
'MAGNET_D6_T2P5_DIAMETRIC':'本步每个实测轴 1 颗，位于对应磁铁座 / 端盖',
'NUT_M1P6':'C14 / C15 合环螺钉对应捕获窝',
'NUT_M2':'本步各 M2 螺钉对应捕获窝，一螺钉配一螺母',
'NUT_M3':'轴肩捕获窝、板托夹固定点，以及有 P/D 端轴时的摩擦调节槽',
'SCREW_M1P6_L6':'C14 / C15 合环',
'SCREW_M2_L20':'P / D 端轴固定半壳与活动半壳合壳',
'SCREW_M2_L4':'P / D 端轴的磁铁端盖',
'SCREW_M2_L5':'N003 / N004 侧装磁铁座盖，每个 2 枚',
'SCREW_M2_L8':'P / D 端轴的成对 PCB 板夹',
'SCREW_M3_L8':'每只传感板托夹 1 枚；每个 P/D 摩擦块调节 1 枚',
'SHOULDER_D4_L8_M3_L6':'轴肩摩擦支点，铰链 1 处 / 十字核心 4 处',
'W_M3_D9_T0P8':'固定座内侧，每个支点 1 片反力垫',
'W_M4_D12_T1':'旋转叉耳两侧，每个支点 2 片',
'W_M4_D9_T0P8':'螺钉头下、碟簧外侧，每个支点 1 片',
'SELF_TAP_M2_L6':'中央板四角，直接拧入打印柱'}

G1=[
'先找到固定座的六角螺母窝和反力垫座。放入 1 枚 M3 普通螺母、1 片 M3 外径 9 × 厚 0.8 反力垫，让螺母与轴孔同心；反力垫贴固定座内侧。先确认螺钉能轻松对正，不歪牙。',
'在固定座反力壁外放 1 片 M4 外径 12 × 厚 1 大垫，再放旋转叉耳，再放第 2 片同规格大垫；叉耳由两片大垫夹住。',
'向外依次放相对安装的 2 片 A8 碟簧、1 片 M4 外径 9 × 厚 0.8 普通垫。两片碟簧不要同方向完全套叠；沿用已通过实物验证的 O11 叠法。',
'从外侧穿入 Φ4×8 / M3 螺纹长 6 的轴肩螺钉。光杆穿过垫片和叉耳，M3 螺纹进入里面的螺母。边小幅摆动边拧紧到你需要的保持力，不能用普通 M3 全螺纹螺钉替代。',
'确认动的是叉耳，固定座内螺母不跟转、垫片未夹歪。装好磁铁座盖后会遮住轴肩头，所以先把摩擦力调好，再装磁铁与传感板。']
G2=[
'找 C14 下环、C15 上环盖与互相正交的 C01 / C02 两叉；有些叉已经和长骨一起打印，具体见每步的“一体件说明”。在环尚未封闭时，把 4 组 M3 螺母和 M3 反力垫放到对应捕获窝。',
'先将两叉交叉放进开口环中，逐一对正四个支点孔。按 G1 安装四套轴肩摩擦结构，先保持能够转动和微调的位置，不先将一侧完全拧死。',
'放入 4 枚 M1.6 螺母，合上 C15。四个角的螺钉头方向交错：同一对角线同向，两条对角线反向；按圆形头窝和六角螺母窝分辨，不能把 4 枚都从同一面穿入。用 4 枚 M1.6×6 交替、分次收紧。确认环的接缝贴合、叉耳和垫片仍在正确层次；不要靠螺钉硬拉未对齐的打印件。',
'分别转动 C01 和 C02，再均匀调整四个轴肩螺钉。核心是四个支点、两个测量轴；背面的两个支点也必须装。',
'在两个指定测量端装磁铁座盖和传感板托夹：每端 1 颗磁铁、2 枚 M2×5 + 2 枚 M2 螺母固定磁铁座盖，1 枚 M3×8 + 1 枚 M3 螺母固定板托夹。最后按 G4 确认芯片对准磁铁。']
G3=[
'P 表示靠近父骨架一端，D 表示靠近子骨架一端。固定半壳 case_minus 已并入骨架；另取 case_plus、radial_pad、magnet_cap 和正负两只 PCB 板夹。',
'找到带 M3 调节凸台的半壳，在尚未合壳、插入叉轴之前预装调节用 M3 螺母。把径向摩擦块放进该处的槽，凹面贴着叉臂的圆轴；M3×8 调节螺钉只顶摩擦块外侧，不直接顶打印轴。',
'将带限位环的叉臂轴从侧面放入固定半壳，环落入环形槽，止挡进入对应空间。盖上 case_plus，用 4 枚 M2×20 和 4 枚 M2 螺母固定。先检查圆轴能在允许范围转动，再调 M3×8 的松紧。',
'按 G4 固定 1 颗径向磁铁，磁铁端盖用 2 枚 M2×4 + 2 枚 M2 螺母固定。这里不是 M2×5，也不是合壳用的 M2×20。',
'把传感板放在轴端两只板夹之间，器件面朝磁铁，出线边朝预留出口。两只板夹共用 2 枚 M2×8 + 2 枚 M2 螺母固定。不能用螺钉压到芯片或拉弯电路板。',
'端轴有机械限位，也有线束限制，不是无限旋转轴。手动低速检查当前可用范围，无拉线、卡夹后再收线。']
G4=[
'领用工厂已焊好五线、做过导通检测并贴有端口标签的传感板。先核对板上元件面与出线端，不在装好的人偶上焊接。',
'侧装 N003 / N004 磁铁座盖先从斜向开口滑入 Φ6×2.5 磁铁，在磁铁侧壁间隙用少量非导电胶防转，完全固化后安装两枚 M2×5。螺钉头能挡住磁铁滑出，但不能代替圆磁铁的防转粘接。P/D 端轴磁铁同样需要防止相对轴自转；保持端面清洁。',
'卡扣式传感板托夹先脱离关节，在开口端轻让弹性卡舌，把 PCB 沿导轨平行滑入，让卡舌复位；线从开口端引出。不要从正面压芯片或弯曲 PCB 强塞。卡舌如有裂纹、永久变形，换该打印件。',
'传感器 IC 顶面朝磁铁，磁铁旋转中心与 IC 中心相对；名义封装顶面间隙 1.00–1.75 mm。这个间隙不同于板面距离。实际磁场、偏心和测量误差仍由 O22 首件与标定记录确认。',
'34 个托夹用 M3×8 + M3 螺母固定，12 个端轴用成对板夹固定。装完轻拉线束时不能带动 PCB，也不能让固线胶进入导轨或磁铁间隙。',
'先做线束出口处应力释放，再在同一刚性骨段上用扎带固定；跨运动缝留 U 形活动段，不把相邻两骨段捆死。磁铁与座盖固化后视作一个替换单元。']

def intro():
    D.heading(1,'O22 人偶拼装教程','start')
    D.p('对应 A1 mini 打印盘 A01–A10。按 **盘号 → 零件号 → 关节 → 电路端口** 查找，覆盖 25 个关节与中央板安装。左右一律按人偶自身区分。','lead')
    D.raw('<div class="hero-actions"><a class="button" href="../../bench/revO22/PoseDoll_O22_Assembly_Guide.zip" download>下载完整教程包 ↓</a><a href="ASSEMBLY.zh-CN.md">文字清单</a><button class="outline" onclick="window.print()">打印 / 保存 PDF</button></div>')
    D.p('本教程使用已保存的 O22 设计和 A1 mini 排盘，不改变结构。186 件 = 185 件装机件 + 1 件焊接量规；另有可选 T01 两件传感器小样。O11 的配合和摩擦已由你实测通过；O22 新传感板、线束及整机测量仍需首件实测，以下 CAD 图不是已完成实物装配的照片。','note')
    D.heading(2,'00 · 开始前先分袋、准备五金与电路','prepare')
    D.listing([
'每盘冷却取件后，按排盘编号图把零件装袋，标签写完整的“盘 A05-19 / N004 / 左锁骨前后”。N003、N004、P013 等打印编号可重复，盘内序号才唯一；它们不是传感器的电路端口。',
'清除支撑和毛刺，尤其是垫片座、螺母窝、PCB 导轨、磁铁侧槽与摩擦轴面；使用你已验证的 O11 工艺，不扩大精配合孔来迁就错规格五金。',
'工具：与螺钉头匹配的内六角批头（轴肩螺钉为 3 mm）、游标卡尺、镊子、小尖嘴钳、剪钳、万用表、标签笔、软垫。胶分别用于磁铁防转和电子线束柔性固线，按材料说明完全固化。',
'先把电子加工包交给供应方：48 块已焊线的传感板（46 使用 + 2 完整备件）、1 块中央成品板、1 块 XIAO、压接并逐路标号的线束。由供应方完成贴片、板端焊接、端子压接及导通检测；你负责装配和插接。',
'机械部分按 S01–S25 顺序装，传感板可以在每个关节完成后装入，但先不接电。推荐左臂做首个完整线束样段，通过后再按同样方法做右侧；不要封背盒后才开始排线。',
'在软垫上托住骨架操作，不让未装完的关节承受整机重量。先调整摩擦，再覆盖轴肩的磁铁座盖；先放内部螺母和反力垫，再关闭环或端轴外壳。'],True)
    D.heading(2,'01 · 从打印盘找到装配步骤','plates')
    D.p('“首次领用”统计每件只取一次；在后续关节步骤出现的长骨是已经装上的连接件。可点击盘图放大编号，也可以直接打开对应步骤。')
    D.raw('<div class="plate-grid">')
    for p in PM['plates']:
        if p['optional']:continue
        steps=sorted({s['step'] for s in STEPS if any(k in s['parts'] for k in [i['part'] for i in p['items']])})
        D.raw('<article class="plate-card">')
        D.heading(3,f"打印盘 {p['id']} · {p['title']}",'plate-'+p['id'])
        D.img(f"../../bench/revO22/a1mini/{p['preview']}",f"打印盘 {p['id']} 的 {p['count']} 件；编号对应下方清单",'plate-preview')
        D.p('涉及步骤：'+ '、'.join(f'[{s}](#{s})' for s in steps))
        D.raw('<details><summary>展开本盘每件的去向</summary>')
        D.table(['盘内编号 / 打印号','零件','首次领用 / 后续连接'],[[f"{p['id']}-{i['number']:02} / {i['id']}",zh(i['part']),f"[{FIRST[i['part']]}](#{FIRST[i['part']]})"+('；还用于 '+ '、'.join(s['step'] for s in STEPS if i['part'] in s['parts'] and s['step']!=FIRST[i['part']]) if any(i['part'] in s['parts'] and s['step']!=FIRST[i['part']] for s in STEPS) else '')] for i in p['items']])
        D.raw('</details></article>')
    D.raw('</div>')
    D.p('T01 为传感器安装小样：T001 传感桥 + T002 磁铁桥，单独在台面上核验板厚、封装间隙与磁场。**不装在人偶上、不计入 186 件。** [小样与首件要求](../../bench/revO22/physical_tests/ACCEPTANCE.zh-CN.md)。')
    D.heading(2,'02 · 全部金属件与磁铁清单','hardware')
    D.p('下面是整机净用量。备件是采购损耗备份，**不是增加到关节里的冗余零件**；每步的五金清单已分配全部 958 件标准件（912 件金属紧固／摩擦件 + 46 颗磁铁）。电子连接器和排针另列，不混进这个总数。')
    D.table(['规格 / SKU','净用','可选备件','含备件采购数','装在哪里'],[[r['name_zh'].replace('，弹力待测',''),str(r['net_quantity']),str(r['optional_spares']),str(r['suggested_total']),USES[k]+f"；`{k}`"] for k,r in STOCK.items()])
    D.p('螺钉长度按头下长度识别，分开存放 M2×4 / ×5 / ×8 / ×20。CAD 中 M1.6 螺钉头为 Φ3×1.6、内六角 1.5 mm、螺距 0.35 mm；M1.6 螺母对边 3.2、厚 1.3 mm。M2 螺母对边 4、厚 1.6 mm；M3 螺母对边 5.5、厚 2.4 mm。普通 M2 圆柱头包络为 Φ3.8×2，M3 为 Φ5.6×3；用现有验证件核对头部与沉孔。M3、M2、M1.6 都用普通六角螺母，不用带尼龙圈的锁紧螺母替换。磁铁必须直径方向充磁，不能买上下两面 N/S 的轴向充磁磁铁。')
    D.heading(2,'03 · 四种通用装法','recipes')
    D.p('每个步骤会直接写需要哪一种装法，并给出真实的盘号和五金数量。这里的顺序适用于现有设计；不同轴的朝向以该步骤的 CAD 模型为准。')
    for n,title,rows in [('G1','轴肩、垫片和碟簧',G1),('G2','两轴十字核心',G2),('G3','P / D 有限扭转端轴',G3),('G4','磁铁、传感板与局部应力释放',G4)]:
        D.heading(3,n+' · '+title,n)
        if n=='G1':D.img('images/friction-stack.svg','每处轴肩摩擦支点的层次顺序；不按比例')
        if n=='G4':D.img('images/sensor-section.svg','磁铁与传感板侧剖示意；IC 元件面朝磁铁')
        D.listing(rows,True)
    D.heading(3,'G5 · 一体式铰链的特殊顺序','G5')
    D.listing(['父骨架端部已经包含完整固定座，子骨架端部已经包含旋转叉耳。不再寻找旧版 base_service_half，也不用旧版固定座合壳螺钉。','在旋转叉耳装入前，从固定座侧面的检修开口，沿槽送入 M3 螺母和 M3 反力垫，让它们分别落在六角窝和圆形座。这里“侧面”是零件自身的槽口，不是人偶统一的左侧。','按 G1 装入旋转叉耳和一套轴肩结构。轴肩就位后帮助限制内部件滑出；先调整保持力。最后按 G4 装侧装磁铁座盖和板托夹。'],True)

def joint_steps():
    D.heading(2,'04 · 按身体部位逐步拼装','steps')
    D.raw('<div class="step-jump">'+''.join(f'<a href="#{s["step"]}">{s["step"]} {E(s["title"])}</a>' for s in STEPS)+'</div>')
    for s in STEPS[:-1]:
        sid,jid=s['step'],s['id'];pa='frame/'+s['parent'];ch='frame/'+s['child']
        D.raw('<article class="assembly-step">')
        D.heading(3,f"{sid} · {s['title']}",sid)
        D.p(f"连接 **{part(pa)} → {part(ch)}**。本步需打开打印盘："+'、'.join(s['plates'])+'。','connection')
        D.raw(f'<button class="view-step" data-step="{sid}">查看本步可旋转 CAD / 单件识别 ↗</button>')
        D.img(f'images/{sid}.png',f"{sid} {s['title']} · CAD 装配位置；蓝色为父骨架，橙色为子骨架",'joint-image')
        D.table(['取件位置','名称 / 原始键','本步用途 / 状态'],[[part(k),f'`{k}`',('本步新取。' if k in s['new_parts'] else f'已在 {FIRST[k]} 取用，直接使用已装骨架。')+role(k)] for k in s['parts']])
        D.table(['五金 / 磁铁','本步数量','位置'],[[STOCK[k]['name_zh'].replace('，弹力待测',''),v,LOCAL_USE[k]] for k,v in s['stock'].items()])
        actions=[]
        if s['kind']=='hinge':
            actions=[f'将 {part(pa)} 的固定关节座与 {part(ch)} 的旋转叉耳摆到图示连接位置。侧槽尚未被挡住时，预装 1 枚 M3 螺母与 1 片 M3 反力垫。',
'按 [G5 一体铰链](#G5) 和 [G1 轴肩层次](#G1) 装 1 套轴肩结构。单个支点为 1 枚轴肩螺钉、2 片 M4 大垫、2 片 A8 碟簧、1 片 M4 普通垫，外加刚才放入的螺母和反力垫。',
f"调整摩擦后，按 [G4](#G4) 给 {part(jid+'/magnet_cartridge')} 装 1 颗磁铁，固化后用 2 枚 M2×5 + 2 枚 M2 螺母固定到旋转侧。",
f"把下表所列传感板装入 {part(jid+'/sensor_cassette')}，再用 1 枚 M3×8 + 1 枚 M3 螺母固定到固定侧。传感器与磁铁相对，不能把两者都固定到同一旋转骨段。"]
        else:
            forks=[resolve(jid+'/'+x) for x in ('C01','C02')]
            actions=[f"取 {part(jid+'/C14')}、{part(jid+'/C15')}。两叉分别是 {part(forks[0])} 的 C01 部位、{part(forks[1])} 的 C02 部位；已经连在骨架上的叉不要拆分或另找重复打印件。",
'按 [G2](#G2) 先预装 4 枚 M3 螺母与 4 片 M3 反力垫，把两叉交叉放入环，再按 G1 装四套轴肩结构；随后用 4 枚 M1.6×6 + 4 枚 M1.6 螺母合环。']
            stages=['P'] if s['kind']=='three_axis' else ([] if s['kind']=='ankle_core' else ['P','D'])
            for end in stages:
                fixed=resolve(f'{jid}/{end}_case_minus');fork=resolve(jid+('/C01' if end=='P' else '/C02'))
                actions.append(f"{end} 端按 [G3](#G3)：{part(fixed)} 内是一体固定半壳，容纳 {part(fork)} 的圆轴与限位环；装 {part(jid+'/'+end+'_radial_pad')}，M3×8 + M3 螺母调摩擦。用 {part(jid+'/'+end+'_case_plus')} 和 4 枚 M2×20 + 4 枚 M2 螺母合壳。磁铁端盖用 2 枚 M2×4 + 2 枚 M2 螺母；两只 PCB 板夹用 2 枚 M2×8 + 2 枚 M2 螺母。")
            for end in ('C01','C02'):
                actions.append(f"{end} 测量端按 [G4](#G4)：{part(jid+'/'+end+'_magnet_cartridge')} 内放 1 颗磁铁，用 2 枚 M2×5 + 2 枚 M2 螺母固定到叉臂端；{part(jid+'/'+end+'_sensor_cassette')} 先滑入传感板，再用 M3×8 + M3 螺母固定。")
        actions.append('局部慢慢活动，确认每一相邻活动面不挤压垫片、PCB 和线束。按需要的手感调保持力即可；当前可用行程由实物相邻件与线束决定，软件 raw_limits 不是要求你硬拧到的机械行程。')
        D.listing(actions,True)
        rr=[r for r in ROUTES if r['module']==jid]
        D.table(['电路端口 / 中央板位号','测量轴','传感板装在','对应磁铁装在','每根线建议长度'],[[f"端口 {r['connector']} / {r['carrier_reference']}",f"`{r['raw_id']}`",' + '.join(part(k) for k in r['mounts']),part(r['magnet_mount']),f"{r['proposed_cut_each_wire_mm']} mm × 5 根，首件后定长"] for r in rr])
        D.p('本步完成检查：'+'、'.join(r['connector'] for r in rr)+' 标签对应正确；磁铁不相对载体打滑；转轴可手动摆动并保持；线先松放到背盒方向，留待走线章节统一固定。','check')
        D.raw('</article>')

def electronics():
    D.heading(2,'05 · 电路、中央板与背盒','electronics')
    D.p('以下区分“交给工厂做的电路”和“你总装时需要做的插接”。整机没有电机，也不需要电池、摄像头或旧版 AS5048A 串链排线。传感板各自五线返回中央板。')
    D.table(['要准备的东西','数量 / 规格','交付与装配要求'],[
['MT6701 传感成品板','46 使用 + 2 完整备件；12×10×1 mm；SOP8','裸板报价口径 50 张、装 48 张；芯片 50 颗含 2 颗加工损耗，不是多装 50 路。板端五线由工厂焊好并标号。'],
['中央采集成品板','1 块；80×94×1.6 mm、四层','裸板最小订单按 5 张核价，只装 1 张。使用最终 O22 PCB 与 BOM，不用 placement / route_input 中间板。'],
['XIAO ESP32S3 普通版','1 块；两排各 7 针、中心距 15.24 mm','中央板顶面到 XIAO PCB 底面 4.0 mm，由工厂用盘 A03-09 P242 量规定位焊接后取出。'],
['中央板传感插座','46 个 BM05B-SRSS-TB；SH 1.0 mm 5P 顶插','由工厂贴在中央板上；已经计入 PCBA，不再购买另一套。'],
['线端塑壳 / 压接端子','48 个 SHR-05V-S + 240 个 SSH-003T-P0.2-H','对应 46 套使用线 + 2 套完整备用线；可另留 2 塑壳 / 20 端子作为加工损耗。传感 PCB 端直接焊线，没有第二套插座。'],
['五色柔性线','单根 AWG30 铜线，外径 0.4–0.7 mm','每色 22.75 m 实装，加两套 750 mm 备件为 24.25 m；再加 10% 下料损耗约 26.68 m/色，五色约 133.38 m。下料表见下一节。'],
['外部稳压电源与输入尾线','5V / 2A 电源 1 个；PH 2P 线端 1 套','J3 为 PH 2.0 mm，不是传感 SH 1.0 mm。线端 PHR-2 + 2 枚 SPH-002T-P0.5S；可用符合端子绝缘尺寸的 AWG24 柔线。适配器端按实际插头定做，工厂标明正负与导通。'],
['USB 数据线','1 根，接 XIAO USB-C','必须支持数据。线长按桌面布置，插头外形须通过背盒 USB 开口。'],
['2.5 mm 扎带','65 根净用，建议另备 10 根','用于局部应力释放、沿骨架分束及背盖；不绕过旋转缝把两骨段锁在一起。'],
['磁铁固持胶 / 电子固线胶','按实际小包装准备','磁铁侧壁非导电防转胶；板线出口用可返修、中性柔性电子胶。工厂固线已计入工序时不重复收费。']])
    D.p('连接器系列与端子依据 [JST SH 官方图纸](https://www.jst-mfg.com/product/pdf/eng/eSH.pdf) 和 [JST PH 官方图纸](https://www.jst-mfg.com/product/pdf/eng/ePH.pdf)。输入尾线列在这里是为了把 J3 的配对件补充说明清楚，不是新增一块电路。实际总价仍按完整询价核算。')
    D.heading(3,'工厂贴片与焊线：使用这些文件','factory')
    D.listing([
'[完整电子 BOM](../../bench/revO22/manufacturing/electronic_bom.tsv) 与 [首件加工要求](../../bench/revO22/manufacturing/RFQ.zh-CN.md) 一起给工厂；Gerber、钻孔与坐标文件在 [已保存工程包](../../bench/revO22/PoseDoll_O22_Engineering_Package.zip) 的 manufacturing 目录。',
'传感板每块：U1=MT6701CT-STD-R，C1=100nF X7R 16V 0603，C2=1µF X7R 16V 0603，R1=33Ω 0603 串联 DO，R2=10kΩ 0603 上拉。J1 是五个焊线焊盘，不是另购连接器。芯片脚 1/2 接供电，4 接地，6 为 DO，7 为 CLK，8 为 CSN；按封装圆点与 PCB pin 1 对齐，3/5 不接。',
'中央板主要有 U1/U2=SN74LVC244APWR，U3–U5=CD74HC4067PW，U6=SN74LVC125APWR，Q1=2N7002；由缓冲器、三组 16:1 选通和 MCU 侧电平接口完成采集，不把传感器 DO 直接跨接到 XIAO。',
'供电链为 J3 → F4 输入保护 → D1 SS14 → U7 AP3429AW5-7 + L1 2.2µH → F5 → SENSOR_3V45。F4=1206L110THR；F5=0467001.NR 1A 快断保险丝，不任意换成 PTC。',
'反馈 R50=316kΩ、R51=66.5kΩ，0.1%、≤25ppm/K，对应标称约 3.451V。C7/C8/C9 虽标称 22µF，仍需工厂返回直流偏压曲线；C7 在 4.1V 下有效容量至少 10µF，C8+C9 在 3.45V 下合计至少 20µF。当前候选料号未因教程编写而变成已实测批准。',
'板端焊线、端子压接、套管 / 柔性胶应力释放、端口双端标签、逐芯导通和无短路检查均由供应方完成。器件加焊料总高度不超过 1.85 mm；胶不得进入板托夹导轨或芯片对磁铁的间隙。'],False)
    D.p('降压器依据 [AP3429 官方数据表](https://www.diodes.com/datasheet/download/AP3429.pdf)。完整逐位号 BOM 在网页附录可展开查看；器件采购和工厂焊接不是用户总装时额外重复购买的散件。')
    D.heading(3,'S26 · 安装中央板与 XIAO','S26')
    D.p(f"本步连接 {part('frame/chest')}、{part('o22/controller_lid')}；{part('fixture/xiao_spacing_gauge')} 仅在焊接定位时使用。打印盘 A01 的盖要等 A02 的胸架装好、电路检查完成后再盖；A03 的量规不留在里面。",'connection')
    D.raw('<button class="view-step" data-step="S26">查看背盒与中央板 CAD ↗</button>')
    D.img('images/S26.png','S26 背盒与中央板 CAD，显示装配位置；接线完成前保留敞开状态','joint-image')
    D.listing([
'让工厂按中央板焊接位置装 XIAO：USB 端口朝板上边缘，两排针间距 15.24 mm，PCB 之间净距 4.0 mm。插入 P242 量规定位后焊接，冷却并检查焊点，再取出量规。J2.7 的 XIAO 5V 不接传感供电，不能拉跨接线去 J3。',
'把已完成台面电测的中央板放到胸架背盒四根柱上，旋转整块板使 USB-C 对准背盒专用 USB 开口，元件面朝盒外 / 盖板。四角孔对正后用 **4 枚塑料自攻 M2×6、头径≤4 mm** 交替拧入；不用金属 M2 螺母，也不用普通机牙螺钉强行攻塑料。',
'从预留进线开口引入各身体分束，先按端口表插上短的躯干线，再接手臂、腿部线。端口多而密，捏塑壳插拔，不拉导线。留出电源、USB 插头和拆盖的维护余量。',
'背盖先放在一旁。先完成单路、单组、左臂和全部通道检查，再收好余线、装背盖，用两条 2.5 mm 扎带穿现有固定槽固定；这两条计入 65 根，不增加盖板螺钉。盖上后再确认没有压住 U 环或线端。'],True)
    D.img('images/power-flow.svg','USB 与外部电源的职责、传感电源及回传信号路径')
    D.img('images/carrier-map.svg','中央板在桌面上的元件面视图，USB 朝图上方；装入背盒后以实体 USB 开口为准。A01 / B01 / C01 是电路端口，不是打印盘')
    D.heading(3,'五芯线的针序与供电边界','pinout')
    D.img('images/wire-pinout.svg','传感板焊线边朝下的正面针序；插头从背面看会镜像，请按针号核对')
    D.table(['针号','颜色','传感板网络','中央板网络 / 功能'],[['1','黑','GND','共同地'],['2','红','+3V3（旧网络名称）','实际接 SENSOR_3V45，标称约 3.451V'],['3','蓝','CLK','本组 SSI 时钟'],['4','绿','DO','该轴独立返回，经对应 MUX 通道选通'],['5','黄','CS_N','本组片选']])
    D.p('五根线逐根直通同号针，不交叉。板上叫 +3V3 不表示你应外加 3.3V；它由中央板统一受控供电。46 路都是独立回线，DO 不能并在一起，也不是上一块板出线接下一块板的串链。')
    D.heading(3,'XIAO 引脚核对表（供工厂与排错使用）','xiao')
    xiao=[('J1','1','D0','GPIO1'),('J1','2','D1','GPIO2'),('J1','3','D2','GPIO3，未用'),('J1','4','D3','GPIO4'),('J1','5','D4','GPIO5'),('J1','6','D5','GPIO6'),('J1','7','D6','GPIO43'),('J2','1','D7','GPIO44'),('J2','2','D8','GPIO7'),('J2','3','D9','GPIO8'),('J2','4','D10','GPIO9'),('J2','5','3V3','MCU 3.3V'),('J2','6','GND','地'),('J2','7','5V','NC，保持不连接')]
    D.table(['中央板焊盘','XIAO 引脚','GPIO / 电源','最终板网络'],[[ref+'.'+pin,p,g,next(x['net'] for x in COMP['carrier'][ref]['pads'] if x['pin']==pin).replace('unconnected-(J1-Pin_3-Pad3)','NC').replace('unconnected-(J2-Pin_7-Pad7)','NC')] for ref,pin,p,g in xiao])
    D.p('引脚命名依据 [Seeed XIAO ESP32S3 官方文档](https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/)。表中的 J1/J2 是中央板位号；不是传感小板的 J1 五线焊盘。两排针方向按最终原生 PCB 核对，不能按左右两排都从上往下编号来猜。')
    D.heading(2,'06 · 46 路逐根接线与跨关节走线','wiring')
    D.p('下面的长度是**每一根**线的下料候选长度，每路需要黑红蓝绿黄各一根。沿用当前 routing_plan 的运动余量；必须先试装确认，不能按旧 wiring.json 的短报价估计裁线。尽量先做 1 根完整的左臂代表线束，再让工厂定批量长度。')
    D.listing(['线从传感器出口先随所属刚性骨段固定，再跨关节形成 U 环，然后沿表中路径依次走到胸部中央板。支点扎带落在骨架实体上，不能跨旋转接缝。','名义活动环半径 8 mm，装配最小弯曲半径 7 mm（可绕直径 14 mm 的光滑圆棒成形后取下）。线不绷直，也不让多余环卷进齿形止挡、叉耳或垫片。','每动一个关节，看近端和远端线都没有拉动 PCB、压住相邻件或抽紧插头；再调整局部扎带。远处肢体碰撞可以通过姿势规避，但不能借此忽略相邻关节的夹线。','线两端都标“电路端口 + raw_id”，例如“B05 / elbow_l.flex/r0”；打印件另外标“盘 A04-03”。在两个体系都叫 A01 的地方始终保留“盘”或“端口”前缀。'],True)
    D.raw('<label class="search-label">筛选线束：<input id="wire-search" type="search" placeholder="例如 B05、左膝、S18、A08" aria-label="筛选线束"></label><div id="wire-table">')
    D.table(['端口 / 位号','步骤 / 测量轴','传感板固定件','磁铁固定件','五色各一根','沿骨架到背盒'],[[f"{r['connector']} / {r['carrier_reference']}",f"[{r['step']}](#{r['step']}) {zh(r['module'])} / `{r['raw_id']}`",' + '.join(part(k) for k in r['mounts']),part(r['magnet_mount']),f"{r['proposed_cut_each_wire_mm']} mm",' → '.join(zh(x) for x in r['anchor_chain'])] for r in ROUTES])
    D.raw('</div><p id="wire-filter-state" aria-live="polite"></p>')
    D.p('A 组只使用 A01–A14（J10–J23）；B、C 组各 16 路。没有需要补装的 A15 / A16，J24 / J25 不在本版 46 个传感插座中。对应路径的三维坐标和余量记录见 [当前线束规划](../../bench/revO22/harness/routing_plan.json)。')

def commissioning():
    D.heading(2,'07 · 分段上电、固件与装配检查','power')
    D.p('先在台面检查中央板与一只传感器，再在关节上检查，最后才连接全部 46 路。插拔、改线和测导通时先断开 USB 与外部 5V。正常串口收到的是二进制帧，不会连续打印可读角度。')
    D.table(['阶段','操作','通过标准 / 异常时处理'],[
['断电检查','核对 J3 的 1 脚 +5V / 2 脚 GND；XIAO 5V 不接 J3；每根五线对号导通','万用表查错接、邻针短接及焊点。电容充电可能让蜂鸣器短暂响，不能只凭一次蜂鸣判定短路或通过。'],
['中央板空载','先不插传感器；供应方以受控电源完成电源首件；再分别接 USB 与外部 5V','确认 MCU_3V3 与 SENSOR_3V45 是不同电压域，后者约 3.451V；没有异常发热、反向送电。'],
['单路传感器','断电后接 A01 / J10，安装或对准磁铁；上电读取原始诊断','只要求所装这一轴有有效 SSI 帧、CRC 正确、状态正常，缓慢转磁铁时未标定角度连续变化。其他 45 路未装会无效，这是预期的。'],
['一组满载','先 B01–B16 或 C01–C16 接齐做 16 路检查，A 组只有 14 路','核对每路端口，不把共享 CLK / CS 误认为 DO 也能并联。采样稳定，转一轴只影响该轴的相对测量。'],
['左臂样段','接 A11 / A12 + B01–B08，共 10 路；缓慢活动各相邻关节','检查焊线不受剥离力，U 环不抽紧，端子不松脱，各轴标号及传感板固定侧正确。首件后确认长度，再复制右臂。'],
['全部 46 路','接齐 A01–A14、B01–B16、C01–C16 后再进入完整捕获','远端传感板供电 ≥3.10V 且不超过 3.6V；外部适配器带载出口 ≥4.9V、输入线压降 ≤0.08V、U7 VIN ≥4.05V；电源纹波 / 热态等按原首件表记录。由工厂在易短路的小焊盘处测量。'],
['完成机械装配','逐关节看活动面、磁铁防转、固定螺母、板夹和走线，再盖背盒','非相邻身体部件的姿势碰撞可调整姿势规避；相邻件或线束夹住必须重新调整装配 / 行程，不能靠强扭通过。']])
    D.heading(3,'固件烧录（新 XIAO 才需要）','firmware')
    D.p('已保存工程包内的固件文件名仍带 o21，这是 O22 继续使用的 USB RAW46 固件名称；本教程已把 3 个二进制与构建 flash_args 对照核验。先只接 XIAO USB，外部传感 5V 暂不接。工厂若已烧录，直接做诊断即可。')
    D.p('在已安装 Python / esptool 的电脑上，进入工程包的 `firmware_binaries` 目录，把下例 COM7 换成设备实际端口；用串口设备列表核对，不能照抄端口。需要时按住 BOOT 再插 USB 进入下载模式，烧录后复位。烧录会覆盖该 XIAO 上的原有程序。')
    D.code('python -m esptool --chip esp32s3 --port COM7 --baud 460800 write-flash --flash-mode dio --flash-freq 80m --flash-size 8MB 0x0 bootloader.bin 0x8000 partition-table.bin 0x10000 posedoll_o21_usb_raw46.bin')
    D.p('教程不会自动访问或烧写连接到电脑的设备。需要换工具版本时，让工厂按其 esptool 版本采用等价 write_flash / write-flash 命令，地址和二进制保持不变。')
    D.heading(3,'部分安装时的原始读数诊断','diagnostic')
    D.p('附带 [usb_diagnostic.py](tools/usb_diagnostic.py)：只在你明确指定串口时打开设备，读取原始 SSI 状态；记录全部数据，但只检查你指定的已装端口。它不生成可用测量证书，也不把未装传感器补零后送入 UE。使用电脑上装有 pyserial 的 Python 环境。')
    D.p('在教程目录运行，串口 COM7 仅为示例：')
    D.code('python tools/usb_diagnostic.py --port COM7 --ports A01 --seconds 1 --output single-A01.json\npython tools/usb_diagnostic.py --port COM7 --ports A11 A12 B01 B02 B03 B04 B05 B06 B07 B08 --seconds 1 --output left-arm.json')
    D.p('看输出的 valid / CRC / SSI status / idle 与未标定角度范围。只移动一个机械轴，确认标签对应那一轴。遇到 invalid 时查供电、磁铁朝向 / 间隙、CLK / DO / CSN 针序和线束，不能把 invalid 当成 0°。原有 usb_capture.py 要求 46 路完整且已标定；在只接一块板时拒绝捕获是正常行为。')
    D.heading(3,'标定与 UE 检查的交接','handover')
    D.listing([
'装配完成后保存每轴的传感器身份、端口、零位、方向、标定版本与原始读数。模板不是已完成标定；A 字站姿中的数值也不代表所有传感器零度。',
'依照 [O22 实物验收表](../../bench/revO22/physical_tests/ACCEPTANCE.zh-CN.md) 做角度精度、重复性、双向回差、线束与满载采集记录。未完成的字段保留未完成，不使用软件生成数据冒充实物测量。',
'46 路原始轴经过明确的机械组合得到 41 个语义自由度。先用设备数字骨架确认左右、轴向、参考姿势和实测变化，再在 UE 的已配置角色上检查基础姿态转换；角色比例造成的接触和穿模仍由后期调整。',
'用“只动左肘”“只转右前臂”“单侧抬臂”的不对称姿势验收，避免左右接反却在对称姿势下看不出来。保存可编辑的采集结果和原始记录，最后收束线材并盖上背盒。'],True)
    D.heading(3,'常见装配问题','troubleshooting')
    D.table(['现象','先查哪里'],[
['M3 轴肩旋紧后完全不动','用户已确认松紧控制摩擦；先略松轴肩，检查碟簧 / 垫片层次和光杆长度，不额外加摩擦垫或轴承。'],
['找不到 C02 或固定半壳','看对应步骤的“一体骨架”说明；它可能已经长在腰架、胸架、腿架上。不要从旧 O15/O16 文件补打一件。'],
['磁铁能在座内打转','侧槽螺钉只挡滑出；检查防转胶固化。打滑会破坏角度零位，先修复再重做受影响轴的标定。'],
['某一路不响应，别的轴却变化','断电后核对端口 / J 位号 / raw_id 与板夹安装位置；不可仅按 N003 / N004 的重复打印号识别。'],
['单板有效，接满后掉数据','检查远端压降、插头接触、5V 适配器、CLK/DO 串扰及线束应力；按原首件检查表记录，不靠加滤波隐藏错误。'],
['装一半时完整捕获被拒绝','使用部分通道诊断工具；等所有 46 路和真实标定完成后再使用完整捕获。'],
['手臂摆动牵扯板子','局部应力释放和刚性骨段上的固定不足，或 U 环太短；解开对应扎带重排线，不把线拉直来省长度。']])
    D.heading(2,'08 · 附录与文件对应','appendix')
    D.raw('<details><summary>工厂用完整电子 BOM（元件位号、封装、数量）</summary>')
    grouped=defaultdict(list)
    for r in BOM['components']:grouped[(r['board'],r['value'],r['footprint'],r['mpn_or_procurement_spec'])].append(r)
    D.table(['板 / 位号','值 / 封装','料号或要求','每板数量','装配总量'],[[k[0]+' / '+', '.join(r['references'] for r in rs),k[1]+' / '+k[2],k[3] or ('焊线焊盘，不采购插座' if k[1]=='FACTORY_SOLDERED_5_CORE' else '由供应方返回完整 AVL，遵守源 BOM 验收栏'),sum(r['per_board'] for r in rs),sum(r['net_quantity'] for r in rs)] for k,rs in grouped.items()])
    D.raw('</details>')
    D.table(['文件','用途'],[
['[guide-data.json](guide-data.json)','可机器核对的盘内零件 → 步骤 → 五金 → 电路映射'],
['[文字教程](ASSEMBLY.zh-CN.md)','与网页相同的步骤和清单；保存或打印使用'],
['[核对结果](verification.json)','186 件覆盖、958 件标准件分配、46 路端口 / 原生 PCB 针序核对'],
['[打印盘页面](../../bench/revO22/a1mini/index.html)','原 10 盘 3MF、编号图和打印说明'],
['[完整设计页](../full-doll-o22/index.html)','整机 CAD、原有验收与工程资料'],
['[最终中央板焊盘快照](evidence/carrier_native_pads.json)','来自最终 KiCad PCB 的元件位置、针号、网络及源散列'],
['[最终传感板焊盘快照](evidence/sensor_native_pads.json)','核对元件面、出线边及焊线针序'],
['[首件验收要求](../../bench/revO22/physical_tests/ACCEPTANCE.zh-CN.md)','保持原有首件门槛与真实证据要求']])
    D.p('版本：O22 / A1 mini 10 盘，2026-10-02。图示只展开零件帮助识别，不模拟真实插入轨迹；实际预装和穿装次序按文字步骤。教程包不重复包含全部打印模型和 KiCad 制造资料，请与已保存的两个原包一起使用。')

def build_scene():
    source=H/'tutorials/full-doll-o22';scene=read(source/'scene_universal.json')
    objects=[o.copy() for o in scene['scenes'][0]['objects'] if o['label'] in META]
    raw=np.fromfile(source/'geometry_universal.bin',dtype='<f4').reshape(-1,6)
    meshes={};chunks=[];first=0
    for k in dict.fromkeys(o['mesh'] for o in objects):
        m=scene['meshes'][k];a=raw[m['first']:m['first']+m['count']]
        meshes[k]={'first':first,'count':len(a),'min':a[:,:3].min(axis=0).tolist(),'max':a[:,:3].max(axis=0).tolist()};first+=len(a);chunks.append(a)
    # Reuse the saved viewer buffer instead of tracking another 75 MB copy.
    for k,m in meshes.items():m['first']=scene['meshes'][k]['first']
    for o in objects:
        o['module']=META[o['label']].get('module')
        m=meshes[o['mesh']];M=np.array(o['matrix']).reshape(4,4)
        corners=np.array([[x,y,z,1] for x in (m['min'][0],m['max'][0]) for y in (m['min'][1],m['max'][1]) for z in (m['min'][2],m['max'][2])])@M.T
        o['bounds']=[corners[:,:3].min(axis=0).tolist(),corners[:,:3].max(axis=0).tolist()]
        if o['label'] in PARTS:o['address']=PARTS[o['label']]['address'];o['name_zh']=zh(o['label'])
    data={'meshes':meshes,'objects':objects,'geometry_url':'../full-doll-o22/geometry_universal.bin','source_scene_sha256':sha(source/'scene_universal.json'),'source_geometry_sha256':sha(source/'geometry_universal.bin'),'scope':'Original A-stance CAD and unchanged shared vertex buffer; not assembly motion or physical evidence.'}
    (OUT/'scene.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf8')


def main():
    diagrams();intro();joint_steps();electronics();commissioning();build_scene()
    data={'schema':'POSEDOLL-O22-ASSEMBLY-GUIDE/1','steps':STEPS,'parts':PARTS,'first_use':FIRST,'routes':ROUTES,'hardware':STOCK,'pin_order':ROUTING['pin_order'],'source_plate_manifest_sha256':sha(B/'a1mini/manifest.json')}
    (OUT/'guide-data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    (OUT/'ASSEMBLY.zh-CN.md').write_text('\n'.join(D.m),encoding='utf8')
    view='''<dialog id="viewer"><header class="viewer-heading"><div><small>原始 O22 CAD · 装配位置识别</small><h2 id="viewer-title">关节查看</h2></div><button id="viewer-close" aria-label="关闭 CAD 查看器">关闭 ×</button></header><div class="viewer-layout"><div class="viewport"><canvas id="model" tabindex="0" aria-label="可旋转三维关节模型"></canvas><div id="viewer-status" role="status">按需加载三维模型…</div></div><aside class="viewer-controls"><label>装配步骤<select id="view-step-select"></select></label><label>选择零件<select id="view-part-select"></select></label><label class="checkbox"><input type="checkbox" id="isolate">只看选中件</label><label class="checkbox"><input type="checkbox" id="show-metal" checked>显示金属件</label><label class="checkbox"><input type="checkbox" id="show-electronics" checked>显示电路</label><label>展开识别 <input id="view-explode" type="range" min="0" max="1" step=".02" value="0"></label><div class="button-row"><button id="view-front">正面</button><button id="view-side">侧面</button><button id="view-reset">复位</button></div><p id="view-part-info"></p><p class="legend"><span class="parent">■</span>父骨架 <span class="child">■</span>子骨架<br><span class="printed">■</span>关节打印件 <span class="selected">■</span>选中件</p><p class="fine">拖动旋转，滚轮缩放。蓝色与橙色只是上下游连接关系，P / D 端以文字为准。展开是识别示意，不是插入轨迹。</p></aside></div></dialog>'''
    page='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>O22 · 按打印盘拼装人偶</title><link rel="stylesheet" href="style.css"></head><body><header class="topbar"><a class="brand" href="#start">POSEDOLL <span>O22 / ASSEMBLY</span></a><a href="../../bench/revO22/a1mini/index.html">查看打印盘 ↗</a></header><nav class="contents" aria-label="章节目录">'''+''.join(f'<a href="#{k}">{t}</a>' for k,t in [('prepare','准备'),('plates','按盘找件'),('hardware','五金'),('recipes','通用装法'),('steps','逐步拼装'),('electronics','电路安装'),('wiring','46 路接线'),('power','上电检查')])+'''</nav><main>'''+ '\n'.join(D.h)+'''</main>'''+view+'''<footer>O22 · A1 mini · 2026-10-02 / 按已保存设计编写，保留首件实测状态。</footer><script src="app.js"></script></body></html>'''
    (OUT/'index.html').write_text(page,encoding='utf8')
    inputs=[B/'a1mini/manifest.json',B/'mechanical/assembly_metadata.json',B/'profiles/device_profile.json',B/'harness/routing_plan.json',B/'procurement.json',B/'manufacturing/electronic_bom.json']+[ROOT/v['source'] for v in NATIVE.values()]
    checks={'status':'PASS','scope':'Digital inventory, CAD-derived reference and final native PCB connectivity only','main_print_instances':len(FIRST),'on_doll_print_instances':185,'assembly_tools':1,'optional_coupon_parts':2,'joint_steps':25,'controller_steps':1,'stock_instances_including_magnets':sum(r['net_quantity'] for r in STOCK.values()),'magnet_instances':46,'sensor_routes':len(ROUTES),'native_connector_pin_checks':len(ROUTES)*5,'input_sha256':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in inputs},'physical_assembly_verified':False,'O11_user_fit_and_friction_pass_preserved':True,'first_article_electronics_verified':False}
    (OUT/'verification.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({**{k:v for k,v in checks.items() if k!='input_sha256'},'geometry_bytes':(H/'tutorials/full-doll-o22/geometry_universal.bin').stat().st_size},ensure_ascii=False))

if __name__=='__main__':main()
