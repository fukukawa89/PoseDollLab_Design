"""Two-axis clavicle packaging experiment; keeps all original requested poses.
A shared clavicle-output/shoulder-input carrier is a layout hypothesis only.
Its manufacturing join, electronics and structural verification are not implied.
"""
from assemble_shoulders import profile,fk,rotation,H,G7,G9,OUT
from solid_ops import from_tri,tri,pose,rot,sha,save,md
import numpy as np,json,itertools,time,copy,sys
from pathlib import Path

from parts_library import library

MAPP={(x['character'],x['side']):x for x in json.loads((G9/'bounded_mapping.json').read_text())['characters']}
OLD={(x['character'],x['side']):x for x in json.loads((G7/'layout_search.json').read_text())['characters']}

def frames(char,x,y,zshift=0,progress=1.0,pose_index=None):
 context={}
 for side in ('l','r'):
  base=profile(char,side);p=copy.deepcopy(base);nodes={n['id']:n for n in p['nodes']};T0,A0=fk(base,{});sign=1 if side=='l' else -1;center=A0[f'clavicle_{side}.protract']['origin'];desired=np.array([x,sign*y,center[2]+zshift]);delta=T0['chest'][:3,:3].T@(desired-center)/1000
  a=nodes[f'clavicle_{side}.protract_frame'];a['parent_to_axis']['translation_m']=(np.array(a['parent_to_axis']['translation_m'])+delta).tolist()
  b=nodes[f'clavicle_{side}'];removed=np.array(b['parent_to_axis']['translation_m']);b['parent_to_axis']['translation_m']=[0,0,0]
  n=nodes[f'upperarm_{side}.flex_frame'];n['parent_to_axis']['translation_m']=(np.array(n['parent_to_axis']['translation_m'])+removed-delta).tolist()
  T,A=fk(p,{});assert np.linalg.norm(T[f'hand_tip_{side}'][:3,3]-T0[f'hand_tip_{side}'][:3,3])<1e-7
  u=A[f'clavicle_{side}.protract']['direction'];v=A[f'clavicle_{side}.elevate']['direction'];sgn=1 if np.cross(u,v)[1]*sign>0 else -1;B=np.c_[u,sgn*v,np.cross(u,sgn*v)];B=T['chest'][:3,:3].T@B
  oldprofile=json.loads((G7/f'{char}_{side}_profile.json').read_text());_,Ao=fk(oldprofile,{});rec=OLD[char,side];local={axis:np.linalg.inv(Ao[axis]['frame'])@np.array(rec['module_frames'][i][0]) for i,axis in enumerate(rec['axes'])}
  context[side]=(p,B,sgn,local)
 states=[]
 from module_frames import matrices
 for k,goal in enumerate(OLD[char,'l']['poses']):
  if pose_index is not None and k!=pose_index:continue
  q={**goal['angles_deg'],**OLD[char,'r']['poses'][k]['angles_deg']};q={key:value*(progress.get('l' if key.split('.')[0].endswith('_l') else 'r' if key.split('.')[0].endswith('_r') else 'common',1.) if isinstance(progress,dict) else progress) for key,value in q.items()};objects=[]
  for side in ('l','r'):
   p,B,sgn,local=context[side];T,A=fk(p,q);a=q.get(f'clavicle_{side}.protract',0);b=sgn*q.get(f'clavicle_{side}.elevate',0);base=T['chest'][:3,:3]@B;center=A[f'clavicle_{side}.protract']['origin']
   for name,M,body in [('clav_input',base,'chest'),('clav_ring',base@rot(0,a),'clav_ring_'+side),('clav_output',base@rot(0,a)@rot(1,b),'clav_output_'+side)]:
    F=np.eye(4);F[:3,:3]=M;F[:3,3]=center;objects.append({'id':side+'/'+name,'library':name,'body':body,'frame':F.tolist()})
   maps=MAPP[char,side];mp=maps['paths'][k];Bshoulder=T[f'clavicle_{side}'][:3,:3]@np.array(maps['mount_matrix']);origin=A[f'upperarm_{side}.flex']['origin']
   for name,M in matrices(mp['angles_deg'][round((progress[side] if isinstance(progress,dict) else progress)*(len(mp['angles_deg'])-1))],mp['zero_offsets_deg']).items():
    F=np.eye(4);F[:3,:3]=Bshoulder@M;F[:3,3]=origin;objects.append({'id':f'TUT_{side}/'+name,'library':f'{char}_{side}/'+name,'body':'clav_output_'+side if name=='P' else f'TUT_{side}/'+name,'frame':F.tolist()})
   for i in (5,6,7,8):
    rec=OLD[char,side];axis=rec['axes'][i];M=A[axis]['frame']@local[axis];C=M.copy();C[:3,:3]=rotation(A[axis]['direction'],q.get(axis,0))@M[:3,:3]
    for owner,F in [('parent',M),('child',C)]:objects.append({'id':axis+'/'+owner,'library':'M4_'+owner,'body':axis+'/'+owner,'frame':F.tolist()})
  states.append({'character':char,'pose':goal['pose'],'requested_angles_deg':q,'objects':objects})
 return states,context

