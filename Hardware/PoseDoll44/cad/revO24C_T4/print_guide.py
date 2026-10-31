from arm_kit import *
from publish import page
import html

def main():
 plate=json.loads((OUT/'printing/combined_plate.json').read_text('utf8'))['plates'][0]
 items=plate['items'];svg='<svg xmlns="http://www.w3.org/2000/svg" width="720" height="760" viewBox="0 0 720 760"><rect width="720" height="760" fill="#f4f6ef"/><text x="24" y="30" font-family="sans-serif" font-size="20" fill="#213d37">T4 · H / R / W · 17 件 / 1 盘</text><rect x="24" y="48" width="672" height="672" fill="#e0e5dc" stroke="#82998c"/>'
 for item in items:
  x,y,z,X,Y,Z=item['bounds_mm'];scale=672/180;px=24+x*scale;py=48+(180-Y)*scale;w=(X-x)*scale;h=(Y-y)*scale
  color='#d18e5d' if item['id'].startswith('H') else '#70a6a0' if item['id'].startswith('R') else '#809fc4' if item['id'].startswith('W') else '#c9b76b'
  svg+=f'<rect x="{px:.2f}" y="{py:.2f}" width="{w:.2f}" height="{h:.2f}" rx="3" fill="{color}" stroke="#455e58"/><text x="{px+w/2:.2f}" y="{py+h/2+4:.2f}" text-anchor="middle" font-family="sans-serif" font-size="13" fill="#162c26">{item["id"]}</text>'
 svg+='<text x="24" y="746" font-family="sans-serif" font-size="14" fill="#435d55">外框 180×180 mm · 矩形是零件外廓，非实际形状 · 仅用于辨认</text></svg>'
 (OUT/'printing/ALL_H_R_W_T4_layout.svg').write_text(svg,encoding='utf8')
 rows={r['id']:r for r in json.loads((OUT/'assembly.json').read_text('utf8'))['parts']}
 table='<table><tr><th>零件</th><th>作用</th><th>数量</th></tr>'+''.join('<tr><td>'+i['id']+'</td><td>'+html.escape(rows[i['id']]['label'])+'</td><td>1</td></tr>' for i in sorted(items,key=lambda i:i['id']))+'</table>'
 content='<h1>三个样件，合成一个打印文件</h1><p><a class="button" href="printing/ALL_H_R_W_T4.3mf">下载 ALL_H_R_W_T4.3mf</a></p><p>一个 A1 mini 180×180 mm 打印盘，含 12 个实际关节件、4 个可拆测试附件、1 个可选 C3-01 试配片，共 17 件，各一件。H、R 沿用 T3，W 为 T4 双轴腕。若已打印这些同版本零件，本次无需重印。</p><p>工程中的 17 个对象仍彼此独立，可以按编号隐藏或删除已有件；没有把它们焊成一个不可拆的 STL。原打印接触面保持不变，仅作盘面内旋转与平移。</p><img style="max-width:100%" src="printing/ALL_H_R_W_T4_layout.svg" alt="17 件单盘位置编号图"><h2>打开后确认</h2><ol><li>使用 OrcaSlicer / Bambu Studio 打开整个 3MF 工程，保留工程参数，不要只导入模型。默认 A1 mini、0.4 mm 喷嘴、PLA、0.12 mm 层高、5 道墙、100% 填充、自动支撑、3 mm 裙边。</li><li>对象列表应有 17 个名称。不要自动翻转零件来改变受力与摩擦面方向；若手动重排，切片后复查边缘及支撑。</li><li>第一次使用该材料 / 打印机，仍建议先用 C3-01 试配。可以在同一工程中只启用该对象；确认配合后再启用其余对象。文件只有一个，不等于必须跳过试配或强行一次打印完。</li><li>清支撑后按上图和下表辨认。两组叉、十字芯和 H/R 各件不能仅凭相似外形互换；教程右侧有每件放大图。</li></ol><h2>已做的检查</h2><p>离线切片已核对 17 个对象、零网格修复、未改变摆放，所有层的模型 / 支撑 / 裙边挤出路径在 180 mm 范围内。数字检查不等于已试打，也没有向打印机发送任务。工程不附机器可直接执行的 G-code。</p>'+table+'<p><a href="START_HERE.html">单件或分盘补打入口</a> · <a href="tutorial/index.html">逐件装配动画</a> · <a href="verification/combined_printing.json">合盘切片检查报告</a></p>'
 (OUT/'ONE_PRINT.html').write_text(page('T4 三样件一盘打印',content),encoding='utf8')
 print('PRINT GUIDE ready')

if __name__=='__main__':main()
