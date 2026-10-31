"""Presentation consumer of sealed O4 artifacts; preserves the original run."""
from revo4_evidence import *
import math,html
def main():
 rid='o4_20260924_h3';os.environ['REVO4_RUN_ID']=rid;v,o=run_paths()
 deps={k:read(v/(k+'_execution.json'))['artifacts'] for k in ('comparison','electronics','pcba_geometry','backlash')}
 os.environ['REVO4_DEPENDENCIES']=json.dumps(deps);readers={k:ArtifactReader(k) for k in deps}
 data=readers['comparison'].json(v/'hardware_comparison.json');e=readers['electronics'].json(v/'electronics.json');g=readers['pcba_geometry'].json(v/'pcba_geometry.json');b=readers['backlash'].json(v/'backlash.json')
 folder=HW/'generated/revO4/deliveries/o4_20260924_d1';folder.mkdir(parents=True,exist_ok=True)
 boards={x['kind']:x for x in data['boards']};a=boards['A_proximal5'];ad=boards['A_distal4'];c=boards['proximal5_rs485'];cd=boards['distal4_rs485_top'];pair={}
 for key in ('physical_dimensions_mm','R4_dimensions_mm','R12_dimensions_mm','with_service_dimensions_mm'):
  av=math.prod(a[key])+math.prod(ad[key]);cv=math.prod(c[key])+math.prod(cd[key]);pair[key]={'A_sum_bbox_mm3':av,'C_sum_bbox_mm3':cv,'change_percent':100*(cv/av-1)}
 data['two_PCB_bbox_sum_proxy']=pair
 names={'A_proximal5':'A 近端 / 14 芯','A_distal4':'A 远端 26×30','proximal5_rs485':'C 近端 / 四芯侧出线','distal4_rs485':'C 远端 26×30 / 侧出线','distal4_rs485_stretch':'C 远端 20×30 / 侧出线','distal4_rs485_top':'C 远端 20×30 / 顶出线'}
 fmt=lambda a:' × '.join(f'{x:.2f}' for x in a)
 table=''.join('<tr>'+''.join('<td>'+html.escape(str(x))+'</td>' for x in [names[q['kind']],fmt(q['pcb_mm']),q['components'],fmt(q['physical_dimensions_mm']),q['checks']['erc']['status'],'FAIL / '+str(q['checks']['drc']['unconnected_items'])])+'</tr>' for q in data['boards'])
 payload=json.dumps({'comparison':data,'electronics':e,'geometry':g,'backlash':b,'names':names},ensure_ascii=False).replace('</','<\\/')
 template=r'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>PoseDoll O4 · 静态采集硬件实验</title>
