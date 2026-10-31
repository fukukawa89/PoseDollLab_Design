"""Reusable assembly aids, not parts of the arm or its load path."""
from build_stock import *
import io

def tray():
    # Slot is wider than the 7 mm AX4 head, so the captured packet can be released sideways.
    s=tube([0,0,0],[0,0,1.2],5.9,3.8)-box([-3.8,0,-.1],[3.8,20,1.3])
    s+=tube([0,0,1.1],[0,0,1.8],5.9,4.62)-box([-4.62,0,1.0],[4.62,20,1.9])
    for x in [-4.85,4.85]:s+=box([x-1.0,-32,0],[x+1.0,0,1.2])
    s+=box([-10,-50,-1],[10,-30,2])
    return s

def pin():
    # Enter from the open front of the bare rotor. AX4 pushes it out the same open end.
    # The 7 mm grip NEVER traverses the rotor's 4.25 mm bore.
    return cyl([0,0,-14],[0,0,4],1.85)+cyl([0,0,4],[0,0,10],3.5)

def run():
    (OUT/'tooling').mkdir(exist_ok=True);rows=[]
    for pn,label,s in [('R4-J001','侧装托叉（可重复使用）',tray()),('R4-J002','从裸转子正面插入的导向针',pin())]:
        v,f=e.base.a.mesh_data(s);m=trimesh.Trimesh(v,f,process=False);R=rot([1,0,0],90) if pn.endswith('2') else np.eye(4);vv=v@R[:3,:3].T;R[:3,3]=-vv.min(0);m.apply_transform(R)
        path=OUT/'tooling'/f'{pn}.stl';m.export(path);m=trimesh.load(path,process=True);assert m.is_watertight and len(m.split())==1
        rows.append(dict(part_number=pn,kit_label=label,quantity=1,stl=path.relative_to(OUT).as_posix(),sha256=sha(path),print_matrix=R.tolist(),print_bounds_mm=m.bounds.tolist(),temporary=True,installed_in_arm=False))
    put(OUT/'tooling/kit.json',dict(parts=rows,additional_metal_count=0,notes='两个工装全臂反复使用；不留在人偶内，不承担预紧或防脱。托叉使轴向肩钉能够先捕获整组，再从侧面抽出。'))
    print('TOOLING',len(rows),flush=True)
if __name__=='__main__':run()
