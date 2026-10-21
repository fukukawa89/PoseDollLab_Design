"""Check the retained attachment solids with their eventual rigid-body associations.
This exposes contacts inherited from endpoints before any connecting rod is added.
"""
from common import *
from layout_fullbody import *
from carriers_swept import anchors,ASSEMBLY_POSE
from connected import adjacent_pairs
from collision_fast import first_cross

def associated_parts(char,angles,overrides=None,only=None):
 pp,meta,st,f,pr=build(char,angles,overrides,only);aa=anchors(st,meta)
 for body,ends in aa.items():
  ids=[e['part'] for e in ends];s=md.Manifold()
  for k in ids:s+=pp.pop(k)
  key='frame/'+body;pp[key]=s;meta[key]={'body':body,'module':key,'modules':sorted(set(k.split('/')[0] for k in ids)),'sku':None}
  for k in ids:del meta[k]
 return pp,meta,f

def associated_hit(char,a,ov=None,only=None):
 pp,meta,f=associated_parts(char,a,ov,only)
 if f:return {'mapping_failures':f}
 groups={}
 for k in pp:groups.setdefault(meta[k]['module'],[]).append(k)
 adj=adjacent_pairs(char);pairs=set()
 for ga,gb in itertools.combinations(groups,2):
  ma,mb=meta[groups[ga][0]],meta[groups[gb][0]];aa=ma.get('modules',[ga]);bb=mb.get('modules',[gb])
  if set(aa)&set(bb) or any(frozenset((x,y)) in adj for x in aa for y in bb):pairs.add(frozenset((ga,gb)))
 return first_cross(pp,meta,pairs,skip_same_body=True)
