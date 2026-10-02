"""Common A/C mechanical screening with explicit pivot offsets and actual imported parts.
This exposes unresolved shared constraints. It is NOT a completed load-bearing arm:
mounting yokes, shell, precision stops and continuous swept cable tubes remain open.
"""
from pathlib import Path
import argparse,json,hashlib,sys,itertools,math,copy
import numpy as np
import cadquery as cq
ROOT=Path(__file__).resolve().parents[4];HW=ROOT/'Hardware/PoseDoll44'
sys.path.insert(0,str(ROOT/'scripts'))
from study_revo import anatomy
from model import fk,rotation
from packaging_revo2 import inside_surface
from study_revo2 import measure_character

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def boxbb(bb):return cq.Workplane('XY').box(*[bb[i+3]-bb[i] for i in range(3)]).translate([(bb[i+3]+bb[i])/2 for i in range(3)]).val()
def bb(s):
 b=s.BoundingBox();return [b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax]
def corners(b):return np.array(list(itertools.product(*[(b[i],b[i+3]) for i in range(3)])))
def apply(points,T):return np.asarray(points)@T[:3,:3].T+T[:3,3]
def alignment(z):
 z=np.asarray(z,float);x=np.cross([0,1,0] if abs(z[1])<.9 else [1,0,0],z);x/=np.linalg.norm(x);y=np.cross(z,x);return np.column_stack([x,y,z])
def located(shape,M):
 assert np.max(np.abs(M[:3,:3].T@M[:3,:3]-np.eye(3)))<1e-9 and np.linalg.det(M[:3,:3])>0
 plane=cq.Plane(origin=tuple(M[:3,3]),xDir=tuple(M[:3,0]),normal=tuple(M[:3,2]))
 return shape.moved(cq.Location(plane))

