"""Targeted chest orientations derived from its real shoulder-bore axis."""
import numpy as np,json,time,math
from explore_revo22_f3 import *
from search_revo22_f2_orientations import frame
from pack_revo22_a1mini import read_mesh
import check_revo22_f3_layers as layer
import repair_revo22_f3_contacts as repair
import repair_revo22_f3_side_contacts as side
pid='X046';item=next(i for p in json.loads((B/'a1mini/manifest.json').read_text())['plates'] for i in p['items'] if i['id']==pid)
vols=next(x['volumes'] for x in json.loads((B/'a1mini_supports/design/all_protected_volumes.json').read_text())['objects'] if x['id']==pid)
v,f=read_mesh(B/item['source_3mf']);old=np.array(json.loads((OLD/'design/X046.json').read_text())['orientation']['gravity_in_source'])
axis=np.array(next(x for x in vols if x['feature']=='chest_C02_-1_D4_shoulder_hole')['local_to_source_print_matrix'])[:3,2]
axis=axis-old*np.dot(old,axis);axis/=np.linalg.norm(axis)
out=[]
for angle in [-35,-20,20,35]:
    d=old*math.cos(math.radians(angle))+axis*math.sin(math.radians(angle))
    M=frame(d);best=None
    for zangle in range(0,90,15):
        z=math.radians(zangle);Q=np.array([[math.cos(z),-math.sin(z),0],[math.sin(z),math.cos(z),0],[0,0,1.]])@M
        vv=v@Q.T;size=np.ptp(vv,axis=0);cost=size[0]*size[1]+10000*max(0,max(size[:2])-162)**2
        if best is None or cost<best[0]:best=(cost,Q,-vv.min(0),size)
    _,M,tr,size=best;label='bore_'+str(angle).replace('-','minus')
    dest=O/'candidates/X046'/label
    for sub in ['parts','design','verification']:(dest/sub).mkdir(parents=True,exist_ok=True)
    ori={'matrix':M.tolist(),'source_translation_mm':tr.tolist(),'gravity_in_source':d.tolist(),'size_mm':size.tolist(),'bore_directed_tilt_deg':angle}
    builder.O=dest;builder.choose=lambda _:ori;builder.AXIS=90;builder.FACE_FILTER=None;builder.PITCH_OVERRIDE=8;builder.THICKNESS_OVERRIDE=2.;builder.NORMAL_THRESHOLD=-.3;builder.SEGMENT_OVERRIDE=48
    layer.O=dest;repair.O=dest;side.O=dest
    builder.make(pid,item,vols);layer.check(pid);repair.repair(pid);side.repair_side(pid)
    r=audit(pid,dest);out.append({'label':label,'orientation':ori,'metrics':r})
    (O/'candidates/X046/bore_comparison.json').write_text(json.dumps(out,indent=2),encoding='utf8')
    print('BORE_CANDIDATE',label,len(r['layer_islands']),sum(i['area_mm2'] for i in r['layer_islands']),r['max_long_overhang_area_mm2'],r['support_volume_mm3']/1000,flush=True)

