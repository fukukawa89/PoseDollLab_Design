"""Repack the frozen F4 assembly and its fins without changing meshes or print rotations."""
from pathlib import Path
import sys,json,copy,random,math,numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from pack_revo22_a1mini import split_free
B=R/'Hardware/PoseDoll44/bench/revO22';D=B/'O22F4_Release';O=B/'a1mini_fins_v4';S=O/'compact230';S.mkdir(exist_ok=True)
EDGE=4.;GAP=6.;LIMIT=180-2*EDGE+GAP

def pack(items,seed):
 rng=random.Random(seed);mode=seed%6
 def score(i):
  w,h=i['w'],i['h'];v=[w*h,max(w,h)**2,min(w,h)**2,w*w,h*h,w+h][mode]
  return -v*(rng.uniform(.65,1.35)if seed>=6 else 1)
 plates=[]
 for it in sorted(items,key=score):
  best=None;iw,ih=it['w']+GAP,it['h']+GAP
  for pi,p in enumerate(plates):
   for x,y,w,h in p['free']:
    if iw>w+1e-8 or ih>h+1e-8:continue
    s=(pi,min(w-iw,h-ih),max(w-iw,h-ih),y,x)if seed%3 else(pi,w*h-iw*ih,min(w-iw,h-ih),y,x)
    if best is None or s<best[0]:best=(s,pi,x,y)
  if best is None:
   assert max(iw,ih)<=LIMIT+1e-6
   pi=len(plates);plates.append({'free':[(0.,0.,LIMIT,LIMIT)],'items':[]});best=((),pi,0.,0.)
  _,pi,x,y=best;p=plates[pi];p['free']=split_free(p['free'],(x,y,iw,ih));i=copy.deepcopy(it);delta=np.array([x+EDGE,y+EDGE,0.])-np.array(it['bounds_mm'][:3]);i['translation_mm']=(np.array(it['translation_mm'])+delta).tolist();i['bounds_mm']=(np.array(it['bounds_mm'])+np.r_[delta,delta]).tolist();i['fins_bounds_mm']=i['bounds_mm'];i['x']=x+EDGE;i['y']=y+EDGE;p['items'].append(i)
 return plates

def search(items,n=1200):
 best=None
 for seed in range(n):
  p=pack(items,seed);score=(len(p),sum(len(q['items'])==1 for q in p),-len(p[-1]['items']))
  if best is None or score<best[0]:best=(score,p,seed);print('PACK230_BEST',len(items),seed,score,flush=True)
 return best[1],best[2]

def main():
 src=json.loads((D/'manifest.json').read_text());main=[];samples=[]
 for p in src['plates']:
  for it in p['items']:
   q=copy.deepcopy(it);q['previous_f4_address']=it['object_name'].split()[0];q['previous_f4_plate']=p['id'];q['source_profile']=copy.deepcopy(p['profile']);q['w']=it['bounds_mm'][3]-it['bounds_mm'][0];q['h']=it['bounds_mm'][4]-it['bounds_mm'][1]
   (samples if p['optional'] else main).append(q)
 chest=next(i for i in main if i['id']=='X046');others=[i for i in main if i['id']!='X046'];packed,seed=search(others);sp,ss=search(samples,120);plates=[]
 for index,p in enumerate([{'items':[chest]}]+packed,1):
  pid=f'C{index:02}'
  for number,it in enumerate(p['items'],1):it.update(number=number,object_name=f'{pid}-{number:02} '+it['id']+' '+it['part'])
  plates.append({'id':pid,'title':'O22-F4 合盘主套','optional':False,'items':p['items'],'exact_original_plate_reuse':'F01'if index==1 else None})
 for index,p in enumerate(sp,1):
  pid=f'Q{index:02}'
  for number,it in enumerate(p['items'],1):it.update(number=number,object_name=f'{pid}-{number:02} '+it['id']+' '+it['part'])
  plates.append({'id':pid,'title':'O22-F4 合盘额外小样','optional':True,'items':p['items']})
 original={i['object_name'].split()[0]:i for p in src['plates']for i in p['items']};gaps=[];edge=[]
 for p in plates:
  for i,it in enumerate(p['items']):
   old=original[it['previous_f4_address']];assert it['rotation_matrix']==old['rotation_matrix'];assert abs(it['translation_mm'][2]-old['translation_mm'][2])<1e-8;b=np.array(it['bounds_mm']);assert min(b[:2])>=EDGE-1e-6 and max(b[3:5])<=180-EDGE+1e-6 and abs(b[2])<1e-6 and b[5]<180;edge.append(min(*b[:2],*(180-b[3:5])))
   for other in p['items'][i+1:]:
    bb=np.array(other['bounds_mm']);gap=np.linalg.norm(np.maximum(np.maximum(b[:2]-bb[3:5],bb[:2]-b[3:5]),0));assert gap>=GAP-1e-6;gaps.append(float(gap))
 out={'status':'layout only; whole-plate native audits pending','version':'O22-F4-Compact','source_release':str(D),'main_instances':len(main),'sample_instances':len(samples),'type_count':src['type_count'],'before_main_plates':23,'after_main_plates':len(packed)+1,'before_optional_plates':2,'after_optional_plates':len(sp),'bed_mm':[180,180,180],'minimum_model_edge_margin_mm':min(edge),'minimum_combined_body_fin_teeth_bbox_gap_mm':min(gaps),'all_meshes_unchanged':True,'all_print_rotations_unchanged':True,'packing':'Deterministic multi-start MaxRects, fixed print rotations, global optimum not claimed','seed':seed,'sample_seed':ss,'plates':plates};(S/'layout.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print('PACK230_DONE',len(plates),[(p['id'],len(p['items']))for p in plates],flush=True)
if __name__=='__main__':main()