def matrix(R,xyz):
 m=np.eye(4);m[:3,:3]=R;m[:3,3]=xyz;return m

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 metadata=[Path(__file__),ROOT/'scripts/study_revo.py',ROOT/'scripts/study_revo2.py',ROOT/'scripts/packaging_revo2.py',HW/'cad/model.py',HW/'cad/revE/character_reference.py',HW/'generated/revO3/runs/o3_20260924_r3/joint/manifest.json',HW/'verification/revO4/runs/o4_20260924_h3/pcba_geometry.json']
 for char in ('manny','quinn'):
  metadata += [HW/f'reference/ue58/{char}_mesh_probe.json',HW/f'reference/ue58/{char}_geometry.json',HW/f'mechanical_manifest/physical_{char}_44_revG_humanform_trial.json']
 consumed={p.relative_to(ROOT).as_posix():sha(p) for p in metadata}
 old=HW/'generated/revO4/runs/o4_20260924_h3';pcpath=HW/'verification/revO4/runs/o4_20260924_h3/pcba_geometry.json';pc=json.loads(pcpath.read_text());boards={b['kind']:b for b in pc['boards']}
 jointdir=HW/'generated/revO3/runs/o3_20260924_r3/joint';jm=json.loads((jointdir/'manifest.json').read_text());cache={}
 def load(path,expected=None):
  path=path.resolve();name=path.relative_to(ROOT).as_posix();h=sha(path)
  if expected:assert h==expected,name
  consumed[name]=h
  if name not in cache:cache[name]=cq.importers.importStep(str(path)).val()
  return cache[name]
 exact_cache={}
 parent=[];child=[]
 for part in jm['parts']:
  s=load(jointdir/part['step_file'],part['step_sha256'])
  if part['part_id']=='measurement_shaft':s=load(a.out.parent/'output/extended_measurement_shaft.step')
  (child if part['owner']=='child' else parent).append(s)
 child.extend(load(a.out.parent/'output'/(name+'.step')) for name in ('output_clamp_minus','output_clamp_plus'))
 parent=cq.Compound.makeCompound(parent);child=cq.Compound.makeCompound(child)
 pcb={}
 for name in ('A_proximal5','A_distal4','proximal5_rs485','distal4_rs485_top'):
  pcb[name]=[(obj,load(old/obj['file'],obj['sha256'])) for obj in boards[name]['objects'] if 'bend_R4' not in obj['id']]
 n2=load(a.out/'N2_inherited.step');n2bb=bb(n2);n2=n2.translate(tuple(-(np.array(n2bb[:3])+n2bb[3:])/2))
 report={'schema':'o5-common-arm-screen-v1','scope':'POSITIONED_NATIVE_PARTS_AND_SAMPLED_ENVELOPES_NOT_COMPLETE_MANUFACTURING_ASSEMBLY','characters':[],'physical_tested':False,'manufacturing_released':False}
 basis=np.array([[0,0,1],[1,0,0],[0,1,0]],float)
 for char in ('manny','quinn'):
  profile=anatomy(char,480);offsets={'clavicle_l':[0,.024,0],'upperarm_l.abduct_frame':[0,0,-.028],'upperarm_l':[0,0,-.028],'hand_l':[0,0,-.025]}
  for node in profile['nodes']:
   if node['id'] in offsets:node['parent_to_axis']['translation_m']=offsets[node['id']]
  profile['profile_id']='o5_'+char+'_left_arm_offset_trial';profile['status']='COLLISION_SCREEN_ONLY_NOT_DEVICE_CALIBRATION_OR_FROZEN_DESIGN'
  (a.out/(char+'_offset_trial.json')).write_text(json.dumps(profile,indent=2)+'\n')
  ids=[n['axis_id'] for n in profile['nodes'] if n.get('axis_id') and any(n['axis_id'].startswith(x) for x in ('clavicle_l.','upperarm_l.','elbow_l.','forearm_l.','hand_l.'))];assert len(ids)==9
  poses=[('neutral',{})]
  for degrees in range(10,161,10):poses.append(('raise_'+str(degrees),{'upperarm_l.flex':degrees,'elbow_l.flex':min(degrees*.7,110)}))
  for degrees in range(-60,61,15):poses.append(('twist_'+str(degrees),{'upperarm_l.abduct':45,'elbow_l.flex':90,'upperarm_l.twist':degrees}))
  source=measure_character(char);verts=source['vertices_mm'];faces=np.array(source['geometry']['triangles'])
  variants=[]
  for variant,prox,dist in [('A','A_proximal5','A_distal4'),('C','proximal5_rs485','distal4_rs485_top')]:
   cases=[];harness=[]
   for pose_name,pose in poses:
    T,axes=fk(profile,pose);objects=[];mounts={};render=[]
    for aid in ids:
     axis=axes[aid];node=next(n for n in profile['nodes'] if n.get('axis_id')==aid);local=alignment(node['axis_local'])
     # Move a module along its own axis (not change the physical pivot); output collar lies near the pivot.
     M=axis['frame']@matrix(local,[0,0,0]);M[:3,3]+=M[:3,2]*36
     Rchild=M.copy();Rchild[:3,:3]=rotation(axis['direction'],pose.get(aid,0))@M[:3,:3]
     mounts[aid]=(M,Rchild)
     for suffix,shape,trans in [('stator',parent,M),('rotor',child,Rchild)]:objects.append((aid+'_'+suffix,aid,'physical',shape,trans))
    positions={'N3_prox':('chest',np.array([-8,23,16]),prox),'N4_prox':('chest',np.array([-8,-23,16]),prox),'D3':('upperarm_l',np.array([4,0,-37]),dist)}
    board_frames={}
    for owner,(node,offset,kind) in positions.items():
     physical=boards[kind]['physical_with_declared_substitutes_bounds_mm'];center=(np.array(physical[:3])+physical[3:])/2
     M=T[node]@matrix(basis,offset-basis@center);board_frames[owner]=M
     for meta,shape in pcb[kind]:objects.append((owner+'_'+meta['id'],owner,meta['class'],shape,M))
    M=T['chest']@matrix(basis,[-8,0,20]);objects.append(('N2_inherited','N2','physical_unqualified',n2,M))
    # Explicit conservative N2 RF allowance; component-level N2 mating model remains unqualified.
    rf=boxbb([-20,-15,-12,20,15,12]);objects.append(('N2_RF_provisional','N2','functional_keepout_unqualified',rf,T['chest']@matrix(basis,[-8,0,55])))
    bounds=[]
    for name,owner,kind,shape,M in objects:
     points=apply(corners(bb(shape)),M);bounds.append((name,owner,kind,points.min(0),points.max(0)))
    hits=[]
    for x,y in itertools.combinations(bounds,2):
     if x[1]==y[1]:continue # Previously audited same module/board interfaces; not a new self-clearance pass.
     if not ('physical' in x[2] or x[2]=='physical') and not ('physical' in y[2] or y[2]=='physical'):continue
     overlap=np.minimum(x[4],y[4])-np.maximum(x[3],y[3])
     if np.all(overlap>0):hits.append({'a':x[0],'b':y[0],'bbox_overlap_mm3':float(np.prod(overlap)),'kind':'POTENTIAL_NOT_EXACT_SOLID_COLLISION'})
    lines=[]
    for index,aid in enumerate(ids):
     target='N3_prox' if index<5 else 'D3';kind=prox if index<5 else dist;ref='J'+str(11+index)
     connector=next(c for c in boards[kind]['connectors'] if c['ref']==ref);xy=connector['frame_origin_xy_mm'];dest=apply([[xy[0],-xy[1],3]],board_frames[target])[0]
     start=apply([[0,0,30]],mounts[aid][0])[0]
     # Shared control-point routes retain all nine six-conductor sensor connections.
     route=[start,(start+dest)/2+np.array([18,0,0]),dest];length=sum(np.linalg.norm(b-a) for a,b in zip(route,route[1:]))+2*math.pi*12+20
     lines.append({'id':aid,'conductors':6,'draft_points_mm':[x.tolist() for x in route],'length_with_one_R12_loop_and_20mm_allowance_mm':float(length)})
    points=[]
    for target,kind in [('N3_prox',prox),('D3',dist)]:
     c=next(c for c in boards[kind]['connectors'] if c['ref']=='J50');xy=c['frame_origin_xy_mm'];points.append(apply([[xy[0],-xy[1],3]],board_frames[target])[0])
    path=[points[0],T['clavicle_l'][:3,3]+[18,0,0],T['upperarm_l'][:3,3]+[18,0,0],points[1]]
    length=sum(np.linalg.norm(b-a) for a,b in zip(path,path[1:]))+2*math.pi*12+20
    lines.append({'id':'J50','conductors':14 if variant=='A' else 4,'draft_points_mm':[x.tolist() for x in path],'length_with_one_R12_loop_and_20mm_allowance_mm':float(length)})
    harness.extend({'pose':pose_name,**line} for line in lines)
    cases.append({'pose':pose_name,'angles_deg':pose,'potential_external_pairs':len(hits),'pairs':hits,'J50_draft_length_mm':float(length)})
    if pose_name=='neutral':
     # Two reproducible solid counterexamples supplement conservative all-pair AABB screening.
     byname={name:(shape,M,kind) for name,_,kind,shape,M in objects};exact=[]
     for left,right in [('clavicle_l.protract_stator','N2_inherited'),('upperarm_l.flex_stator','N3_prox_antenna_manufacturer_air')]:
      key=(char,left,right)
      if key not in exact_cache:
       ls,lm,lk=byname[left];rs,rm,rk=byname[right]
       exact_cache[key]=located(ls,lm).intersect(located(rs,rm)).Volume()
      exact.append({'a':left,'b':right,'intersection_mm3':exact_cache[key],'scope':'exact imported BRep vs physical part or declared functional keepout; no tolerance expansion'})
     # Imported native solids, not a passing claim from rectangular board proxies.
     physical_shapes=[located(shape,M) for _,_,k,shape,M in objects if 'physical' in k]
     if char=='manny':cq.exporters.export(cq.Compound.makeCompound(physical_shapes),str(a.out/(variant+'_left_arm_native_trial.step')))
     pts=np.vstack([apply(corners(bb(shape)),M) for _,_,k,shape,M in objects if 'physical' in k]);inside=inside_surface(pts,verts,faces)
     neutral={'physical_bound_corners_inside_reference':int(inside.sum()),'sampled_corners':len(inside),'bounds_mm':np.r_[pts.min(0),pts.max(0)].tolist(),'includes_2mm_shell':False,'exact_counterexamples':exact}
   variants.append({'variant':variant,'cases':cases,'harness':harness,'neutral':neutral,'max_J50_draft_length_mm':max(c['J50_draft_length_mm'] for c in cases),'status':'BLOCKED_SHARED_MECHANICS_AND_ROUTE_DETAIL'})
  report['characters'].append({'character':char,'left_measured_axes':ids,'explicit_pivot_offsets_m':offsets,'module_axis_standoff_mm':36,'output_extension_mm':16,'variants':variants})
 report['missing_before_qualification']=['Resolved mounting yokes and fasteners','N2 missing models/mating/service qualification','Real shell thickness/tolerance','Continuous collision and minimum cable curvature','Full required pose paths including back reach','Right arm mechanical offset design and separate mirror validation','Wire restoration force / spring / bonds / output clamp loads']
 report['decision']='Retain A acquisition baseline; C integration decision deferred. This shared failed screen grants no whole-arm fit credit to either route.'
 assert all(sha(ROOT/path)==h for path,h in consumed.items()),'CAD input changed during consumption'
 report['input_sha256']={**consumed,pcpath.relative_to(ROOT).as_posix():sha(pcpath)}
 (a.out/'shared_arm_screen.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print('Shared screen complete',[(c['character'],[(v['variant'],len(v['cases']),v['max_J50_draft_length_mm']) for v in c['variants']]) for c in report['characters']])
if __name__=='__main__':main()
