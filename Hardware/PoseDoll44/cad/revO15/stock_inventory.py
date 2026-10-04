from common import *
from layout_fullbody import build
from collections import Counter
_,m,st,f,_=build('quinn',{},geometry=False);count=Counter(v['sku'] for v in m.values() if v['sku'] and v['sku']!='PCBA_INCLUDED')
names={'SHOULDER_D4_L8_M3_L6':'轴肩螺钉：光杆 Φ4 × 8，M3×0.5 螺纹长 6 mm，头 Φ7×3，3 mm 内六角','W_M4_D12_T1':'M4 大垫圈，外径12、厚1 mm；到货验证能自由套过 Φ4 光杆','W_M4_D9_T0P8':'M4 普通平垫圈，外径9、厚0.8 mm；到货验证通孔','W_M3_D9_T0P8':'M3 大垫圈，外径9、厚0.8 mm；到货验证通孔','A8_SS':'A8 不锈钢碟簧，外径8、内径4.2、厚0.4、自由高0.6 mm；弹力尚未实测','MAGNET_D6_T2P5_DIAMETRIC':'Φ6 × 2.5 mm 径向两极磁铁（直径方向充磁），禁止用轴向充磁替代','AS5048A_MINI_PCBA':'传感小板 Rev C mini，12 × 10 × 1 mm；电路加工件，非金属标准件'}
rows=[]
for sku,n in sorted(count.items()):
 if sku.startswith('NUT_'):name=sku.removeprefix('NUT_').replace('P','.')+' 普通六角螺母'
 elif sku.startswith('SCREW_'):
  size,length=sku.removeprefix('SCREW_').split('_L');name=size.replace('P','.')+' × '+length+' 内六角圆柱头螺钉；需核对头部/内六角尺寸'
 else:name=names.get(sku,sku)
 rows.append({'sku':sku,'name_zh':name,'net_quantity':n,'provisional_spares_quantity':max(2,math.ceil(n*.1)),'scope':'Current mechanical modules only; harness/controller/end fixtures not counted.'})
BENCH.mkdir(parents=True,exist_ok=True);(BENCH/'metal_and_sensor_inventory_draft.json').write_text(json.dumps({'status':'DRAFT_DO_NOT_ORDER_YET','rows':rows,'assumptions':['User O12 received stock usable for conditional design.','No new physical validation.','Do not purchase from this interim list; final combined batch is pending.'],'module_sources_sha256':{p.name:sha(p) for p in OUT.glob('*_parts.npz')},'layout_source_sha256':sha(Path(__file__).with_name('layout_fullbody.py'))},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for r in rows:print(r['sku'],r['net_quantity'],flush=True)
