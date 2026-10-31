"""Physical face directions for the tutorial; never changes manufacturing meshes.

Axes are in each exported component's assembly coordinates. They travel through
the same animation matrix as that component, including the tilted preload path.
For locknuts the marked face is the screw EXIT, not the nut insertion direction.
"""
EDITION = '2026-10-23 · 五金朝向版'
NUTS = {'N2': (2, 4, 1.6, .4), 'N3': (3, 5.5, 2.4, .5),
        'NL2': (2, 4, 3, .4), 'NL3': (3, 5.5, 4, .5), 'NL4': (4, 7, 5, .7)}
WASHERS = {'W2': (5, 2.2), 'W3': (7, 3.2), 'W4': (9, 4.3),
           'FR4': (12, 4.3), 'FR6': (18, 6.4)}


def annotate(catalog, lessons):
    pairs = {}

    def mark(id, normal, target, target_id, instruction, bolt=None, metal_only=False):
        p = catalog[id]; sku = p['sku']
        kind = 'nylon' if sku.startswith('NL') else 'plain' if sku in NUTS else 'washer'
        lo, hi = p['bounds']; c = [(a+b)/2 for a, b in zip(lo, hi)]
        depth = sum(abs(n)*(b-a) for n, a, b in zip(normal, lo, hi))
        face = [a+n*depth/2 for a, n in zip(c, normal)]
        if kind == 'nylon':
            d, af, height, pitch = NUTS[sku]
            title = f'M{d} 尼龙锁紧螺母 · 有尼龙圈'
            label = '尼龙圈端'; other = '金属螺纹端 · 先旋入'
            note = '从金属螺纹端起牙，最后旋过尼龙圈。进入尼龙圈后阻力增加，用配套扳手缓慢旋入；不要挖掉尼龙圈。若金属段就卡住，先退出检查。'
            p['label'] = title
            p['spec'] = f'{title}；M{d}×{pitch}；对边 {af:g} / 总高 ≤{height:g} mm'
            radius, bore = af*.44, d/2+.02
        elif kind == 'plain':
            d, af, height, pitch = NUTS[sku]
            title = f'M{d} 普通六角螺母 · 无尼龙圈'
            label = '承压平面'; other = '另一端也是金属'
            note = '两端均为金属螺纹，无塑料圈；两面相同可互换，若一面承压面更宽、更平，让该面贴合所指零件。先在打印件外确认能顺畅旋过螺钉。'
            p['label'] = title
            p['spec'] = f'{title}；M{d}×{pitch}；对边 {af:g} / 厚 {height:g} mm'
            radius, bore = af*.44, d/2+.02
        else:
            od, inner = WASHERS[sku]; radius, bore = od/2, inner/2
            title = '导向座钢垫圈 · 两面接触金属' if metal_only else ('大摩擦垫圈 · 光滑面朝转子' if sku.startswith('FR') else '平垫圈 · 光滑面贴打印件')
            label = '光滑面（示意）'; other = '另一面 · 去除凸起毛刺'
            note = ('两面均须平整、无毛刺。这处没有强制正反：教程统一示意光滑面朝肩部；翻面不能补偿厚度或圆角干涉。' if metal_only else
                    '绿色仅标示光滑、平整的一面，实物不需要涂色。明显凸起、刮手的毛刺先去除或换件，不把毛刺压进塑料。两面同样平整时可互换。')
        p['orientation'] = dict(kind=kind, normal=normal, center=c, face=face,
                                depth=depth, radius=radius, bore=bore, title=title,
                                face_label=label, opposite_label=other, target=target,
                                target_id=target_id, instruction=instruction, note=note,
                                metal_only=metal_only, bolt=bolt)
        if bolt:
            pairs.setdefault(bolt, []).append(id)

    for st in ['H', 'R']:
        # R's fixed frame is clocked 90 degrees about Y. Its rotor is not.
        shaft_exit = [0, 0, -1] if st == 'H' else [-1, 0, 0]
        for sign, bracket in [(-1, '04'), (1, '05')]:
            mark(f'{st}shaft_clamp_nut_{sign}', shaft_exit, '光轴 / 轴孔', st+'shaft',
                 f'尼龙圈端朝 {st}{bracket} 的轴孔；金属螺纹端朝外侧 M3×10 螺钉头。侧向送入螺母，不能把侧向装入箭头当作螺纹方向。', f'{st}shaft_clamp_{sign}')
        for z in [-20, -50, -80]:
            mark(f'{st}rotor_n0_{z}', [0, 1, 0], st+'01 槽底', st+'01',
                 f'只用 N3 普通 M3 螺母（厚 2.4 mm、无尼龙圈）。平整承压面贴 {st}01 槽底，孔对准前半体；NL3 尼龙锁紧螺母不能替代。', f'{st}rotor_bolt_{z}')
            mark(f'{st}rotor_n1_{z}', [0, 1, 0], '槽内第一颗普通螺母', f'{st}rotor_n0_{z}',
                 '第二颗也用 N3 普通 M3 螺母，无尼龙圈。平整承压面朝槽内第一颗螺母，固定螺钉头后并紧。')
            mark(f'{st}rotor_w_{z}', [0, -1, 0], st+'02 转子前半体', st+'02',
                 f'光滑、平整的一面贴 {st}02；另一面朝 M3×12 螺钉头。尺寸 7×3.2×0.5 mm。')
        for sign, rotor in [(-1, '01'), (1, '02')]:
            mark(f'{st}friction_{sign}', [0, -sign, 0], st+rotor+' 转子', st+rotor,
                 f'光滑面朝 {st}{rotor} 转子摩擦面；另一面朝压板。两片垫圈的光滑面相对，夹住转子。两面都须去毛刺。')
        for z in [-5, 5]:
            mark(f'{st}preload_w-1_{z}', [0, 1, 0], st+'04 固定压板', st+'04',
                 f'光滑面贴 {st}04 固定压板，另一面朝 M3×30 螺钉头；侧向倾斜放入时保持此正反关系。')
            mark(f'{st}preload_w1_{z}', [0, -1, 0], st+'03 浮动压板', st+'03',
                 f'光滑面贴 {st}03 浮动压板；另一面朝 M3 尼龙锁紧螺母的金属端。')
            mark(f'{st}preload_n{z}', [0, 1, 0], '前侧外部 / 螺钉尖端', st+'03',
                 f'金属螺纹端朝 {st}03 外侧垫圈，尼龙圈端背离压板、朝螺钉尖端；不是朝螺钉头。', f'{st}preload_{z}')
        for z in [-12, 12]:
            mark(f'{st}tie_w0_{z}', [0, 1, 0], st+'08 刻度环', st+'08',
                 f'光滑面贴 {st}08 刻度环；另一面朝 M4×60 螺钉头。')
            mark(f'{st}tie_w1_{z}', [0, -1, 0], st+'05 可拆支架', st+'05',
                 f'光滑面贴 {st}05；另一面朝 M4 尼龙锁紧螺母的金属端。')
            mark(f'{st}tie_n_{z}', [0, 1, 0], '可拆支架外侧 / 螺钉尖端', st+'05',
                 f'金属端贴 {st}05 外侧垫圈，尼龙圈端背离支架、朝 M4×60 螺钉尖端。', f'{st}tie_{z}')

    for sign, side, liner, cup in [(-1, '后侧', 'W04', 'W06'), (1, '前侧', 'W05', 'W07')]:
        mark(f'Wguide_nut_{sign}', [0, sign, 0], '导向座 0.5 mm 钢垫圈', f'Wguide_w_{sign}',
             f'{side}导向座只用 N2 普通 M2 螺母（厚 1.6 mm、无尼龙圈）。平整承压面直接贴钢垫圈，垫圈靠球外、螺母靠球心；不能换 NL2。', f'Wguide_{sign}')
        mark(f'Wguide_w_{sign}', [0, sign, 0], '导向肩螺钉的肩部台阶', f'Wguide_{sign}',
             f'{side}导向座必须用厚 0.5 mm 钢垫圈。外侧贴肩部台阶，内侧直接贴普通 M2 螺母，中间不夹塑料。两面平整即可，无强制正反。', metal_only=True)
        for xx in [-8.5, 8.5]:
            suffix = f'{sign}_{xx}'
            mark('Wliner_n_'+suffix, [0, sign, 0], cup+' 外侧 / 远离球心', cup,
                 f'金属端朝 {liner} 固定耳和球心；尼龙圈端朝 {cup} 外侧、背离球心。不要与导向座的普通 M2 螺母混用。', 'Wliner_screw_'+suffix)
            mark('Wliner_w_'+suffix, [0, sign, 0], liner+' 衬片固定耳', liner,
                 f'光滑面贴 {liner} 固定耳；另一面朝球心一侧的 M2×8 螺钉头。不是把粗糙面压在薄耳上。')
    for z in [-5.5, 5.5]:
        mark(f'Wball_nut_{z}', [-1, 0, 0], 'W01 球后半体外侧', 'W01',
             '金属螺纹端朝球内部和 W02；尼龙圈端朝 W01 外侧，即远离 W02 的一端。', f'Wball_bolt_{z}')
    for xx in [-8, 8]:
        for sign, cup in [(-1, 'W06'), (1, 'W07')]:
            mark(f'Wpreload_w{sign}_{xx}', [0, -sign, 0], cup+' 预紧耳', cup,
                 f'光滑面贴 {cup} 预紧耳外表面；另一面朝'+('M3×35 螺钉头。' if sign < 0 else 'M3 尼龙锁紧螺母的金属端。'))
        mark(f'Wpreload_n{xx}', [0, 1, 0], 'W07 外侧 / 螺钉尖端', 'W07',
             '金属端贴 W07 外侧垫圈；尼龙圈端背离 W07，朝 M3×35 螺钉尖端。', f'Wpreload_{xx}')
    for sign in [-1, 1]:
        mark(f'Wlever_w{sign}', [-sign, 0, 0], 'W09 加载杆', 'W09',
             '光滑面贴 W09 加载杆；另一面朝'+('M2×20 螺钉头。' if sign > 0 else 'M2 尼龙锁紧螺母的金属端。'))
    mark('Wlever_n', [-1, 0, 0], '加载杆外侧 / 螺钉尖端', 'W09',
         '金属端贴 W09 螺母侧垫圈；尼龙圈端背离加载杆，朝横向螺钉尖端。', 'Wlever_screw')

    expected = {id for id, p in catalog.items() if p['sku'] in NUTS or p['sku'] in WASHERS}
    actual = {id for id, p in catalog.items() if 'orientation' in p}
    assert actual == expected, (expected-actual, actual-expected)
    for lesson in lessons:
        for step in lesson.steps:
            relevant = [id for id in step['ids'] if id in actual]
            # Paired nuts remain visible in the instructions while the screw is
            # installed, even if the nut itself comes in a later step.
            if not relevant:
                relevant = list(dict.fromkeys(n for id in step['ids'] for n in pairs.get(id, [])))
            step['orientation_ids'] = relevant
            if step['kind'] == 'add' and relevant:
                o = catalog[relevant[0]]['orientation']
                own = step['ids'][0] == relevant[0]
                step['orientation_instruction'] = o['instruction']
                if own and o['kind'] in ['nylon', 'plain']:
                    step['title'] += ' · '+('有尼龙圈' if o['kind']=='nylon' else '无尼龙圈')
        lesson.steps[0]['detail'] += ' 先展开页面上方“五金辨认与朝向”。普通螺母无尼龙圈；锁紧螺母有尼龙圈，二者不能互换。'
    return dict(parts=len(actual), nuts=sum(catalog[id]['orientation']['kind']!='washer' for id in actual),
                washers=sum(catalog[id]['orientation']['kind']=='washer' for id in actual),
                paired_screws=len(pairs), edition=EDITION)
