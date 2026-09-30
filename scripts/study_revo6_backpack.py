"""Back-mounted reuse study. Boxes are occupied-envelope reservations, NOT complete PCBA."""
from pathlib import Path
import argparse,hashlib,itertools,json,math,sys
import numpy as np
R=Path(__file__).resolve().parents[1];H=R/'Hardware/PoseDoll44'
sys.path.insert(0,str(R/'scripts'))
from study_revo import anatomy
from model import fk,keyposes
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pack(rects,W,H,nlayers):
 # Exact for a declared bottom-left corner placement grammar, not globally optimal nesting.
 order=sorted(rects,key=lambda r:r[1]*r[2],reverse=True);placed=[]
 def go(k):
  if k==len(order):return list(placed)
  name,w,h=order[k]
  for layer in range(nlayers):
   same=[r for r in placed if r['layer']==layer]
   if layer and not same and not any(r['layer']==layer-1 for r in placed):continue
   xs=sorted(set([0]+[r['x']+r['w']+2 for r in same]));ys=sorted(set([0]+[r['y']+r['h']+2 for r in same]))
   for rw,rh,rot in ((w,h,0),(h,w,90)):
    for x,y in itertools.product(xs,ys):
     if x+rw>W or y+rh>H:continue
     if any(x<r['x']+r['w']+2-1e-7 and x+rw+2>r['x']+1e-7 and y<r['y']+r['h']+2-1e-7 and y+rh+2>r['y']+1e-7 for r in same):continue
     placed.append(dict(id=name,layer=layer,x=x,y=y,w=rw,h=rh,rotation_deg=rot))
     result=go(k+1)
     if result is not None:return result
     placed.pop()
  return None
 return go(0)
