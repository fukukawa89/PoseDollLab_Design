"""Integrate one clavicle output fork and one shoulder input case half.
Real same-body printed bridge, stock screws remain separate. Endpoint packing
study only: no stress/creep/cable/slicer or manufacturing acceptance.
"""
from solid_ops import *
from parts_library import Parts,library
from clavicle_trial import bounds
from fullbody_stage import geometry_model
import itertools,copy

def beam(a,b,r):
 a=np.array(a,float);b=np.array(b,float);z=b-a;length=np.linalg.norm(z);z/=length
 u=np.eye(3)[np.argmin(abs(z))];x=np.cross(u,z);x/=np.linalg.norm(x)
 return pose(md.Manifold.cylinder(length,r,circular_segments=32),np.c_[x,np.cross(z,x),z],a)+md.Manifold.sphere(r,circular_segments=32).translate(a)+md.Manifold.sphere(r,circular_segments=32).translate(b)

def make(char,side,st,h,skew,r=3):
 ob={o['id']:np.array(o['frame']) for o in st['objects']};relative=np.linalg.inv(ob[f'{side}/clav_output'])@ob[f'TUT_{side}/P']
 core=from_tri(np.load(OUT/'printed_core/parts.npz')['C02']);raw=np.load(OUT/f'braked_module/{char}_{side}.npz');case=from_tri(raw['P_case_plus']);case=pose(case,relative[:3,:3],relative[:3,3])
 collar=cylinder(8,30.5,35)-cylinder(4.5,30.4,35.1)
 pad=pose(box([-4,10,-33.8],[4,18,-30.7]),relative[:3,:3],relative[:3,3])
 a=np.array([0,-6,33.]);b=relative[:3,:3]@np.array([0,15,-32.3])+relative[:3,3]
 mid=(a+b)/2;mid[2]=max(a[2],b[2])+h;mid[0]+=skew*(1 if side=='l' else -1)
 c=relative[:3,:3]@np.array([0,32,-32.3])+relative[:3,3]
 last=pose(box([-3,15,-35.3],[3,35,-30.7]),relative[:3,:3],relative[:3,3])
 bridge=collar+pad+beam(a,mid,r)+beam(mid,c,r)+last
 connected=core+case+bridge
 return bridge,connected,relative

def main():
 lib=library();world={};states={}
 # P case_plus is the one intentionally integrated printed piece; other case
 # halves, screws and nuts remain collision obstacles, even on the same body.
 for char,side in itertools.product(('manny','quinn'),('l','r')):
  raw=np.load(OUT/f'braked_module/{char}_{side}.npz')
  lib[f'{char}_{side}/P_except_integrated_plus']=Parts([from_tri(t) for k,t in raw.items() if k.startswith('P_') and k!='P_case_plus'])
 for char in ('manny','quinn'):
  states[char]=json.loads((OUT/f'clavicle_trial/{char}_states.json').read_text())['states']
  world[char]=[]
  for st in states[char]:
   obstacles=[]
   for o in st['objects']:
    key=o['library'];F=np.array(o['frame'])
    obstacles.append((o,F,pose(lib[key],F[:3,:3],F[:3,3])))
   world[char].append(obstacles)
 def evaluate(h,skew,chosen):
  built={(ch,s):make(ch,s,states[ch][0],h,skew) for ch,s in itertools.product(('manny','quinn'),('l','r'))};rows=[]
  for ch,i in chosen:
   st=states[ch][i];ob={o['id']:np.array(o['frame']) for o in st['objects']};hits=[];placed={}
   for side in ('l','r'):
    br,connected,relative=built[ch,side];F=ob[f'{side}/clav_output'];actual=np.linalg.inv(F)@ob[f'TUT_{side}/P'];assert np.max(abs(actual-relative))<1e-6
    part=pose(br,F[:3,:3],F[:3,3]);placed[side]=part;pb=part.bounding_box()
    for o,Go,original in world[ch][i]:
     if o['id']==f'{side}/clav_output':continue
     other=original
     if o['id']==f'TUT_{side}/P':other=pose(lib[f'{ch}_{side}/P_except_integrated_plus'],Go[:3,:3],Go[:3,3])
     qb=other.bounding_box()
     if np.any(np.minimum(pb[3:],qb[3:])<=np.maximum(pb[:3],qb[:3])):continue
     v=(Parts([part])^other).volume()
     if v>1e-4:hits.append({'pair':[f'{side}/integrated_bridge',o['id']],'sum_piece_overlap_mm3':v})
   v=(placed['l']^placed['r']).volume()
   if v>1e-4:hits.append({'pair':['l/integrated_bridge','r/integrated_bridge'],'sum_piece_overlap_mm3':v})
   rows.append({'character':ch,'pose':st['pose'],'findings':hits})
  return {'rise_mm':h,'side_skew_mm':skew,'beam_radius_mm':3,'failed_endpoints':sum(bool(r['findings']) for r in rows),'sum_overlap_mm3':sum(f['sum_piece_overlap_mm3'] for r in rows for f in r['findings']),'single_printed_components':{ch+'_'+s:len(v[1].decompose()) for (ch,s),v in built.items()},'cases':rows},built
 risk=[(ch,i) for ch in states for i,st in enumerate(states[ch]) if st['pose'] in ('neutral','clavicle_l.protract_20','clavicle_l.protract_-20','clavicle_l.elevate_40','upperarm_l.abduct_120','upperarm_l.abduct_160','arms_overhead','elbow_l.flex_140')]
 rows=[]
 for h,skew in itertools.product((0,8,16,24),(0,8,-8)):
  row,_=evaluate(h,skew,risk);rows.append(row)
  save('carriers/search.json',{'complete':False,'candidates':rows});print('carrier',h,skew,'fail',row['failed_endpoints'],row['single_printed_components'],flush=True)
 rows.sort(key=lambda r:(max(r['single_printed_components'].values())!=1,r['failed_endpoints'],r['sum_overlap_mm3']))
 best=rows[0];report,built=evaluate(best['rise_mm'],best['side_skew_mm'],[(ch,i) for ch in states for i in range(len(states[ch]))])
 save('carriers/search.json',{'complete':True,'candidates':rows,'scope':'Risk-pose search; only selected candidate receives full endpoint audit.'})
 save('carriers/endpoints.json',{'complete':True,**report,'scope':'Integral printed fork-to-one-case-half bridge, all 102 endpoints, other case halves/metal included even when same body. Existing unlike module collisions tracked separately. Missing full torso, arm carriers, harness, stress, tolerances, tool/assembly path, full motion.'})
 target=OUT/'carriers';target.mkdir(exist_ok=True)
 np.savez_compressed(target/'parts.npz',**{ch+'_'+s+'_bridge':tri(v[0]) for (ch,s),v in built.items()},**{ch+'_'+s+'_integrated':tri(v[1]) for (ch,s),v in built.items()})
 print('carrier final failed',report['failed_endpoints'],flush=True)
if __name__=='__main__':main()
