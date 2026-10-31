"""Compare the T1 hardware BOM with the latest O22F7 purchasing baseline.

Quantities describe one H/R/W kit without spares, not the owner's inventory.
No geometry or manufacturing files are regenerated here.
"""
from pathlib import Path
import csv
import hashlib
import json

H = Path(__file__).resolve().parents[2]
OUT = H / 'bench/revO24C_T1'
BASE = H / 'bench/revO22/O22F7_PLA_AssemblyRevision/五金采购清单.csv'
REUSE = {
    'W4': 'W_M4_D9_T0P8', 'FR4': 'W_M4_D12_T1',
    'N3': 'NUT_M3', 'N2': 'NUT_M2',
    'M2x8': 'SCREW_M2_L8', 'M2x20': 'SCREW_M2_L20',
}
# Dimensions below are the actual T1 purchase envelope. AF = across flats.
DETAILS = {
    'B4': ('684ZZ 微型深沟球轴承', '内径4×外径9×宽4；双面金属防尘盖；无凸缘', '轴承钢；不要买宽2.5的684开式或带法兰版本'),
    'B6': ('MR126ZZ 微型深沟球轴承', '内径6×外径12×宽4；双面金属防尘盖；无凸缘', '轴承钢；不要买宽3的MR126开式或带法兰版本'),
    'SHAFT4': ('D4×45 精磨实心光轴', '直径4、长度45；与684ZZ内圈实配', '推荐304不锈钢精磨件；两端去毛刺；可由精磨长轴切至45±0.1；验收见说明'),
    'SHAFT6': ('D6×45 精磨实心光轴', '直径6、长度45；与MR126ZZ内圈实配', '推荐304不锈钢精磨件；两端去毛刺；可由精磨长轴切至45±0.1；验收见说明'),
    'GUIDE_M2_D2P5_L6': ('S1腕部导向轴肩螺钉', '肩径2.5、肩长6、M2×0.4螺纹长4、头径4.8×头高2.4、内六角2', '按用户天卓五金商品图片，304；用于S1六件新版腕部打印件，不直接装入旧T1；仍需低强度可拆金属螺纹锁固'),
    'M2x14': ('M2×14 内六角圆柱头螺钉', '螺距0.4；头下长14；头径3.8×头高2；内六角1.5', 'DIN 912 / ISO 4762外形；推荐A2不锈钢'),
    'M3x10': ('M3×10 内六角圆柱头螺钉', '螺距0.5；头下长10；头径5.5×头高3；内六角2.5', 'DIN 912 / ISO 4762外形；推荐A2不锈钢'),
    'M3x12': ('M3×12 内六角圆柱头螺钉', '螺距0.5；头下长12；头径5.5×头高3；内六角2.5', 'DIN 912 / ISO 4762外形；推荐A2不锈钢'),
    'M3x30': ('M3×30 内六角圆柱头螺钉', '螺距0.5；头下长30；头径5.5×头高3；内六角2.5', 'DIN 912 / ISO 4762外形；推荐A2不锈钢'),
    'M3x35': ('M3×35 内六角圆柱头螺钉', '螺距0.5；头下长35；头径5.5×头高3；内六角2.5', 'DIN 912 / ISO 4762外形；推荐A2不锈钢'),
    'M4x60': ('M4×60 内六角圆柱头螺钉', '螺距0.7；头下长60；头径7×头高4；内六角3', 'DIN 912 / ISO 4762外形；推荐A2不锈钢'),
    'NL2': ('M2 尼龙圈六角锁紧螺母', '螺距0.4；对边AF4；总高≤3', '非普通螺母；非加高型；推荐A2不锈钢，尺寸以实物为准'),
    'NL3': ('M3 尼龙圈六角锁紧螺母', '螺距0.5；对边AF5.5；总高≤4', '非普通螺母；非加高型；推荐A2不锈钢，尺寸以实物为准'),
    'NL4': ('M4 尼龙圈六角锁紧螺母', '螺距0.7；对边AF7；总高≤5', '非普通螺母；非加高型；推荐A2不锈钢，尺寸以实物为准'),
    'W2': ('M2 平垫圈', '外径5×内径2.2×厚0.5', 'S1总计8片；导向座2片必须0.5厚，其余6片允许原0.3；304、平整去毛刺，先试配肩部倒角'),
    'W3': ('M3 平垫圈', '外径7×内径3.2×厚0.5', '推荐304不锈钢；不是O22的外径9、厚0.8版本'),
    'FR6': ('M6 大平垫圈／摩擦垫片', '外径18×内径6.4×厚1.5；原1.6也可用', '优先采购1.5；两片同厚；304不锈钢、平整光滑去毛刺；无须重印，见替代说明'),
    'W4': ('M4 平垫圈', '外径9×内径4.3×厚0.8', '核对旧件内径、厚度与平整度'),
    'FR4': ('M4 大平垫圈／摩擦垫片', '外径12×内径4.3×厚1', '核对旧件内径；不锈钢、平整光滑去毛刺'),
    'N3': ('M3 普通六角螺母', '螺距0.5；对边AF5.5×高2.4；DIN 934', '可沿用O22普通螺母；不替代NL3'),
    'N2': ('M2 普通六角螺母', '螺距0.4；对边AF4×高1.6；DIN 934', '已修正T1旧清单的薄螺母误称；不替代NL2'),
    'M2x8': ('M2×8 内六角圆柱头螺钉', '螺距0.4；头下长8；头径3.8×头高2；内六角1.5', '可沿用O22同规格件'),
    'M2x20': ('M2×20 内六角圆柱头螺钉', '螺距0.4；头下长20；头径3.8×头高2；内六角1.5', '可沿用O22同规格件'),
}

