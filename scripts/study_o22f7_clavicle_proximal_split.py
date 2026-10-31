from o22f7_animation import *
from build_revo22_assembly import b
import itertools
C=WORK/'structure_revision';x=Build();x.begin(x.g['steps'][3]);inverse=np.linalg.inv(x.mount)
def shape(k):
 o=x.obs[k];m=x.scene['meshes'][o['mesh']];return b.g.move(b.b.from_tri_exact(x.verts[m['first']:m['first']+m['count'],:3].reshape(-1,3,3)),inverse@x.mats[k])
original=shape('frame/clavicle_l.protract_frame');fixed=[shape(k) for k in ['frame/chest']+['clavicle_l.protract/'+t for t in ['M3_nut','M3_reaction_washer','inner_M4_wide']]]
D=[np.array(v,float)/np.linalg.norm(v) for v in itertools.product([0,-1,1],repeat=3) if any(v)]
def test(s,fix):
 bounds=[np.array(f.bounding_box()) for f in fix];wins=[]
 for d in D:
  for mm in np.r_[np.linspace(0,12,25),np.arange(13,181,2)]:
   moved=s.translate(d*mm);bb=np.array(moved.bounding_box());bad=False
   for f,bo in zip(fix,bounds):
    if np.any(np.minimum(bb[3:],bo[3:])<=np.maximum(bb[:3],bo[:3])+1e-6):continue
    if (moved^f).volume()>.02:bad=True;break
   if bad:break
  if not bad:wins.append(d.tolist())
 return wins
rows=[];pack={}
for xx in [16,18,20,22,24]:
 region=b.b.box([-200,-200,-200],[xx,200,200]);a=original^region;c=original-region
 if b.g.solid_count(a)!=1 or b.g.solid_count(c)!=1:print('SKIP',xx);continue
 wa=test(a,fixed);wc=test(c,fixed+[a]);rows.append({'split_mount_x':xx,'root_first':wa,'distal_after_root':wc});pack['root_'+str(xx)]=b.g.tri(a);pack['distal_'+str(xx)]=b.g.tri(c)
 put(C/'proximal_split_feasibility.json',{'status':'CANDIDATE_STUDY_ONLY','rows':rows});print('PROXIMAL',xx,len(wa),len(wc),flush=True)
np.savez_compressed(C/'proximal_split_halves.npz',**pack)
