"""Candidate-only splitting study. Released manufacturing files are read-only."""
from o22f7_animation import *
from build_revo22_assembly import b
import itertools,time
C=WORK/'structure_revision';C.mkdir(exist_ok=True)
x=Build();x.begin(x.g['steps'][3]);key='frame/clavicle_l.protract_frame'
def shape(k):
 o=x.obs[k];m=x.scene['meshes'][o['mesh']];return b.g.move(b.b.from_tri_exact(x.verts[m['first']:m['first']+m['count'],:3].reshape(-1,3,3)),x.mats[k])
original=shape(key);chest=shape('frame/chest');fixed=[chest]+[shape('clavicle_l.protract/'+t) for t in ['M3_nut','M3_reaction_washer','inner_M4_wide']]
D=[np.array(v,float)/np.linalg.norm(v) for v in itertools.product([0,-1,1],repeat=3) if any(v)]
D=[x.mount[:3,:3]@v for v in D]+D

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
for xx in [-32,-28,-24,-20]:
 region=b.b.box([-200,-200,250],[xx,200,550]);a=original^region;c=original-region
 if b.g.solid_count(a)!=1 or b.g.solid_count(c)!=1:continue
 wa=test(a,fixed);wc=test(c,fixed+[a]);wa2=test(a,fixed+[c]);wc2=test(c,fixed)
 row={'split_x':xx,'root_volume':a.volume(),'distal_volume':c.volume(),'root_first':wa,'distal_after_root':wc,'root_after_distal':wa2,'distal_first':wc2};rows.append(row);pack['root_'+str(-xx)]=b.g.tri(a);pack['distal_'+str(-xx)]=b.g.tri(c)
 print('SPLIT',xx,'paths',[len(q) for q in [wa,wc,wa2,wc2]],flush=True)
 put(C/'split_feasibility.json',{'status':'CANDIDATE_STUDY_ONLY','rows':rows,'manufacturing_changed':False})
np.savez_compressed(C/'split_halves.npz',**pack)
