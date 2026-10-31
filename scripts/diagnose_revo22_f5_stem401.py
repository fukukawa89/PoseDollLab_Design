import sys,json,numpy as np
sys.path.insert(0,'PoseDoll_HW44_Plan/design/scripts')
from search_revo22_f5_orientation268 import O
from build_revo22_fins import solid,md,union,box
from verify_revo22_x062_removal245 import exact_clear
p='X046';l='cap396_0';a=O/'candidates'/p/l;n=np.load(a/'parts'/f'{p}.npz');d=json.loads((a/'design'/f'{p}.json').read_text());body=solid(n['v'],n['f']);teeth=solid(n['teeth_v'],n['teeth_f']);r=d['local_route_repairs'][57];print('RECORD',r,flush=True);a0=np.array(r['root']);b=np.array(r['tip']);mid=b-[0,0,r.get('taper_height_mm',.9)];xy=np.array([[-1,-1,0],[1,-1,0],[1,1,0],[-1,1,0]]);tt=union([md.Manifold.hull_points(np.r_[xy*.4+a0,xy*.4+mid]),md.Manifold.hull_points(np.r_[xy*.4+mid,xy*(r['tip_width_mm']/2)+b])]);dr=np.array(r['stem_removal_vector']);dr/=np.linalg.norm(dr)
for name,s in [('ideal',tt),('actual',tt^teeth)]:
 print(name,'outside',(s-teeth).volume(),'overlap',(s^body).volume(),'withdraw',exact_clear(s-body,body,dr*220),flush=True)
