"""Four-piece O13 core prototype; old coupon remains valid and unchanged."""
from solid_ops import *
import importlib.util,zipfile
def main():
 spec=importlib.util.spec_from_file_location('print_helpers',H/'cad/revO11/export_print_pack.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 dest=H/'bench/revO13';dest.mkdir(exist_ok=True);(dest/'print_beds').mkdir(exist_ok=True)
 raw={k:from_tri(t) for k,t in np.load(OUT/'printed_core/parts.npz').items()}
 layout={'C01':m.place(raw['C01'],rot(0,90),10,10),'C02':m.place(raw['C02'],rot(1,90),65,10),
 'C14':m.place(raw['C14'],rot(0,180),10,70),'C15':m.place(raw['C15'],np.eye(3),50,70)}
 audit=m.write_3mf(dest/'print_beds/O13_core_fit_only.3mf',layout)
 for name,s in layout.items():export_stl(dest/'print_beds'/f'{name}_on_bed.stl',tri(s))
 bom=[{'item':'打印叉架与承力环半件','quantity':4,'spec':'C01, C02, C14, C15'},
 {'item':'轴肩螺钉','quantity':4,'spec':'用户现货 Φ4 × 8，M3螺纹长6 mm，3 mm内六角'},
 {'item':'M4大垫圈','quantity':8,'spec':'外径12，厚1；同当前小样'},
 {'item':'M4普通垫圈','quantity':4,'spec':'外径9，厚0.8；同当前小样'},
 {'item':'A8不锈钢碟簧','quantity':8,'spec':'8×4.2×0.4，每处2片反向；弹力未知'},
 {'item':'M3六角螺母','quantity':4,'spec':'对边5.5，厚2.4；同当前小样'},
 {'item':'M3大垫圈','quantity':4,'spec':'外径9，厚0.8；同当前小样'},
 {'item':'承力环合拢螺钉参考件','quantity':4,'spec':'M1.6×6，头径3，头高1.6；采购尺寸需核对'},
 {'item':'承力环合拢螺母参考件','quantity':4,'spec':'M1.6，对边3.2，厚1.3；采购尺寸需核对'}]
 save('core_print_pack.json',{'bed':audit,'bom':bom,'slicer_tested':False,'geometry_only':True,'spring_force_N':None,'fit_prototype_only':True,
 'scope':'Four new-core printed bodies only, no outer twist housings, sensor, arm carrier or full body. Candidate orientation requires service-provider slicing/support review.'})
 (dest/'bom.json').write_text(json.dumps(bom,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('core prototype bed exported: 4 parts; not full body release')
if __name__=='__main__':main()
