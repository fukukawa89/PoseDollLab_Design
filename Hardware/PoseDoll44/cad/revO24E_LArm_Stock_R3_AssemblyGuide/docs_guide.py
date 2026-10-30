from build_guide import *
import html
esc=html.escape
def main():
 d=load(DEST/'steps.json');P={p['id']:p for p in d['parts']};report=load(DEST/'verification/assembly_paths.json');chunks=[]
 for c in d['chapters']:
  cards=[]
  for i in c['step_indices']:
   s=d['steps'][i];pp=[x for x in s['parts'] if P[x]['kind']=='打印件'];mm=[x for x in s['parts'] if P[x]['kind']=='五金'];rows=[]
   for n in s['parts']:rows.append(f'<tr><td>{esc(n)}<br>{esc(P[n]["kind"])} · {esc(P[n]["sku"] or P[n]["label"])}</td><td>{esc(P[n]["orientation"])}</td></tr>')
   body=f'<p><b>操作：</b>{esc(s["note"])}</p><p><b>固定／接收打印件：</b>{esc(s["target"])} — {esc(s["printed_direction"])}</p><p><b>本步：</b>{len(pp)}件打印件，{len(mm)}件五金；'+('属于已装总成，保持组装状态。' if not s['new_parts'] else '首次取用：'+', '.join(s['new_parts']))+'</p>'
   body+='<details><summary>逐件方向（含已预装总成）</summary><table><thead><tr><th>件号／类型</th><th>朝向与识别方法</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table></details>'
   cards.append(f'<article id="step-{s["number"]}"><div class="cardhead"><h3>{s["number"]:03d} · {esc(s["title"])}</h3><a href="index.html?step={s["number"]}">播放这一步 ↗</a></div>{body}</article>')
  chunks.append(f'<section><h2>{esc(c["label"])}</h2>'+''.join(cards)+'</section>')
 doc='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>R3 单臂 · 156步安装卡</title><style>body{max-width:1080px;margin:35px auto;padding:0 24px;background:#f4f7f2;color:#193c38;font:14px/1.75 "Microsoft YaHei",sans-serif}a{color:#141b73}h1{font-size:28px}h2{padding-top:24px;border-bottom:1px solid #c7d8ce}h3{font-size:16px;margin:0}.intro,article{background:#fff;border:1px solid #d7e1d8;border-radius:8px;padding:18px 24px;margin-bottom:14px}.cardhead{display:flex;justify-content:space-between;gap:15px}p{margin:8px 0}table{border-collapse:collapse;width:100%;margin-top:12px}td,th{border:1px solid #d5e0d5;text-align:left;padding:8px}td:first-child{width:250px}summary{cursor:pointer;color:#266853}.nav{display:flex;gap:16px;flex-wrap:wrap}small{color:#5f786f}@media print{article{break-inside:avoid}details{display:block}a{color:inherit;text-decoration:none}}@media(max-width:600px){.cardhead{display:block}body{padding:0 12px}article{padding:15px}}</style><body><nav class="nav"><a href="index.html">返回动画教程</a><a href="verification/assembly_paths.json">路径与方向验证</a><a href="verification/browser_review.json">浏览器验证</a></nav><h1>R3 单臂 · 逐步安装卡</h1><div class="intro"><b>6章 · 156步 · 11个打印件＋130件五金</b><p>前三章分别在台面组装，随后连接肩、肘、双轴腕与手掌。压盖先装两颗锁母再合盖；腕中心先装齐四侧内五金再合叉。</p><p>每一步的动画链接都会直接定位；动画页右侧可以逐件查看打印件端口、尼龙端、螺纹端和碟簧凸缘。平垫明确标注两面等效。</p><small>文件使用冻结R3生产几何。动画演示名义路径，不替代实物配合、预紧力与强度验收；不要求重新验收已接受的T6 H/W才开始。本教程不安装电子件。</small></div>'''+''.join(chunks)+'</body></html>'
 (DEST/'STEP_CARDS.html').write_text(doc,encoding='utf8')
 (DEST/'README.txt').write_text('O24E R3 单臂独立逐步安装动画\n打开 index.html 即可离线使用，不需要联网；解压后请保持同目录文件完整。\n6章，156步；11个打印件、130件五金。\n支持单步播放/暂停/重播、拖动进度、连续播放、0.5~2倍速、旋转视角、固定打印件显示半剖，以及当前件独立放大。\n全部文字步骤见 STEP_CARDS.html。每个链接可直接定位对应动画步骤。\n压盖锁母分别装入；腕中心件在前臂叉外预装四侧五金；碟簧凸缘箭头由R3网格计算，并附夸张剖面方向示意。\n此包只提供教程，不替换R3生产STL或3MF。原R3模型/打印包均保持不变。\nverification含逐步路径和方向审查；几何演示不等于实装力或材料/疲劳验证。\n源码在source；重建需原仓库冻结R3输入，依次 build_guide.py、verify_guide.py、docs_guide.py，浏览器核对后 package_guide.py。\n',encoding='utf8')
 print('CARDS',len(d['steps']),'checked path samples',report['total_samples'],flush=True)
if __name__=='__main__':main()
