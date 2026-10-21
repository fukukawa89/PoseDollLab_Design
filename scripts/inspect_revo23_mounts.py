"""Orthographic diagnostic renders of the actual retained attachment material."""
from repair_revo23_endfaces import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

parts,p,cfg=load_h();N=frames(p,p['neutral_raw_deg'])
key=sys.argv[1] if len(sys.argv)>1 else 'frame/clavicle_l.protract_frame'
index=int(sys.argv[2]) if len(sys.argv)>2 else 0
r=connection_records(key)['rods'][index];host=native_hosts(key,parts,p,N)[r['mount']]
v,f=vf(host);bb=np.array(host.bounding_box());center=(bb[:3]+bb[3:])/2;span=max(bb[3:]-bb[:3])/2+4
a=np.array(r['centerline_world_mm'])[0];body=rod_body(r)^box(center-span,center+span)
fig=plt.figure(figsize=(16,5))
for i,(elev,azim) in enumerate(((25,-50),(0,0),(90,-90))):
    ax=fig.add_subplot(1,3,i+1,projection='3d');ax.set_proj_type('ortho')
    for s,color,alpha in [(host,'#7b9bb6',1),(body,'#de8926',.65)]:
        vv,ff=vf(s);ax.add_collection3d(Poly3DCollection(vv[ff],facecolors=color,edgecolor='none',alpha=alpha))
    ax.set_xlim(center[0]-span,center[0]+span);ax.set_ylim(center[1]-span,center[1]+span);ax.set_zlim(center[2]-span,center[2]+span)
    ax.set_box_aspect((1,1,1));ax.view_init(elev,azim);ax.set_xlabel('X');ax.set_ylabel('Y');ax.set_zlabel('Z')
fig.suptitle(key+' retained mount (blue) and rod (orange)');fig.tight_layout()
path=HROOT/(key.replace('/','__')+f'_mount_{index}.png');fig.savefig(path,dpi=150);print(path)
