from audit_revo23_print import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

fig,axs=plt.subplots(2,3,figsize=(15,9))
for ax,(rid,name,idx) in zip(axs.flat,[('S18','flat1_clear',0),('S06','pose1_clear_m2',2),('S21','flat1_clear',0),('S02','pose1_tree_clear_snug',0),('S05','pose1_tree_clear_snug',0),('W01','flat2_clear',-1)]):
    r=read(OUT/'bambu'/('O23G-'+rid)/name/'checked_result.json');p=B/r['project'];_,a=paths(p);M=np.array(r['matrix']);v,f=read_project(p)[0][r['id']];host=solid(v,f)
    if idx>=0:
        t=r['islands']['external_new_islands'][idx];z=t['z_mm'];bb=t['bounds_mm'];cx=(bb[0]+bb[2])/2;cy=(bb[1]+bb[3])/2
    else:z=r['clearance']['functional_void_hits'][0]['z_mm'];cx=90;cy=90
    for color,sel in [('green',a[(a[:,7]==0)&(abs(a[:,5]-z)<.001)]),('red',a[(np.isin(a[:,7],[1,2,3]))&(a[:,5]>z-.65)&(a[:,5]<z-.1)])]:
        if len(sel):ax.add_collection(LineCollection(sel[:,[0,1,3,4]].reshape(-1,2,2),colors=color,linewidths=1.1))
    n=np.load(OUT/'guards_v2'/(r['id']+'.npz'));guard=move(solid(n['v'],n['f']),M)
    for c in guard.slice(z-.3).to_polygons():ax.fill(c[:,0],c[:,1],c='orange',alpha=.3)
    for c in host.slice(z-.24).to_polygons():ax.plot(*np.vstack([c,c[0]]).T,'k-',lw=.8)
    n=np.load(B/r['source_project'].replace('input.3mf','support_blocker.npz'));block=move(solid(n['v'],n['f']),M)
    for c in block.slice(z-.24).to_polygons():ax.plot(*np.vstack([c,c[0]]).T,'b-',lw=.8)
    d=10 if idx>=0 else 30
    ax.set_xlim(cx-d,cx+d);ax.set_ylim(cy-d,cy+d);ax.set_aspect('equal');ax.set_title(rid+' z='+str(round(z,2)))
fig.suptitle('green=current model; black=prior CAD; red=support below; orange=void; blue=blocker')
fig.tight_layout();fig.savefig(OUT/'debug_sections.png',dpi=130)