def bounds(s):
 b=np.array(s.bounding_box());return np.array(list(itertools.product(*zip(b[:3],b[3:]))))

def relevant(a,b):
 if a['body']==b['body']:return False
 # This experiment evaluates the newly proposed clavicle against everything,
 # and shoulder against retained other modules. Intra-shoulder checked separately.
 if 'clav_' in a['library'] or 'clav_' in b['library']:return True
 if a['id'].startswith('TUT_') != b['id'].startswith('TUT_'):return True
 return a['id'].startswith('TUT_l') and b['id'].startswith('TUT_r')

def main():
 sources=[__file__,OUT/'printed_core/parts.npz',OUT/'braked_module/build.json',G9/'bounded_mapping.json',G7/'layout_search.json']+list((OUT/'braked_module').glob('*.npz'))+list((H/'generated/revO10/runs/o10_20260926_r1/old_modules').glob('*.npz'));before={str(Path(p).relative_to(H)):sha(p) for p in sources}
 lib=library();bb={k:bounds(s) for k,s in lib.items()};trial=[];start=time.time()
 # Whole original bilateral pose set used for the inexpensive conservative bounds screen.
 candidates=[tuple(map(float,sys.argv[sys.argv.index('--candidate')+1].split(',')))] if '--candidate' in sys.argv else itertools.product((-50,-40,-30,-20,-10),(20,26,32,38),(-10,0,10))
 for x,y,z in candidates:
  states,_=frames('manny',x,y,z);score=0.;n=0
  for state in states:
   rows=[]
   for ob in state['objects']:
    F=np.array(ob['frame']);p=bb[ob['library']]@F[:3,:3].T+F[:3,3];rows.append((ob,p.min(0),p.max(0)))
   for (a,al,ah),(b,bl,bh) in itertools.combinations(rows,2):
    if not relevant(a,b):continue
    if a['library'].startswith('clav') and b['library'].startswith('clav') and a['id'][0]==b['id'][0]:continue
    overlap=np.minimum(ah,bh)-np.maximum(al,bl)
    if np.all(overlap>0):score+=float(np.prod(overlap));n+=1
  trial.append({'x_mm':x,'lateral_mm':y,'z_shift_mm':z,'aabb_overlap_score_mm3':score,'aabb_pairs':n})
 trial.sort(key=lambda r:r['aabb_overlap_score_mm3']);save('clavicle_trial/search.json',{'candidates':trial,'scope':'Conservative broadphase ranking only. Positive AABB overlap is not a collision and low score is not acceptance.','elapsed_s':time.time()-start});print('ranked',trial[:5],flush=True)
 chosen=trial[0];allrows=[]
 for char in ('manny','quinn'):
  states,context=frames(char,chosen['x_mm'],chosen['lateral_mm'],chosen['z_shift_mm']);save(f'clavicle_trial/{char}_states.json',{'candidate':chosen,'states':states,'scope':'Shared output carrier proposed but not modeled. Not an assembly pass.'})
  for side,(p,B,sgn,local) in context.items():save(f'clavicle_trial/{char}_{side}_profile.json',p)
  for state in states:
   world={};worldbb={};findings=[]
   for ob in state['objects']:
    F=np.array(ob['frame']);world[ob['id']]=pose(lib[ob['library']],F[:3,:3],F[:3,3]);p=bb[ob['library']]@F[:3,:3].T+F[:3,3];worldbb[ob['id']]=(p.min(0),p.max(0))
   for a,b in itertools.combinations(state['objects'],2):
    if not relevant(a,b):continue
    al,ah=worldbb[a['id']];bl,bh=worldbb[b['id']]
    if np.any(np.minimum(ah,bh)<=np.maximum(al,bl)):continue
    v=(world[a['id']]^world[b['id']]).volume()
    if v>1e-4:findings.append({'pair':[a['id'],b['id']],'volume_mm3':v})
   allrows.append({'character':char,'pose':state['pose'],'findings':findings});print(char,state['pose'],len(findings),[(r['pair'],round(r['volume_mm3'],2)) for r in findings],flush=True)
   save('clavicle_trial/motion.json',{'input_sha256':before,'complete':False,'candidate':chosen,'cases':allrows,'elapsed_s':time.time()-start,'scope':'New two-axis clavicle and braked shoulder versus actual retained arm modules. Shared output-carrier join not yet modeled; same rigid-body overlaps not certified as assembled. Missing trunk, neck, shell, wires, electronics and sensor fields. Not whole arm acceptance.','manufacturing_released':False})
 assert before=={str(Path(p).relative_to(H)):sha(p) for p in sources},'Inputs changed during run'
 report=json.loads((OUT/'clavicle_trial/motion.json').read_text());report['complete']=True;save('clavicle_trial/motion.json',report)
if __name__=='__main__':main()