def segbox_distance(a,b,lo,hi):
 def f(t):
  p=a+t*(b-a);return float(np.linalg.norm(np.maximum(np.maximum(lo-p,p-hi),0)))
 l,r=0.,1.
 for _ in range(60):
  x=l+(r-l)/3;y=r-(r-l)/3
  if f(x)<f(y):r=y
  else:l=x
 t=(l+r)/2;return min((f(0),0),(f(1),1),(f(t),t))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 paths=[Path(__file__),H/'docs/CHEST_AND_EXTERNAL_REVN.zh-CN.md',R/'scripts/study_revo.py',H/'cad/model.py'];boards={}
 for name,ports in [('N1',3),('N2',6),('N3',9),('N4',9),('N5',7),('N6',7)]:
  p=H/f'electronics/revO/node_{ports}port/layout.json';paths.append(p);j=json.loads(p.read_text());w,h,t=j['board_mm'];front=max(c['height_max_assumed_mm'] for c in j['components'] if not c['back']);back=max(c['height_max_assumed_mm'] for c in j['components'] if c['back'])
  xs=[0,w];ys=[0,h]
  for c in j['components']:x0,y0,x1,y1=c['courtyard_xy_mm'];xs +=[x0,x1];ys +=[y0,y1]
  for c in j['connectors']:
   x,y=c['position_xy_mm'];pw,ph,_=c['plug_envelope_mm'];xs +=[x-pw/2,x+pw/2];ys +=[y-ph/2,y+ph/2]
  boards[name]={'ports':ports,'bare_board_mm':[w,h,t],'occupied_planar_envelope_mm':[max(xs)-min(xs),max(ys)-min(ys)],'front_assumed_mm':front,'back_assumed_mm':back,'input':p.relative_to(R).as_posix(),'native_status':j['status']}
 rects=[(n,*b['occupied_planar_envelope_mm']) for n,b in boards.items()]
 trials=[]
 for w,h,layers,radius in itertools.product((68,80,96,112),(80,100,120,140),(1,2,3),(4,12)):
  fit=pack(rects,w,h,layers)
  if fit is None:continue
  # Existing top entry plugs on back: 6 mm housing + 3 mm straight neck + R.
  layer_depth=max(b['front_assumed_mm']+b['bare_board_mm'][2]+max(b['back_assumed_mm'],6+3+radius) for b in boards.values())
  depth=layers*layer_depth+(layers-1)*2+3
  trials.append({'inside_width_mm':w,'inside_height_mm':h,'layers':layers,'bend_radius_mm':radius,'outer_mm':[w+3,h+3,depth],'box_volume_cm3':(w+3)*(h+3)*depth/1000,'placements':fit,'status':'RESERVATION_PACKED_NOT_PCBA_QUALIFIED'})
 old=6*36*44*100/1000
 pareto=[x for x in trials if not any(all(b<=c for b,c in zip(y['outer_mm'],x['outer_mm'])) and any(b<c for b,c in zip(y['outer_mm'],x['outer_mm'])) and y['bend_radius_mm']==x['bend_radius_mm'] for y in trials)]
 # Policy trial: thin central thoracic pod; six boards MUST really fit it before adoption.
 compact=[q for q in trials if q['inside_width_mm']<=80 and q['inside_height_mm']<=100 and q['bend_radius_mm']==12]
 selected=min(compact,key=lambda q:q['box_volume_cm3']) if compact else min((q for q in trials if q['bend_radius_mm']==12),key=lambda q:q['box_volume_cm3'])
 poses=keyposes()
 for d in (15,30,45,60):poses['back_reach_'+str(d)]={**{f'upperarm_{s}.flex':-d for s in ('l','r')},**{f'elbow_{s}.flex':90 for s in ('l','r')},**{f'upperarm_{s}.twist':-45 for s in ('l','r')}}
 for d in (-30,30):poses['waist_pitch_'+str(d)]={'waist.pitch':d};poses['waist_twist_'+str(d)]={'waist.yaw':d}
 cases=[];back_variants=[('reused_boards',selected['outer_mm']),('central_relayout_target_only',[66,76,22])]
 # Both use torso-side clearance x=-28, top at chest+58. These are design positions, not skin fit.
 for ch in ('manny','quinn'):
  p=anatomy(ch,480);paths.append(H/f'mechanical_manifest/physical_{ch}_44_revG_humanform_trial.json')
  for variant,(width,height,depth) in back_variants:
   lo=np.array([-28-depth,-width/2,58-height]);hi=np.array([-28,width/2,58])
   for pname,pose in poses.items():
    T,_=fk(p,pose);inv=np.linalg.inv(T['chest']);contacts=[];samples=[]
    for side in ('l','r'):
     for n1,n2,radius in [('upperarm_'+side,'elbow_'+side,10),('elbow_'+side,'hand_'+side,9),('hand_'+side,'hand_tip_'+side,12)]:
      aa=inv[:3,:3]@T[n1][:3,3]+inv[:3,3];bb=inv[:3,:3]@T[n2][:3,3]+inv[:3,3];dist,t=segbox_distance(aa,bb,lo,hi);rec={'segment':[n1,n2],'capsule_radius_assumption_mm':radius,'clearance_mm':dist-radius,'closest_t':t};samples.append(rec)
      if dist<radius:contacts.append(rec)
    cases.append({'character':ch,'variant':variant,'pose':pname,'back_box_local_mm':list(lo)+list(hi),'contacts':contacts,'minimum_capsule_clearance_mm':min(x['clearance_mm'] for x in samples),'status':'FAIL_RESERVATION_CONTACT' if contacts else 'CLEAR_CAPSULE_SCREEN_ONLY'})
 wires=[{'case':name,'conductors':n,'bundle_equivalent_diameter_mm':od*math.sqrt(n/.6),'wire_OD_assumption_mm':od,'fill_fraction_assumption':.6} for name,n in [('nine regional six-wire ports TOTAL; not all cross one shoulder joint',54),('five proximal plus four distal split sensors, local',24),('four-wire remote bus',4),('41 individual sensors at central-board ingress',246)] for od in (.61,.8)]
 p=anatomy('manny',480);nodes={n['id']:n for n in p['nodes']}
 axisnodes=[n for n in p['nodes'] if n.get('axis_id','').startswith(tuple(x+'_l.' for x in ('clavicle','upperarm','elbow','forearm','hand')))]
 def under(owner,root):
  while owner is not None:
   if owner==root:return True
   owner=nodes[owner]['parent']
  return False
 cuts=[]
 for joint in axisnodes:
  root=joint['id'];counts={}
  for scheme in ('all_raw_to_back_chest','A_proximal5_distal4_J50_14','C_proximal5_remote4_J50_4'):
   count=0
   for i,sensor in enumerate(axisnodes):
    dest='chest' if scheme=='all_raw_to_back_chest' or i<5 else 'upperarm_l'
    count+=6*(under(sensor['parent'],root)!=under(dest,root))
   if scheme!='all_raw_to_back_chest':count+=(14 if scheme.startswith('A_') else 4)*(under('chest',root)!=under('upperarm_l',root))
   counts[scheme]=int(count)
  cuts.append({'axis':joint['axis_id'],'conductors_crossing_kinematic_cut':counts,'scope':'Raw sensor wires plus J50 only; no unrelated supply/CAN added. Six raw wires per sensor. No conductor-sharing redesign assumed.'})
 result={'schema':'o6-backpack-alternative-v1','user_override':'Back-mounted concentration explicitly permitted as fallback. Earlier no-backpack requirement no longer absolute. All sensor heads remain at joints.','boards':boards,'candidate_count':len(trials),'pareto_packing':pareto,'selected_reuse_trial':selected,'old_six_box_total_cm3_excludes_power_and_support':old,'selected_nominal_box_reduction_fraction':1-selected['box_volume_cm3']/old,'movement_capsule_screen':cases,'wire_bundles':wires,'actual_arm_kinematic_wire_cutsets':cuts,'central_relayout_target':{'outer_mm':[66,76,22],'status':'SPACE_TARGET_ONLY_NO_LAYOUT_NO_ROUTED_PCB_NO_PASS','requires':'New shared-board placement/routing, matching 41 channels and six logical records, protection, RF keepout, real plugs and cable routing'},'authority':'Comparative digital study. Retain G0 external and radio requirement; no electronics functionality deleted.','scope_limits':['Reused O1 boards are unrouted and their plug/component heights are unqualified','Six independent RF keepouts not packed; placement can require larger envelope','No supports/thermal/voltage or long SPI waveform acceptance','Capsules use anatomy centerlines and stated radii, not full moving skins or revised yokes','One rigid thoracic mounting cannot be assumed to clear lumbar bending or lying poses','Long individual sensor wires need signal-integrity and bending verification even at static rates'],'input_sha256':{p.relative_to(R).as_posix():sha(p) for p in set(paths)},'physical_tested':False,'manufacturing_released':False}
 (a.out/'backpack_study.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');print('selected',selected['outer_mm'],'volume',selected['box_volume_cm3'],'old six boxes',old);print('capsule contacts',[(v,sum(bool(q['contacts']) for q in cases if q['variant']==v)) for v,_ in back_variants]);print('packing candidates',len(trials))
if __name__=='__main__':main()

