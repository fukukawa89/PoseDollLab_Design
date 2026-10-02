"""Package explicit first-batch gauges separately from later core references."""
from pathlib import Path
import json,zipfile,hashlib
H=Path(__file__).resolve().parents[3];G=H/'generated/revO8/runs/o8_20260925_r1';B=H/'bench/revO8';D=Path(__file__).resolve().parents[1]/'assets'
rootread='''# 首批只做 A_first_fit

A_first_fit 中 4 类文件：hole_gauge_Z 1 件、hole_gauge_Y 1 件、pin_D4 3 件、fastener_gauge 1 件，共 6 件。STL 与 STEP 是同一零件的两种格式，不要重复计数。单位 mm。

候选为同批未填充 PA12、SLS，不涂装、不润滑。先让打印方确认材料、孔径与方向要求并报价。B_core_reference 不计入首批订单。

另配 M1.6×6 / 0.35 螺距内六角圆柱头螺钉与 M1.6 六角螺母各 6 件、1.5 mm 内六角工具。实际规格要核对。它们是金属标准件，不是 3D 打印。

先拍照、记录批次与打印方向。从缺口端开始编号，用三根轴逐一轻试五个孔，记录进不去、卡、轻转、明显晃动。螺母既要能放入，也不能跟着螺钉空转。不要敲入、先打磨、先润滑或把试片结果当成整关节合格。

详细说明在 TEST_INSTRUCTIONS.zh-CN.md；有些来源链接指向设计仓库。measurement_template.json 为空白记录，不懂 JSON 时可直接用照片与文字回传。dimensions.svg 是按 CAD 参数绘制的识别图，不能打印后当量尺。

B_core_reference 是 O8 局部研究改型，包含两个各加长 2 mm 的叉架和上下半环；等待配合结果后再推进其制作。没有完整外接机构、PCB、线束或测矩夹具，没有实测承载与制造放行。
'''
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="720" viewBox="0 0 1000 720"><rect width="1000" height="720" fill="#fcfbf7"/><g font-family="Microsoft YaHei,sans-serif" fill="#253c34"><text x="40" y="48" font-size="26">O8 首批配合量规 · 单位 mm</text><text x="40" y="78" font-size="15">识别与名义尺寸；非比例尺。缺口端开始数孔，实际加工以 STEP / STL 为准。</text>']
svg.append('<text x="40" y="122" font-size="20">孔试片：Z / Y 方向各 1 件</text><rect x="55" y="160" width="640" height="140" rx="3" fill="#ded7c3" stroke="#6c7c6b"/><path d="M55 215h12v30H55" fill="#fcfbf7" stroke="#6c7c6b"/>')
for i,d in enumerate([4,4.2,4.4,4.6,4.8]):
 x=135+i*120;svg.append(f'<circle cx="{x}" cy="230" r="{d*5}" fill="#fcfbf7" stroke="#6c7c6b"/><text x="{x}" y="195" text-anchor="middle" font-size="16">{i+1}</text><text x="{x}" y="330" text-anchor="middle" font-size="18">Ø{d:g}</text>')
svg.append('<text x="725" y="195" font-size="17">64 × 14 × 6</text><text x="725" y="225" font-size="15">中心间距 12</text><text x="725" y="255" font-size="15">两端孔离端面 8</text><text x="40" y="395" font-size="20">螺钉 / 螺母试片：1 件</text><rect x="55" y="425" width="540" height="140" fill="#ded7c3" stroke="#6c7c6b"/><path d="M55 480h12v30H55" fill="#fcfbf7" stroke="#6c7c6b"/>')
for i,c in enumerate([0,.2,.4,.6]):
 x=145+i*120;svg.append(f'<circle cx="{x}" cy="495" r="{(4+c)*5}" fill="#eeeade" stroke="#6c7c6b"/><circle cx="{x}" cy="495" r="{(1.8+c)*5}" fill="#fcfbf7" stroke="#6c7c6b"/><text x="{x}" y="463" text-anchor="middle" font-size="15">{i+1}</text><text x="{x}" y="595" text-anchor="middle" font-size="15">孔 Ø{1.8+c:.1f}</text><text x="{x}" y="621" text-anchor="middle" font-size="15">槽 AF{3.3+c:.1f}</text>')
svg.append('<text x="645" y="430" font-size="20">打印轴：3 件</text><rect x="655" y="485" width="120" height="40" fill="#ded7c3" stroke="#6c7c6b"/><rect x="775" y="455" width="30" height="100" fill="#ded7c3" stroke="#6c7c6b"/><text x="650" y="587" font-size="16">直段 Ø4 × 长12</text><text x="650" y="615" font-size="16">圆柄 Ø10 × 厚3</text><text x="40" y="681" font-size="15">较大的螺母槽可能失去止转能力：能放进去，不等于能使用。没有预填实测值。</text></g></svg>')
(B/'dimensions.svg').write_text(''.join(svg),encoding='utf-8')
files={}
for p in sorted((B/'fit_gauges').iterdir()):
 if p.suffix in ('.stl','.step') or p.name=='manifest.json':files['A_first_fit/'+p.name]=p
for p in sorted((G/'fork_extension_2mm').iterdir()):
 if p.suffix=='.stl' or p.name=='manifest.json':files['B_core_reference/'+p.name]=p
files.update({'TEST_INSTRUCTIONS.zh-CN.md':B/'README.zh-CN.md','measurement_template.json':B/'measurement_template.json','dimensions.svg':B/'dimensions.svg'})
checks={n:hashlib.sha256(p.read_bytes()).hexdigest() for n,p in files.items()}
with zipfile.ZipFile(D/'o8-fit-handoff.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
 z.writestr('START_HERE.zh-CN.md',rootread);z.writestr('CHECKSUMS.json',json.dumps(checks,indent=2)+'\n')
 z.writestr('B_core_reference/SOURCE.md','Derived research geometry from https://github.com/oliglauser/atamid/tree/9a152b1d82374d1960ebd2216563fb30b1b6875b/Hardware/Mechanics . Original jointTUT.stl SHA256: 05bc819a65068a68afdb275a639b267ba840d8e2f574fd21368b655a3bf570e0 . Source license / production redistribution terms not verified. Four central parts only; fork stems extended 2 mm each. No physical performance or full assembly qualification.\n')
 for n,p in files.items():z.write(p,n)
with zipfile.ZipFile(D/'o8-fit-handoff.zip') as z:
 assert z.testzip() is None
 for n,d in checks.items():assert hashlib.sha256(z.read(n)).hexdigest()==d,n
print('Verified archive',len(files),'data files', (D/'o8-fit-handoff.zip').stat().st_size,'bytes')
