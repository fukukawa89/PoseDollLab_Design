import json,sys,time
import numpy as np
from explore_revo22_f3 import *
from search_revo22_f2_orientations import frame
from pack_revo22_a1mini import read_mesh
pid='X046';it=next(i for p in json.loads((B/'a1mini/manifest.json').read_text())['plates'] for i in p['items'] if i['id']==pid)
vols=next(x['volumes'] for x in json.loads((B/'a1mini_supports/design/all_protected_volumes.json').read_text())['objects'] if x['part']==it['part'])
v,f=read_mesh(B/it['source_3mf']);old=json.loads((OLD/'design/X046.json').read_text())['orientation'];records=[]
for label,d,axis in [('old_cross',old['gravity_in_source'],90),('diagonal45',[1,0,-1],0),('diagonal45_cross',[1,0,-1],90),('spatial',[.65,.38,-.658],0),('spatial_cross',[.65,.38,-.658],90)]:
 dest=O/'candidates/X046'/label
 for folder in ['parts','design','verification']:(dest/folder).mkdir(parents=True,exist_ok=True)
 M=frame(d);vv=v@M.T;off=-vv.min(0)
 ori={'matrix':M.tolist(),'source_translation_mm':off.tolist(),'gravity_in_source':M[2].tolist(),'size_mm':np.ptp(vv,axis=0).tolist(),'candidate_label':label}
 builder.O=dest;builder.choose=lambda _:ori;builder.AXIS=axis
 t=time.time();builder.make(pid,it,vols);r=audit(pid,dest);records.append({'label':label,'orientation':ori,'axis':axis,'metrics':r,'elapsed_s':time.time()-t})
 (O/'candidates/X046/comparison_cross.json').write_text(json.dumps(records,indent=2),encoding='utf8')
