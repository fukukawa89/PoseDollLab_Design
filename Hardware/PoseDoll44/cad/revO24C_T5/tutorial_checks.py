"""Replay every tutorial state and test exported rigid meshes along every path."""
from arm_kit import *
import collections

def main():
 data=json.loads((OUT/'tutorial/steps.json').read_text('utf8'));geo=sha(OUT/'assembly_meshes.npz');assert data['geometry_sha256']==geo
 rows={r['id']:r for r in json.loads((OUT/'assembly.json').read_text('utf8'))['parts']};z=np.load(OUT/'assembly_meshes.npz')
 P={id:md.Manifold(md.Mesh(z['v'+str(r['index'])].astype(np.float32),z['f'+str(r['index'])].astype(np.uint32))) for id,r in rows.items()}
 B={id:np.array(p.bounding_box()).reshape(2,3) for id,p in P.items()}
 failures=[];checks={};details=[];sample_count=0
 for st,L in data['lessons'].items():
  state={};introduced=[];local_samples=0
  for s in L['steps']:
   assert state==s['before'],(st,s['n'],'before mismatch')
   if s['kind']=='add':
    assert len(s['ids'])==1 and s['ids'][0] not in introduced
    introduced+=s['ids']
   if s['kind']=='reinstall':assert all(id in introduced and id not in state for id in s['ids'])
   moving=set(s['paths']);fixed={id:P[id].translate(off) for id,off in state.items() if id not in moving};fb={id:B[id]+state[id] for id in fixed}
   step_hits=[];ns=0
   for id,path in s['paths'].items():
    path=np.array(path,float)
    for start,end in zip(path,path[1:]):
     count=max(2,int(np.ceil(np.linalg.norm(end-start)/.5))+1)
     for t in np.linspace(0,1,count):
      off=start*(1-t)+end*t;bb=B[id]+off;ss=None
      for oid,ob in fb.items():
       if not np.all(np.minimum(bb[1],ob[1])-np.maximum(bb[0],ob[0])>.008):continue
       if ss is None:ss=P[id].translate(off)
       vol=(ss^fixed[oid]).volume()
       if vol>.02:
        step_hits.append(dict(a=id,b=oid,volume_mm3=round(vol,6),offset_mm=off.tolist()));break
      ns+=1
   state={**state,**{id:path[-1] for id,path in s['paths'].items()}}
   if s['kind']=='remove':
    for id in s['ids']:del state[id]
   assert state==s['after'],(st,s['n'],'after mismatch')
   if step_hits:failures.append(dict(station=st,step=s['n'],title=s['title'],hits=step_hits[:6]))
   details.append(dict(station=st,step=s['n'],kind=s['kind'],samples=ns,passed=not step_hits));local_samples+=ns
  expected={id for id,p in rows.items() if p['station']==st}
  checks[st+'_inventory_once']=set(introduced)==expected and len(introduced)==len(expected)
  checks[st+'_all_final_offsets_zero']=all(np.max(np.abs(off))<1e-8 for off in state.values())
  expectedfinal=expected-({'W3-09','WPALM_B','WPALM_W','WPALM_N'} if st=='W' else set())
  checks[st+'_final_bench_parts']=set(state)==expectedfinal
  # Final stationary assembly must also have no overlaps between pairs that moved together.
  ids=list(state);finalhits=[]
  for i,id in enumerate(ids):
   for oid in ids[i+1:]:
    if np.all(np.minimum(B[id][1],B[oid][1])-np.maximum(B[id][0],B[oid][0])>.008):
     vol=(P[id]^P[oid]).volume()
     if vol>.02:finalhits.append(dict(a=id,b=oid,volume_mm3=round(vol,6)))
  if finalhits:failures.append(dict(station=st,step='final',hits=finalhits))
  sample_count+=local_samples;print(st,'steps',len(L['steps']),'samples',local_samples,'failures',len(failures),flush=True)
 counts=collections.Counter(p['sku'] for p in data['catalog'].values() if p['sku']);bom={r['sku']:r['qty'] for r in json.loads((OUT/'BOM.json').read_text('utf8'))};checks['exact_full_BOM_including_alternate_palm']=counts==bom
 checks['all_washers_nuts_springs_have_orientation']=all(p['orientation'] for p in data['catalog'].values() if p['sku'] in ['W2','W3','W4','RW3','FW4','N2','N3','A8'])
 checks['no_nylon_nuts_in_T5']=not any((p['sku'] or '').startswith('NL') for p in data['catalog'].values())
 # Inspect actual cone vertices: the annotated direction must be the raised
 # inner rim, not inferred from the centre of a long shoulder screw.
 spring_faces=[]
 for id,p in data['catalog'].items():
  if p['sku']!='A8':continue
  v=z['v'+str(rows[id]['index'])];o=p['orientation'];n=np.array(o['normal']);dv=v-np.array(o['center']);radius=np.linalg.norm(dv-np.outer(dv@n,n),axis=1)
  rise=float(np.mean(v[abs(radius-2.1)<1e-4]@n)-np.mean(v[abs(radius-4)<1e-4]@n));spring_faces.append(dict(id=id,inner_rim_rise_mm=rise,passed=rise>.05))
 checks['spring_arrows_match_actual_cone_mesh']=all(r['passed'] for r in spring_faces)
 report=dict(passed=all(checks.values()) and not failures,geometry_sha256=geo,tutorial_edition=data['tutorial_edition'],checks=checks,steps=sum(len(l['steps']) for l in data['lessons'].values()),unique_components=len(data['catalog']),path_samples=sample_count,max_path_step_mm=.5,collision_volume_threshold_mm3=.02,details=details,failures=failures,scope='Every add, subassembly move, removal and reinstall against all previously present exported meshes. Final independent modules checked. Screw threads, hand access, elastic preload and physical tests are not simulated.')
 report['spring_faces']=spring_faces
 put(OUT/'verification/tutorial_paths.json',report);print(json.dumps(dict(passed=report['passed'],checks=checks,failures=failures),ensure_ascii=False),flush=True)
 if not report['passed']:raise SystemExit(1)

if __name__=='__main__':main()
