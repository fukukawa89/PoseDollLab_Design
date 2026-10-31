"""Clear witnessed fine-step metal sweeps in a NEW carrier variant.
Only relieved printed stock changes; original witness and baseline remain intact.
"""
from common import *
from connected import carrier_inputs
from layout_fullbody import build,fk
from raw_paths import paths


def main(char='quinn'):
 base='carriers_finished';dst='carriers_refined';rr,frames,_=carrier_inputs(char,base)
 witness=OUT/f'connected/{char}_{base}_raw_paths.json';d=read(witness);cuts={};records=[]
 if d.get('status') not in ('STRUCTURAL_COLLISION','SAMPLED_STRUCTURE_CLEAR'):raise ValueError('incomplete fine-step evidence')
 cases={r['pose']:r for r in d['cases'] if r['findings']}
 pp,_,_,_,_=build(char,{})
 _,mm,_,_,_=build(char,{},geometry=False)
 for name,meta,T,detail in paths(char):
  if name not in cases:continue
  for hit in cases[name]['findings']:
   a,b=hit['pair']
   if a.startswith('frame/'):a,b=b,a
   if not b.startswith('frame/') or a.startswith('frame/') or mm[a]['sku'] is None:raise RuntimeError(('Requires reroute',hit))
   body=b.split('/',1)[1];I=np.linalg.inv(T[body]);M=I@meta[a]['transform']@np.linalg.inv(mm[a]['transform']);metal=pose(pp[a],M[:3,:3],M[:3,3]);guard=md.Manifold.batch_hull([metal.translate(v) for v in itertools.product((-.4,.4),repeat=3)]);cuts.setdefault(body,[]).append(guard);records.append({'pose':name,'body':body,'obstacle':a,'original_overlap_mm3':hit['overlap_mm3'],'guard_mm':.4})
 for body,guards in cuts.items():
  old=frames[body];new=old-md.Manifold.batch_boolean(guards,md.OpType.Add);lost=old.volume()-new.volume()
  if solid_count(new)!=1 or lost/old.volume()>.015:raise RuntimeError(('Relief must be rerouted',body,lost,old.volume()))
  frames[body]=new
  rec=next(r for r in rr['frames'] if r['body']==body);rec['mesh']=mesh_record(new);rec['fine_path_relief']={'removed_mm3':lost,'removed_fraction':lost/old.volume(),'scope':'Small access relief; physical strength and loaded deflection remain unqualified.'}
 path=OUT/f'{dst}/{char}_parts.npz';path.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(path,**{k:tri(v) for k,v in frames.items()});rr['input_sha256'].update({str(p):sha(p) for p in [Path(__file__),witness,OUT/f'{base}/{char}_parts.npz',OUT/f'{base}/{char}_routing.json']});rr.update(status='ROUTING_GENERATED',mesh_sha256=sha(path),fine_relief_witnesses=records)
 save(f'{dst}/{char}_routing.json',rr);print('REFINED',char,records,flush=True)
if __name__=='__main__':main(sys.argv[1] if len(sys.argv)>1 else 'quinn')
