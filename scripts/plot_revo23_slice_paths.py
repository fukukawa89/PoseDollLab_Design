"""Show actual sliced model/support paths at two heights in four repaired parts."""
from slice_revo23_exports import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

OUT=B/'verification/stl_export_review'

def segments(code):
    values={};feature='';height=0.;layer_h=.16;position=np.zeros(2);absolute=True
    for line in code.splitlines():
        if line.startswith('; Z_HEIGHT:'):height=float(line.split(':',1)[1])
        elif line.startswith('; LAYER_HEIGHT:'):layer_h=float(line.split(':',1)[1])
        elif line.startswith('; FEATURE:'):feature=line.split(':',1)[1].strip()
        elif line.strip()=='G90':absolute=True
        elif line.strip()=='G91':absolute=False
        elif re.match(r'G[0123] ',line):
            words={k:float(v) for k,v in re.findall(r'([XYEIJ])(-?(?:\d*\.\d+|\d+))',line.split(';',1)[0])}
            nxt=np.array([words.get(k,position[i] if absolute else 0.) for i,k in enumerate(('X','Y'))])
            if not absolute:nxt+=position
            if words.get('E',0)>0 and ('X' in words or 'Y' in words) and feature not in ('','Custom','Brim','Skirt'):
                kind='support' if feature in ('Support','Support interface') else 'model'
                d=values.setdefault(height,dict(model=[],support=[],layer_height=layer_h))
                if line.startswith(('G2 ','G3 ')) and ('I' in words or 'J' in words):
                    center=position+np.array([words.get('I',0.),words.get('J',0.)]);rad=np.linalg.norm(position-center)
                    a=np.arctan2(*(position-center)[::-1]);b=np.arctan2(*(nxt-center)[::-1]);delta=(b-a)%(2*np.pi)
                    if line.startswith('G2 '):delta=delta-2*np.pi
                    angles=np.linspace(a,a+delta,max(3,int(abs(delta)*rad/.4)))
                    vv=center+rad*np.c_[np.cos(angles),np.sin(angles)];d[kind].extend(np.stack([vv[:-1],vv[1:]],axis=1))
                else:d[kind].append(np.array([position.copy(),nxt.copy()]))
            position=nxt
    return values

def main():
    OUT.mkdir(parents=True,exist_ok=True);plt.rcParams['font.family']='Microsoft YaHei';plt.rcParams['axes.unicode_minus']=False
    fig,axes=plt.subplots(4,2,figsize=(12,15));provenance=[]
    selected=[('O23G-S19','左大腿'),('O23G-S23','右小臂'),('O23G-S13','骨盆'),('O23G-C01','背盒')]
    reports=read(ROOT/'results.json')['rows'];repair=read(EXPORT_ROOT/'repair.json')['rows']
    for row,(rid,title) in enumerate(selected):
        s=next(r for r in reports if r['id']==rid);r=next(r for r in repair if r['id']==rid)
        with zipfile.ZipFile(B/s['project']) as z:code=z.read(s['gcode_members'][0]).decode('utf8','replace')
        paths=segments(code);levels=np.array([z for z,d in paths.items() if d['model']]);M=np.array(read(ROOT/rid/'input.json')['matrix'])
        mesh=trimesh.load(B/r['staged_stl'],process=True);mesh.apply_transform(M)
        for col,fraction in enumerate((.3,.7)):
            z=float(levels[np.argmin(abs(levels-(levels.min()+fraction*np.ptp(levels))))]);d=paths[z];ax=axes[row,col]
            plane=z-d['layer_height']/2;section=mesh.section(plane_normal=[0,0,1],plane_origin=[0,0,plane])
            if section is not None:
                for loop in section.discrete:ax.plot(loop[:,0],loop[:,1],color='#adb5b1',linewidth=.7)
            for kind,color,width in [('support','#9bbbc5',.45),('model','#17665d',.6)]:
                if d[kind]:ax.add_collection(LineCollection(d[kind],colors=color,linewidths=width))
            ax.set_aspect('equal');lo,hi=mesh.bounds;ax.set_xlim(lo[0]-6,hi[0]+6);ax.set_ylim(lo[1]-6,hi[1]+6)
            ax.set_title(f'{rid} · {title} / Z = {z:.2f} mm',fontsize=12);ax.set_xlabel('X / mm');ax.set_ylabel('Y / mm');ax.grid(alpha=.12)
            provenance.append(dict(id=rid,project_sha256=s['project_sha256'],gcode_sha256=s['gcode_sha256'],z_mm=z,model_segments=len(d['model']),support_segments=len(d['support'])))
    fig.suptitle('O23G · 实际切片路径抽查\n深绿：模型挤出路径　淡蓝：自动支撑　灰：模型截面',fontsize=16,y=.994)
    fig.tight_layout(rect=[0,0,1,.965]);fig.savefig(OUT/'slice_paths.png',dpi=150);plt.close(fig)
    put(OUT/'slice_paths.json',dict(source='Actual generated OrcaSlicer G-code and STL cross-sections; no synthetic illustration.',rows=provenance,image_sha256=sha(OUT/'slice_paths.png')))

if __name__=='__main__':main()
