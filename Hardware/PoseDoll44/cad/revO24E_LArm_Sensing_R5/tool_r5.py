from common import *
from export_stock import orientation

def fork():
    cup=tube([0,0,-.65],[0,0,3.2],8.05,7.15)
    cup+=tube([0,0,-.65],[0,0,-.05],8.05,6.6)
    cup=cup^box([-9,-1,-1],[9,10,5])
    for x in [-7.45,7.45]:cup+=box([x-.6,2,-.65],[x+.6,29,1.2])
    cup+=box([-9,26,-.65],[9,40,2.4])
    cup-=cyl([0,34,-1],[0,34,3],3)
    return cup

def nut_starter():
    s=cyl([0,0,-35],[0,0,0],3.1)+cyl([0,0,-45],[0,0,-32],6)
    return s-k.hexagon([0,0,-.85],[0,0,1],4.15,1.0)-cyl([0,0,-30],[0,0,.1],1.15)

def run():
    s=fork();v,f=e.base.a.mesh_data(s);R=orientation(v);m=trimesh.Trimesh(v,f,process=False);m.apply_transform(R)
    path=OUT/'tooling/R5-J003.stl';m.export(path);m=trimesh.load(path,process=True);assert m.is_watertight and len(m.split())==1
    records=[dict(part_number='R5-J003',name='MAG_INSTALL_FORK',label='磁铁组件侧送托叉（重复使用）',stl=path.relative_to(OUT).as_posix(),print_bounds_mm=m.bounds.tolist(),print_matrix=R.tolist(),sha256=sha(path),quantity=1,not_left_in_arm=True)]
    s=nut_starter()
    v,f=e.base.a.mesh_data(s);R=orientation(v);m=trimesh.Trimesh(v,f,process=False);m.apply_transform(R);path=OUT/'tooling/R5-J004.stl';m.export(path)
    records.append(dict(part_number='R5-J004',name='M2_NUT_STARTER',label='M2螺母临时送料柄（只用于起牙和保持）',stl=path.relative_to(OUT).as_posix(),print_bounds_mm=m.bounds.tolist(),print_matrix=R.tolist(),sha256=sha(path),quantity=1,not_left_in_arm=True))
    put(OUT/'tooling/R5_new_tools.json',dict(parts=records))
    print('TOOL R5-J003; one physical fork reused at three roll joints')

if __name__=='__main__':run()