<style>body{font:16px/1.65 system-ui,sans-serif;background:#eff2f5;color:#182a36;max-width:1200px;margin:32px auto;padding:0 20px}h1{font-size:32px}h2{font-size:22px}.muted{color:#546774}section{background:white;border-radius:12px;padding:24px;margin:20px 0}.badge{display:inline-block;padding:4px 12px;background:#fff2ce;border-radius:20px}select{font:inherit;padding:8px;max-width:100%;margin:8px}table{border-collapse:collapse;width:100%;font-size:14px}th,td{border-bottom:1px solid #d6e0e7;text-align:left;padding:10px;white-space:nowrap}.scroll{overflow:auto}svg{background:#f7fafb;border:1px solid #dae3e8;width:100%;height:460px}#detail{white-space:pre-wrap;overflow-wrap:anywhere}a{color:#1762a2}.cards{display:grid;grid-template-columns:1fr 1fr;gap:20px}@media(max-width:750px){.cards{grid-template-columns:1fr}section{padding:15px}h1{font-size:26px}}</style>
<h1>PoseDoll O4 · 静态采集实验</h1><p>摆好再采集：UE 快照功能已完成模拟端到端验证。硬件方案进入对照试验，整机尚未放行。</p>
<span class="badge">实体测试 NOT_RUN · PCB 未布线 · 完整胸肩 / 单臂未建成</span>
<section><h2>14 芯与四芯：收益在哪</h2><p>只减少 J50 这一段，其他肩部传感器线保留。六个逻辑区域、七个 CAN 节点、41 个测量轴不变；新增两颗远端 MCU 后共九个处理器。</p><div class="scroll"><table id="boards"><thead><tr><th>板件</th><th>PCB mm</th><th>元件</th><th>含插头 / 代用体 mm</th><th>ERC</th><th>DRC / 未连线</th></tr></thead><tbody>__TABLE__</tbody></table></div></section>
<section><h2>原生布局与包络投影</h2><p class="muted">KiCad 元件轮廓和包络的平面投影，不是完整三维装配。黄色表示插头、弯线或拔插需求；蓝 / 红分别为正反面器件轮廓；虚线为缺少实体轮廓时的 courtyard，圆点只表示焊盘位置。R4 / R12 仅作敏感性比较，未验证线材弯曲寿命。</p>
<select id="board"></select><select id="mode"><option value="physical">实体及声明的代用包络</option><option value="4">加 R4 弯线</option><option value="12">加 R12 弯线</option><option value="service">加拔插空间</option></select>
<div class="cards"><svg id="drawing" viewBox="-15 -30 95 115" role="img" aria-label="原生布局和包络投影"></svg><div id="detail"></div></div></section>
<section><h2>时间与供电</h2><p>请求 68 B + 响应 80 B，在 115200 8N1 下仅串行发送需 12.847 ms。保留五项寄存器诊断，四轴读取加假定的 2 ms 调度 / 换向共约 17.527 ms；全 41 轴加两段串行链路保守相加约 57.164 ms。尚未包含 CAN、网关、USB 和操作系统延迟。</p><p>3.3 V 供电采用低端容差、线长、线径、温度和 100 / 200 / 250 mA 的敏感性计算。36 组中 4 组远端低于传感器 3.0 V 下限，最低约 2.951 V。100 kΩ 限流电阻的理论触发范围约 232–306 mA，250 mA 档还可能提前限流。四芯供电尚未合格。</p><p>降低采集频率不会自动让持续供电的磁编码器更省电。休眠、上电稳定时间和断电反灌须单独验证。</p></section>
<section><h2>整条手臂仍有什么缺口</h2><p>两角色各 24 个板件 / 弯线 / 位置筛查均存在包络或关节预留余量失败。这是采样包络筛查，不能替代真实胸肩和带线九轴单臂。四芯顶出线远端板更紧凑，但近端侧出线和拔插空间抵消了一部分收益。</p><p id="pair"></p><p>外耳止挡名义反向空程约 <strong>0.6504°</strong>，不是编码器误差。前截面槽角到外壁径向剩余约 0.6485 mm；加厚到半径 16 mm 可变为约 1.6485 mm，但不能据此判定中断螺纹强度通过。收紧配合可能引入公差干涉与受载卡滞；结合、输出夹持和完整反向扭矩链仍需验证。</p></section>
<section><h2>证据范围</h2><p>硬件输入：b2c54e3；新运行 o4_20260924_h3。原 O3、91 cm 备用和旧时序结论保留。PASS 只表示所注明的执行或局部检查范围，不代表制造放行。</p><p><a href="../../../../verification/revO4/runs/o4_20260924_h3/hardware_comparison.json">硬件原始比较</a> · <a href="../../../../verification/revO4/runs/o4_20260924_h3/run.json">运行与输入哈希</a> · <a href="../../../../docs/O4_DELIVERY.zh-CN.md">完整交付说明</a></p></section>
<script>const DATA=__PAYLOAD__;
const fmt=a=>a.map(x=>x.toFixed(2)).join(' × '),boards=DATA.comparison.boards;
for(const b of boards){const opt=document.createElement('option');opt.value=b.kind;opt.textContent=DATA.names[b.kind];document.querySelector('#board').append(opt)}
function render(){const kind=document.querySelector('#board').value,mode=document.querySelector('#mode').value,b=boards.find(x=>x.kind===kind),layout=DATA.electronics.boards.find(x=>x.kind===kind),geo=DATA.geometry.boards.find(x=>x.kind===kind);const svg=document.querySelector('#drawing');svg.replaceChildren();const visible=[];
function shape(tag,attrs){const el=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [k,v] of Object.entries(attrs))el.setAttribute(k,v);svg.append(el);return el}
for(const q of geo.objects){if(!(q.class.startsWith('physical')||(mode==='service'&&q.class==='service_sweep')||q.id.endsWith('_R'+mode)))continue;const a=q.bounds_mm;visible.push([a[0],-a[4],a[3],-a[1]]);shape('rect',{x:a[0],y:-a[4],width:a[3]-a[0],height:a[4]-a[1],fill:'#ffd56a',stroke:'#c28d22','stroke-width':.18,opacity:.23})}
shape('rect',{x:0,y:0,width:layout.board_mm[0],height:layout.board_mm[1],fill:'#e6f2e8',stroke:'#417955','stroke-width':.18,opacity:.6});
for(const c of layout.components){if(!c.fab_lines_xy_mm.length){const r=c.courtyard_xy_mm;shape('rect',{x:r[0],y:r[1],width:r[2]-r[0],height:r[3]-r[1],fill:'none',stroke:c.back?'#b35b69':'#236fab','stroke-width':.10,'stroke-dasharray':'.3 .2'})}for(const pad of c.pads)shape('circle',{cx:pad.x_mm,cy:pad.y_mm,r:.10,fill:'#9c7622'});for(const l of c.fab_lines_xy_mm)shape('line',{x1:l[0][0],y1:l[0][1],x2:l[1][0],y2:l[1][1],stroke:c.back?'#b35b69':'#236fab','stroke-width':.18});if(['J50','U60','U61','U62'].includes(c.ref))shape('text',{x:c.center_xy_mm[0],y:c.center_xy_mm[1],'font-size':1.8,fill:'#182a36'}).textContent=c.ref}
const left=Math.min(...visible.map(x=>x[0]))-3,top=Math.min(...visible.map(x=>x[1]))-3,right=Math.max(...visible.map(x=>x[2]))+3,bottom=Math.max(...visible.map(x=>x[3]))+3;svg.setAttribute('viewBox',[left,top,right-left,bottom-top].join(' '));
const dim=mode==='physical'?b.physical_dimensions_mm:mode==='service'?b.with_service_dimensions_mm:b['R'+mode+'_dimensions_mm'];
document.querySelector('#detail').textContent=DATA.names[kind]+'\nPCB：'+fmt(b.pcb_mm)+' mm\n本模式总包络：'+fmt(dim)+' mm\nJ50 配合壳宽：'+b.J50_mating_width_mm+' mm\n元件数：'+b.components+'\nDRC FAIL · 未布线 '+b.checks.drc.unconnected_items+' 项\n尚未完全确认的模型 / 配合：'+b.unqualified_models.join(', ')+'\nRF 功能禁布区仍需另行满足。';}
document.querySelector('#board').value='distal4_rs485_top';document.querySelector('#board').onchange=render;document.querySelector('#mode').onchange=render;render();
const q=DATA.comparison.two_PCB_bbox_sum_proxy;document.querySelector('#pair').textContent='近端 + 远端包围盒体积之和只是对照指标：实体与配合包络变化 '+q.physical_dimensions_mm.change_percent.toFixed(1)+'%，加 R4 弯线后变化 '+q.R4_dimensions_mm.change_percent.toFixed(1)+'%，加 R12 后变化 '+q.R12_dimensions_mm.change_percent.toFixed(1)+'%。它不是整条手臂的可用容积或干涉通过结果。';
window.REVIEW_READY=true;</script></html>'''
 (folder/'review.html').write_text(template.replace('__TABLE__',table).replace('__PAYLOAD__',payload),encoding='utf-8')
 proof=HW/'verification/revO4/deliveries/o4_20260924_d1'
 save(proof/'presentation.json',{'delivery_id':'o4_20260924_d1','consumed_inputs':[r.receipt() for r in readers.values()],'viewer_sha256':sha(folder/'review.html'),'pair_bbox_sum_proxy':pair,'scope':'PRESENTATION_ONLY_NOT_NEW_HARDWARE_PASS'})
 print(folder/'review.html');print(pair)
if __name__=='__main__':main()
