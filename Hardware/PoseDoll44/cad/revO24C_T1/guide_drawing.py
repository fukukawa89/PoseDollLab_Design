"""Local CAD section, SVG paths from Manifold solids (not a concept illustration)."""
from kit import *

def main():
    P={p['id']:p for p in build().parts}
    # Section very near the split plane; Y horizontal, Z vertical.
    def path(s):
        polygons=s.translate([-.02,0,0]).rotate([0,90,0]).slice(0).to_polygons()
        return ' '.join('M'+' L'.join(f'{85+36*p[1]:.2f},{235-36*p[0]:.2f}' for p in poly)+' Z' for poly in polygons)
    colors={'W02':'#e0a34c','Wguide_1':'#8097aa','Wguide_w_1':'#df6361','Wguide_nut_1':'#67aa9e'}
    crop=box([-.2,4.7,-3.4],[.2,18.1,3.4])
    s=['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="450" viewBox="0 0 1000 450">',
       '<rect width="1000" height="450" fill="#fafbf6"/><style>text{font-family:Segoe UI,Microsoft YaHei,sans-serif;fill:#243f36}.small{font-size:16px}.label{font-size:19px;font-weight:600}</style>',
       '<text x="35" y="40" font-size="25">S1 腕部导向接口 · 实际CAD局部剖面</text>',
       '<text x="35" y="70" class="small">沿球体合模面附近剖切；只显示正Y侧导向座，未显示球窝与衬片。单位 mm。</text>']
    for id,col in colors.items():s.append(f'<path d="{path(P[id]["s"]^crop)}" fill="{col}" fill-rule="evenodd" stroke="#344a44" stroke-width="1"/>')
    s.append('<path d="M245,235 H760" stroke="#667c71" stroke-dasharray="6 5" fill="none"/>')
    # Separate leaders and text from the cut geometry.
    for label,x,tx,ty in [('普通M2螺母 · 高1.6',8.2,80,120),('钢垫圈 · 厚0.5',9.25,390,104),('光肩 Ø2.5 × 6',12.3,560,120),('头 Ø4.8 × 2.4',16.7,780,152)]:
        xx=85+36*x
        s.append(f'<path d="M{tx+70},{ty+8} L{xx},177" stroke="#5b7167" fill="none"/><text x="{tx}" y="{ty}" class="label">{label}</text>')
    s.extend(['<text x="40" y="370" class="label">金属夹紧路径：光肩 → 钢垫圈 → 普通螺母</text>',
        '<text x="40" y="400" class="small">橙色为球体；凹槽捕获金属组件，名义轴向总游隙0.20。螺纹露出1.9。</text>',
        '<text x="40" y="426" class="small">需低强度可拆金属螺纹锁固；此剖面不代表公差、材料强度或磨损实测结果。</text></svg>'])
    (OUT/'images/guide_section.svg').write_text(''.join(s),encoding='utf8')

if __name__=='__main__':main()
