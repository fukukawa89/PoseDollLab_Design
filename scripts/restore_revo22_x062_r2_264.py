"""Restore sparse R1 teeth only where native layer evidence requests backing."""
import sys,json,numpy as np,shapely
from shapely.geometry import LineString,Point,box as box2
from build_revo22_x062_r2_262 import S,baseline,guards,build,put
from build_revo22_fins import union
from o22_material_components import material_components
from o22_cross_section_geometry import polygon

def restore(src,label):
 p=S/'candidates/X062'/src;d=json.loads((p/'design/X062.json').read_text());audit=json.loads((p/'verification/native_final.json').read_text());it=json.loads((p/'verification/plate_manifest.json').read_text())['items'][0];M=np.array(it['rotation_matrix']);t=np.array(it['translation_mm']);n,base,body,fin,tt,rows=baseline();guard,_,_=guards();groups=material_components(fin-guard);keep=set(d['retained_R1_tooth_indices']);cand=[i for i in range(len(tt))if i not in keep and(tt[i]^guard).volume()<1e-7];spec=[]
 for q in audit['critical_external_runs']:
  pts=(np.c_[np.array(q['xy_mm']),np.full(len(q['xy_mm']),q['z_mm'])]-t)@M;g=LineString(pts[:,:2]);ev=next((x for x in audit.get('endpoint_evidence',[])if x['run']['xy_mm']==q['xy_mm']),None);a=ev['actual_endpoint_anchors']if ev else q['anchors'];spec.append(dict(g=g,z=float(pts[0,2]),island=False,anchors=a))
 for q in audit['external_islands']:
  b=q['bounds_mm'];pts=(np.array([[b[0],b[1],q['z_mm']],[b[2],b[3],q['z_mm']]])-t)@M;spec.append(dict(g=box2(*np.r_[pts[:,:2].min(0),pts[:,:2].max(0)]),z=float(pts[0,2]),island=True,anchors=0))
 def loss(k,cover):
  q=spec[k];g=q['g'];res=g.difference(cover)
  if q['island']:return 10. if cover.intersection(g).area<.04 else 0.
  lost=0
  for v in getattr(res,'geoms',[res]):
   if v.geom_type!='LineString':continue
   endpoint=sum(Point(v.coords[j]).distance(Point(g.coords[j]))<.01 for j in [0,-1]);lim=2.7 if q['anchors']==2 or endpoint==0 else .8
   lost+=max(0,v.length-lim)
  return lost
 cov={};empty=shapely.GeometryCollection();current=[empty]*len(spec);base_loss=[loss(k,current[k])for k in range(len(spec))]
 for i in cand:
  cores=[g for g in groups if(g^tt[i]).volume()>.005];obj=tt[i]+union(cores);bb=obj.bounding_box();cc={}
  for k,q in enumerate(spec):
   if not bb[2]<=q['z']-.30<=bb[5]:continue
   section=polygon(obj.slice(q['z']-.30)).buffer(.18)
   if not section.is_empty and section.intersects(q['g']):cc[k]=section
  if cc:cov[i]=cc
 added=[]
 while cov:
  ranked=[]
  for i,cc in cov.items():
   gain=sum(base_loss[k]-loss(k,current[k].union(v))for k,v in cc.items());ranked.append((gain,i))
  gain,i=max(ranked)
  if gain<.04:break
  added.append(i);keep.add(i)
  for k,v in cov.pop(i).items():current[k]=current[k].union(v);base_loss[k]=loss(k,current[k])
  if len(added)%10==0:print('RESTORE',len(added),'geometric_loss',round(sum(base_loss),2),flush=True)
 rep=build(label,selected=keep);put(S/'candidates/X062'/label/'verification/restoration.json',dict(from_candidate=src,added_indices=added,added_ids=[rows[i]['id']for i in added],remaining_geometric_loss=[dict(index=k,z=q['z'],loss=base_loss[k])for k,q in enumerate(spec)if base_loss[k]>.001],scope='Greedy choice from existing R1 teeth; actual native re-slice remains mandatory.'))
 print('RESTORED',label,len(added),'geometric_loss',sum(base_loss),flush=True)
if __name__=='__main__':restore(*sys.argv[1:])
