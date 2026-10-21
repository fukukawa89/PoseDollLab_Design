from audit_revo23_print import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

fig,axs=plt.subplots(2,3,figsize=(15,9))
for ax,(rid,name) in zip(axs.flat,[('S06','targeted_v4'),('S09','targeted_next'),('S18','targeted_v4'),('S15','v3_upright'),('S04','targeted_next'),('S22','targeted_next')]):
    r=read(OUT/'bambu'/('O23G-'+rid)/name/'checked_result.json');p=B/r['project'];report,a=paths(p);M=np.array(r['matrix']);v,f=read_project(p)[0][r['id']];host=solid(v,f)
    issue=r['clearance']['functional_void_hits'][0];lid=issue['layer'];z=issue['z_mm'];h=report['layers'][lid].get('height_mm') or .16
    n=np.load(OUT/'guards_v5'/(r['id']+'.npz'));guard=move(solid(n['v'],n['f']),M)
    rev=r.get('guard_revision',1);gd=OUT/(f'guards_v{rev}' if rev>1 else 'guards');n=np.load(gd/(r['id']+'.npz'));old=move(solid(n['v'],n['f']),M)
    lines=a[(np.isin(a[:,7],[1,2,3]))&(a[:,6]==lid)];beads=shapely.buffer(shapely.linestrings(lines[:,[0,1,3,4]].reshape(-1,2,2)),lines[:,8]/2+.02,quad_segs=3)
    mask=unary_union([polygon(old.slice(float(q))) for q in (z-h+.001,z-h/2,z-.001)])
    overlaps=shapely.intersection(beads,mask);hit=shapely.union_all(overlaps);cx,cy=hit.centroid.coords[0]
    for color,sel in [('red',lines),('green',a[(a[:,7]==0)&(abs(a[:,5]-(z+.36))<.08)])]:
        if len(sel):ax.add_collection(LineCollection(sel[:,[0,1,3,4]].reshape(-1,2,2),colors=color,linewidths=1))
    for c in old.slice(z-h/2).to_polygons():ax.fill(c[:,0],c[:,1],c='orange',alpha=.2)
    for c in guard.slice(z-h/2).to_polygons():ax.plot(*np.vstack([c,c[0]]).T,'b-',lw=1.3)
    for zz,col in [(z-h/2,'black'),(z+.28,'gray')]:
        for c in host.slice(zz).to_polygons():ax.plot(*np.vstack([c,c[0]]).T,color=col,lw=1)
    ax.set_xlim(cx-6,cx+6);ax.set_ylim(cy-6,cy+6);ax.set_aspect('equal');ax.set_title(rid+' Z='+str(round(z,2)))
fig.suptitle('red=support centerline; orange=original guard; blue=small bore guard; black=model here; gray=model above')
fig.tight_layout();fig.savefig(OUT/'guard_hits.png',dpi=130)
