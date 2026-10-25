"""Compare frozen T3/T4 BOMs against early O22 and T1-S2, not actual stock."""
from arm_kit import *
from publish import page
from html import escape as esc

def main():
 sources={'early_O22':H/'bench/revO22/procurement.json','T1_S2':H/'bench/revO24C_T1/BOM.json','T3':H/'bench/revO24C_T3/BOM.json','T4':OUT/'BOM.json'}
 old=json.loads(sources['early_O22'].read_text('utf8'))['characters'][0]['rows']
 t1=json.loads(sources['T1_S2'].read_text('utf8'))
 aliases={'A8_SS':'A8','NUT_M2':'N2','NUT_M3':'N3','SHOULDER_D4_L8_M3_L6':'AX4','W_M3_D9_T0P8':'RW3','W_M4_D12_T1':'FW4','W_M4_D9_T0P8':'W4'}
 def canonical(s):
  if s.startswith('SCREW_M'):
   m,l=s.removeprefix('SCREW_').split('_L');return m+'x'+l
  return aliases.get(s,s)
 o22={canonical(r['sku']):r['net_quantity'] for r in old};t1q={('FW4' if r['sku']=='FR4' else r['sku']):r['qty'] for r in t1}
 boms={k:{r['sku']:r for r in json.loads(sources[k].read_text('utf8'))} for k in ['T3','T4']}
 rows=[]
 for s in sorted(boms['T3'].keys()|boms['T4'].keys()):
  baseline=max(o22.get(s,0),t1q.get(s,0))
  row=dict(sku=s,spec=(boms['T4'].get(s) or boms['T3'][s])['spec'],early_O22_min=o22.get(s,0),T1_S2_min=t1q.get(s,0),conservative_owned_min=baseline,new_type=baseline==0)
  for k in ['T3','T4']:
   row[k+'_need']=boms[k].get(s,{}).get('qty',0);row[k+'_conditional_topup']=max(0,row[k+'_need']-baseline)
  rows.append(row)
 assert {r['sku'] for r in rows if r['new_type'] and r['T4_need']}=={'M2x12','M2x16','M3x18','M3x20'}
 assert {r['sku'] for r in rows if r['new_type'] and r['T3_need']}=={'M2x12','M2x6','M3x18','M3x20','M4x35','N4'}
 assumptions=['两列为替代套件，均含 H、R、W 和各自测试附件，不相加。','用户确认已购型号，不代表剩余库存；最低数量按早期 O22 与 T1-S2 两份 BOM 的较大值计算，不假定重复购买。','数量差额仅在旧件可拆回、且只买了最低数量时成立；散装余量可抵扣。若保留旧人偶/样件不拆，请按本版总需求减实际空闲库存。','T1-S2 结构更新未更换五金；采用已确认的 M2 平垫厚 0.5 mm、M6 大平垫厚 1.5 mm。','早期 O22 的 M2×6 自攻螺钉不能充当本次 M2×6 机螺钉；未将后期 F7 增加的机螺钉算作已购。']
 report=dict(revision=REVISION,rows=rows,assumptions=assumptions,sources={k:dict(path=v.relative_to(ROOT).as_posix(),sha256=sha(v)) for k,v in sources.items()})
 put(OUT/'purchase_from_owned.json',report)
 def table(selected,full=False):
  head='<tr><th>型号 / 参数</th>' + ('<th>早期 O22</th><th>T1-S2</th>' if full else '')+'<th>T3 总用量</th><th>T4 总用量</th><th>性质 / 补齐说明</th></tr>'
  body=''
  for r in selected:
   note='新增型号' if r['new_type'] else ('已有型号；按最低采购量：T3 补 '+str(r['T3_conditional_topup'])+'、T4 补 '+str(r['T4_conditional_topup']) if r['T3_conditional_topup'] or r['T4_conditional_topup'] else '已有型号；最低采购量足够复用')
   body+='<tr><td><b>'+esc(r['sku'])+'</b><br>'+esc(r['spec'])+'</td>'+(''.join('<td>'+str(r[k])+'</td>' for k in ['early_O22_min','T1_S2_min']) if full else '')+''.join('<td>'+str(r[k])+'</td>' for k in ['T3_need','T4_need'])+'<td>'+note+'</td></tr>'
  return '<div style="overflow:auto"><table>'+head+body+'</table></div>'
 new=[r for r in rows if r['new_type']];top=[r for r in rows if not r['new_type'] and (r['T3_conditional_topup'] or r['T4_conditional_topup'])]
 body='<h1>已买齐 O22 + T1-S2，还要买什么？</h1><p>按早期 O22 和 T1-S2 的清单核对。<strong>当前推荐装配的是 T4：H3 肘、R3 前臂旋转、W4 双轴腕。</strong>T3 球面腕作为对照，两个版本的数量不要相加。</p>'
 body+='<h2>新增型号</h2>'+table(new)+'<p>T4 新型号共 9 件：M2×12 两颗、M2×16 四颗、M3×18 一颗、M3×20 两颗。上表为净用量，未加备用数量。</p>'
 body+='<h2>已有型号，也要清点数量</h2>'+table(top)+'<p>如果当时仅买了 T1 的最低数量，T4 还需补 M2×14 一颗、5×2.2×0.5 mm 平垫三片。手头有多余的就不用买。O22 的轴肩螺钉、A8 碟簧和三种大垫圈均可复用。</p>'
 body+='<h2>下单时核对的尺寸</h2><ul><li>螺钉均为金属机螺钉、圆柱头内六角，标注长度从头下量到末端，不含头。不要买沉头、盘头或自攻螺钉来代替。</li><li>M2：螺距 0.4 mm；模型头部包络 Φ3.8×2 mm，内六角 1.5 mm。新增长度 T3 为 6、12 mm，T4 为 12、16 mm。</li><li>M3：螺距 0.5 mm；模型头部包络 Φ5.5×3 mm，内六角 2.5 mm；新增长度 18、20 mm。M3×20 两颗分别用于 R 测力杆和 W 前臂夹持接口。</li><li>仅 T3：M4×35，螺距 0.7 mm；头 Φ7×4 mm，内六角 3 mm。普通 M4 螺母对边 7、高 3.2 mm、无塑料圈；T1 的 NL4 尼龙锁紧螺母不等同于它。</li><li>复用 O22 肩钉：光杆 Φ4×8，M3×0.5 螺纹长 6，头 Φ7×3，内六角 3 mm。复用 A8：外径 8、内径 4.2、厚 0.4、单片自由高约 0.6 mm。</li><li>T4 全部使用普通 M2 / M3 螺母，无尼龙圈。平垫 5×2.2×0.5、7×3.2×0.5、9×3.2×0.8、9×4.3×0.8、12×4.3×1.0 的孔径和厚度不能混淆。</li></ul><p>上述头部尺寸是现有设计采用的包络；购买时核对卖家尺寸图。已经拥有的 M3×35 不是 M4×35，也不要把长螺钉直接塞进要求短螺钉的位置。</p>'
 body+='<h2>完整复用对照</h2>'+table(rows,True)+'<h2>数量的前提</h2><ul>'+''.join('<li>'+esc(s)+'</li>' for s in assumptions)+'</ul><p><a href="purchase_from_owned.json">可核对的原始对照与来源哈希</a> · <a href="BOM.csv">T4 全量 BOM</a> · <a href="tutorial/index.html">逐件动画教程</a></p>'
 body+='<p><a href="HARDWARE_T3_T4.html">另看：T3 腕到 T4 腕自身的数量变化（不是本次补购基准）</a></p>'
 for filename in ['PURCHASE_FROM_OWNED.html','HARDWARE.html']:(OUT/filename).write_text(page('O22 + T1-S2 → T3 / T4 补购清单',body),encoding='utf8')
 put(OUT/'verification/purchase.json',dict(passed=True,sources=report['sources'],T4_new_types=4,T4_new_type_pieces=9,T4_conditional_existing_topup={'M2x14':1,'W2':3},actual_stock_verified=False))
 print('PURCHASE: four new T4 types, nine pieces; existing minimum top-up 1 screw + 3 washers')

if __name__=='__main__':main()
