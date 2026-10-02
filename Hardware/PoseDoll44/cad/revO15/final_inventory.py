"""Consolidated prototype procurement, directly counted from final retained parts."""
from common import *
from fitted import build_fitted
from collections import Counter

NAMES={'SHOULDER_D4_L8_M3_L6':'轴肩螺钉 Φ4×8 / M3×0.5，螺纹长6 mm；头Φ7×3，内六角3 mm','W_M4_D12_T1':'M4大平垫圈：外径12、厚1 mm，实物能自由套过Φ4光杆','W_M4_D9_T0P8':'M4普通平垫圈：外径9、厚0.8 mm，实物通孔验证','W_M3_D9_T0P8':'M3大平垫圈：外径9、厚0.8 mm，实物通孔验证','A8_SS':'A8不锈钢碟簧：8×4.2×0.4，自由高0.6 mm，弹力待测','MAGNET_D6_T2P5_DIAMETRIC':'径向两极磁铁 Φ6×2.5 mm；直径方向充磁，不能买轴向充磁','AS5048A_MINI_PCBA':'Rev C mini传感PCBA：12×10×1 mm，按配套电路文件加工','C1_CENTRAL_PCBA':'O15 C1中央采集PCBA：70×60×1.2 mm，四层板，按配套电路文件加工','XIAO_ESP32S3':'Seeed XIAO ESP32S3 普通版；人偶BODY和桌面G0各一块','POLOLU_D24V22F3':'Pololu D24V22F3 固定3.3V降压模块；禁止买F5版本','NITECORE_CARBON_6K':'Nitecore Carbon Battery 6K，5V输出，包络Φ22.8×90.4 mm','SEEED_FPC_A02_65MM':'XIAO配套A-02 2.4GHz FPC天线，37.4×17.5 mm，65 mm同轴线','HEADER_1X7_P2P54':'1×7、2.54 mm排针；XIAO与载板间距4.0 mm定位焊接','USB_C_5V_RIGHTANGLE_CABLE':'5V USB-C弯头电源线；电池端伸出≤16 mm、外包络8×8 mm，进盒PH2','JST_GH_6P_MATE':'JST GHR-06V-S壳+SSHL-002T-P0.2端子；26AWG短引线转24AWG，绝缘外径0.76–1.0 mm，6P、1.25 mm；让线束厂压接','JST_PH_2P_MATE':'JST PHR-2壳+SPH-002T-P0.5S端子，2P、2.0 mm；5V输入','JST_PH_3P_MATE':'JST PHR-3壳+SPH-002T-P0.5S端子，3P、2.0 mm；降压模块连接','FFC_6P_0P5_T0P2_L15':'6P 0.5mm FFC短尾线，宽3.5、厚0.2、长15 mm；每端补强≥3.5 mm，按图加六根32AWG短引线'}

def name(s):
 if s.startswith('NUT_'):return s[4:].replace('P','.')+'普通六角螺母（不要锁紧螺母替代外形）'
 if s.startswith('SCREW_'):
  a,l=s[6:].split('_L');return a.replace('P','.')+'×'+l+' 内六角圆柱头螺钉；按CAD头径/头高核对'
 return NAMES.get(s,s)

def main():
 report=[];fixtures=read(OUT/'fixtures.json');extras=Counter(v for v in fixtures['sku'].values() if v)
 for char in ('quinn','manny'):
  p,m,*_=build_fitted(char);count=Counter(v['sku'] for v in m.values() if v['sku'] and not v['sku'].endswith('_INCLUDED'));count.update(extras);rows=[]
  for sku,n in sorted(count.items()):
   typ='电子/线束' if sku in NAMES and not sku.startswith(('SHOULDER','W_','A8','MAGNET')) else '金属/磁铁标准件'
   spares=max(2,math.ceil(n*.1)) if typ=='金属/磁铁标准件' else 2 if sku=='AS5048A_MINI_PCBA' else 4 if sku.startswith('FFC') else 0
   rows.append({'sku':sku,'name_zh':name(sku),'category':typ,'net_quantity':n,'optional_spares':spares,'suggested_total':n+spares})
  report.append({'character':char,'rows':rows})
 d={'status':'ONE_BATCH_PROTOTYPE_PROCUREMENT','default_character':'quinn','choose_one_character_only':True,'characters':report,'not_included_in_counted_cad':['24AWG红黑电源线与30AWG信号线，逐段长度见harness/cut_and_binding_plan.json；32AWG局部短引线','热缩管、柔软可重复扎带/绑线带、标签；不在活动铰接缝内捆扎','USB数据线（G0到电脑），1.5/2/2.5/3 mm内六角扳手（M1.6螺钉另核对1.5mm或1.3mm）、小尖嘴钳','游标卡尺、万用表、弹簧秤/行李秤；示波器和电源测试可委托装配厂','工厂线束焊接、PCBA焊接和通断测试服务'],'metal_custom_machining_required':False,'source_sha256':{str(q):sha(q) for q in [Path(__file__),Path(__file__).with_name('fitted.py'),OUT/'fixtures.json',OUT/'fixtures.npz']},'physical_tested':False}
 save('procurement.json',d);(BENCH/'procurement.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print([(r['character'],len(r['rows']),sum(x['net_quantity'] for x in r['rows'])) for r in report])
if __name__=='__main__':main()