def main():
    bom = {r['sku']: r for r in json.loads((OUT / 'BOM.json').read_text('utf8'))}
    with BASE.open(encoding='utf-8-sig', newline='') as f:
        old = {r['型号']: r for r in csv.DictReader(f)}
    assert set(DETAILS) == set(bom)
    assert set(REUSE.values()) <= set(old)
    rows = []
    for sku, (name, spec, note) in DETAILS.items():
        b = bom[sku]
        rows.append(['可复用' if sku in REUSE else '新增规格', sku, name, spec,
                     b['qty'], ','.join(b['stations']), REUSE.get(sku, ''), note])
    new = [r for r in rows if r[0] == '新增规格']
    reused = [r for r in rows if r[0] == '可复用']
    with (OUT / 'PURCHASE_DELTA_O22.csv').open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['对比分类', 'T1编号', '名称', '采购参数_mm', '一套净用量_不含备件', '站位', 'O22对应编号', '备注'])
        w.writerows(rows)
    text = '''# O24C-T1 对比 O22：五金补购参数

对比依据是仓库 O22F7 装配修订版的 `五金采购清单.csv`，路径为 `bench/revO22/O22F7_PLA_AssemblyRevision/五金采购清单.csv`，以及本目录的 [T1 完整 BOM](BOM.csv)。这不是对用户实际库存的盘点；同规格旧件需要有余量且状态良好才能抵扣购买数量。

范围：H 肩/肘单轴测试站、R 前臂扭转测试站、W 球面腕测试站，各一套。不是整只人偶或整条手臂的采购数量。所有数量为装机净用量，不含备用。

全部尺寸为 mm。螺钉长度指头下长度；垫圈写作外径×内径×厚度；轴承写作内径×外径×宽度；AF 指六角对边宽度。新增规格也包括同类螺钉的不同长度。

2026-10-22 **S1现货适配版**：腕部已按用户图片的D2.5×6/M2螺纹长4肩螺钉修改，停止采购原D3/M2特殊目录规格。球半体、衬片及球窝共6件必须采用新版。M2垫圈总数从6增至8，新增两片导向座必须厚0.5；其余6片可用0.5或原0.3。M6大垫圈仍允许1.5或1.6、两片同厚。详见 [S1五金与打印件变更](HARDWARE_ALTERNATIVES.html)。

'''
    text += f'**新增 {len(new)} 项规格，共 {sum(r[4] for r in new)} 件；可复用 {len(reused)} 项规格，共 {sum(r[4] for r in reused)} 件。整套共 {len(rows)} 项规格、{sum(r[4] for r in rows)} 件五金。**\n\n'
    for title, group in [('需要补购的新增规格', new), ('O22 同规格件可复用', reused)]:
        text += '## ' + title + '\n\n| 零件 | 采购参数（mm） | 净数量 | 说明 |\n|---|---|---:|---|\n'
        for r in group:
            note = r[7] + ('；O22编号：' + r[6] if r[6] else '')
            text += f'| {r[2]}（{r[1]}） | {r[3]} | {r[4]} | {note} |\n'
        text += '\n'
    text += '''## 下单时的关键核对

1. **腕部轴肩螺钉按用户图片的全部尺寸购买。** S1为D2.5肩×6长、M2×0.4螺纹长4、头D4.8×2.4、内六角2、304不锈钢，2件。头下总长为10，不是6。原Accu D3/M2型号属于厂家标注Not Standardised的目录规格，已取消采购要求。D3/M2.5、O22的D4/M3、普通M2×6全牙螺钉均不是本版替代件。导向螺钉仍需低强度、可拆卸金属螺纹锁固处理（耗材不计入17项五金）；按产品说明核对不锈钢适用性和固化要求，只施于啮合金属牙，禁止接触PLA球面、垫圈座和导向槽。见装配手册的先试配、后锁固步骤。
2. **轴承买双面金属防尘盖 ZZ、无凸缘版本。** 684ZZ为4×9×4，MR126ZZ为6×12×4；原厂尺寸依据：[684ZZ 数据表](https://www.smbbearings.com/firebrick/ckeditor/plugins/upload/Uploads/Documents/bearingpdfs/684ZZ-miniature-bearing-4x9x4mm.pdf)、[MR126ZZ 数据表](https://www.smbbearings.com/firebrick/ckeditor/plugins/upload/Uploads/Documents/bearingpdfs/MR126ZZ-miniature-bearing-6x12x4mm.pdf)。两款都采购普通轴承钢版本即可；保留轴承内部润滑脂。装配手册的干摩擦要求针对打印件与摩擦垫片接触面，不是让轴承脱脂。
3. **光轴需要与所买轴承实配。** D4×45和D6×45是CAD名义尺寸。补充采购建议为304不锈钢精磨光轴，长度45±0.1，两端小倒角去毛刺；向卖家要求能用手推入对应轴承内圈、无明显径向晃动的小间隙配合。不要直接把公称D4/D6的普通圆棒或正公差定位销当成精磨轴。只标直径而不说明公差的商品，应由卖家确认配合，收货后先试轴承与轴，不靠打印件夹紧力或锤击强行装配。材料与长度公差是此次补充的采购建议，尚未做实物寿命验证。
4. **普通螺钉选内六角圆柱头。** M2螺距0.4、头D3.8×2；M3螺距0.5、头D5.5×3；M4螺距0.7、头D7×4。这是T1使用的名义外形，按DIN 912 / ISO 4762对应商品核对，不换沉头、盘头或法兰头。螺钉必须完整穿过尼龙圈；各装配位置和长度核对见装配手册。
5. **尼龙锁紧螺母与普通螺母是不同项目。** 锁紧螺母按表中对边及总高采购，含尼龙圈也不能超过所列高度。M2导向位置仍用普通螺母。T1先前把AF4、高1.6的M2螺母误称为“薄螺母”，已修正；它对应DIN 934普通六角螺母，可复用O22同尺寸件。[Böllhoff DIN 934尺寸表](https://eshop.boellhoff.de/out/media/pdf/DIN_934_Edelstahl_A2___en.pdf)列出M2对边4、高1.6及M3对边5.5、高2.4。
6. **垫圈按实际三维尺寸买。** T1新增M3小垫圈7×3.2×0.5，O22的M3大垫圈外径9、厚0.8不能直接混用。M2垫圈5×2.2优先统一买0.5厚、8片；S1导向座2片必须0.5厚，其余6片允许原0.3。H摩擦片12×4.3×1不变，R摩擦片18×6.4允许厚1.5或原1.6，R两片同厚。采用平整、去毛刺的不锈钢件，实测厚度并记录；不用橡胶、尼龙或碟簧替代。

## 本轮不用补购的旧五金与选装件

O22的A8碟簧、D4/M3轴肩螺钉、D6×2.5径向磁铁、M1.6紧固件和其余未出现在表内的规格不用于这一套T1。

机械测试使用已提供的W03打印占位块，**无需购买磁铁**。若后续做测角试验，T1球内预留D8×3轴向磁化磁铁，和O22的D6×2.5径向磁铁不同；传感器方案与采购不属于本次机械测试清单。

以上数量不含备用。螺钉、螺母、垫圈可按商家最小包装数量购买；如希望留拆装备件，每个紧固件规格另留2件即可。轴承、光轴和导向肩螺钉先买小批试配再扩大数量。

可下载 [CSV补购与复用对照表](PURCHASE_DELTA_O22.csv)，或返回 [打印与装配入口](START_HERE.html)。
'''
    (OUT / 'PURCHASE_DELTA_O22.zh-CN.md').write_text(text, encoding='utf8')
    report = {
        'baseline': str(BASE.relative_to(H)).replace('\\', '/'),
        'baseline_sha256': hashlib.sha256(BASE.read_bytes()).hexdigest(),
        't1_bom_sha256': hashlib.sha256((OUT / 'BOM.json').read_bytes()).hexdigest(),
        'new_specs': len(new), 'new_quantity': sum(r[4] for r in new),
        'reuse_specs': len(reused), 'reuse_quantity': sum(r[4] for r in reused),
        'total_quantity': sum(r[4] for r in rows),
        'note': 'One H/R/W bench kit; no spares; no inference about owner inventory. Reuse requires matching actual dimensions.',
    }
    (OUT / 'verification/procurement_delta.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(report, ensure_ascii=False))

if __name__ == '__main__':
    main()
