"""Full body-group Boolean motion screen of the braked module, retaining contacts."""
from solid_ops import *
import itertools,time
from build_finite_twist import D

def main():
 sources=[Path(__file__),Path(__file__).with_name('solid_ops.py'),OUT/'braked_module/build.json',OUT/'printed_core/parts.npz',G9/'bounded_mapping.json',G8/'fastened_core/fasteners.npz']+list((OUT/'braked_module').glob('*.npz'));before={str(p.relative_to(H)):sha(p) for p in sources}
 assert json.loads((OUT/'braked_module/build.json').read_text())['source_sha256']==sha(OUT/'printed_core/parts.npz'), 'Stale assembly'
 rows=[];data=json.loads((G9/'bounded_mapping.json').read_text());start=time.time()
 for c in data['characters'][:1] if '--quick' in sys.argv else data['characters']:
  key=c['character']+'_'+c['side'];p=OUT/'braked_module'/f'{key}.npz';raw={k:from_tri(t) for k,t in dict(np.load(p)).items()};groups={n:md.Manifold() for n in ['P','C01','ring','C02','D']}
  for k,s in raw.items():
   role='P' if k.startswith('P_') else 'D' if k.startswith('D_') else k if k in ['C01','C02'] else 'ring';groups[role]+=s
  for t in np.load(G8/'fastened_core/fasteners.npz').values():groups['ring']+=from_tri(t)
  assert all(s.volume()>0 for s in raw.values()), 'Empty modeled part'
  targets=c['paths']
  if '--quick' in sys.argv:targets=[{'pose':f'{a}_{b}','angles_deg':[[0,a,b,0]],'zero_offsets_deg':c['paths'][0]['zero_offsets_deg']} for a,b in [(0,0),(25,96.2),(-25,-96.2),(0,75),(0,98)]]
  for path in targets:
   p0,a,b,s=np.array(path['angles_deg'][-1])+path['zero_offsets_deg'];P=rot(2,p0);A=P@rot(0,a);B=A@rot(1,b);M={'P':np.eye(3),'C01':P,'ring':A,'C02':B,'D':B@rot(2,s)@D};world={k:pose(g,M[k]) for k,g in groups.items()};hits=[]
   for x,y in itertools.combinations(groups,2):
    inter=world[x]^world[y];v=inter.volume()
    if v>1e-4:hits.append({'pair':[x,y],'volume_mm3':v,'bounds_mm':list(inter.bounding_box())})
   row={'group':key,'pose':path['pose'],'q_relative_deg':path['angles_deg'][-1],'findings':hits};rows.append(row);print(key,path['pose'],[(h['pair'],round(h['volume_mm3'],4)) for h in hits],flush=True)
   save('braked_module/'+('quick_motion.json' if '--quick' in sys.argv else 'target_motion.json'),{'input_sha256':before,'complete':False,'cases':rows,'elapsed_s':time.time()-start,'scope':'Complete rigid-body groups in their physical frames; nominal endpoint check only.','manufacturing_released':False})
 after={str(p.relative_to(H)):sha(p) for p in sources};assert after==before,'Inputs changed'
 filename='braked_module/'+('quick_motion.json' if '--quick' in sys.argv else 'target_motion.json')
 report=json.loads((OUT/filename).read_text());report['complete']=True;save(filename,report)
if __name__=='__main__':main()


