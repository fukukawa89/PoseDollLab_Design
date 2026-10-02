"""O7 conditional arm loads; raising hand force includes gravity as well as friction."""
from pathlib import Path
import argparse,hashlib,json,sys,math
import numpy as np
R=Path(__file__).resolve().parents[1];H=R/'Hardware/PoseDoll44'
sys.path.insert(0,str(H/'cad'))
from model import fk,rotation
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--large',type=Path,required=True);ap.add_argument('--small',type=Path,required=True);ap.add_argument('--layout',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.layout=a.layout.resolve()
 run=H/'generated/revO6/runs/o6_20260924_r1';paths={'LP6':a.large.resolve(),'M4':a.small.resolve()}
 manifests={k:json.loads(p.read_text()) for k,p in paths.items()};sources=[*paths.values(),a.layout/'layout_search.json',Path(__file__),H/'cad/model.py'];layout=json.loads((a.layout/'layout_search.json').read_text());reports=[]
 for char in layout['characters']:
  ch,side=char['character'],char['side'];path=a.layout/(ch+'_'+side+'_profile.json');sources.append(path);profile=json.loads(path.read_text());nodes={n['id']:n for n in profile['nodes']};axisnodes={n['axis_id']:n for n in profile['nodes'] if 'axis_id' in n}
  def downstream(owner,axis):
   target=axisnodes[axis]['id']
   while owner is not None:
    if owner==target:return True
    owner=nodes[owner]['parent']
   return False
  # Engineering allocations, not CAD parts, not secretly massless missing links.
  allowances=[{'owner':axisnodes[axis]['id'],'mass_g':8.,'local_mm':[0,0,0],'basis':'8 g provisional yoke/attachment allowance per axis, not an actual COM'} for axis in char['axes']]
  allowances.extend([{'owner':'upperarm_'+side,'mass_g':20.,'local_mm':[0,0,-20],'basis':'cover, harness and remote-board allowance'}, {'owner':'forearm_'+side,'mass_g':20.,'local_mm':[0,0,-20],'basis':'cover/harness allowance'}, {'owner':'hand_'+side,'mass_g':40.,'local_mm':[0,0,-20],'basis':'hand cover/end mass allowance'}])
  maxima={axis:{'gravity_Nm':0,'pose':None} for axis in char['axes']};subset=sum(manifests[f]['modeled_mass_g'] for f in char['families']);caseout=[]
  for k,pose in enumerate(char['poses']):
   T,A=fk(profile,pose['angles_deg']);masses=[]
   for i,axis in enumerate(char['axes']):
    node=axisnodes[axis];M=np.array(char['module_frames'][i][k]);C=M.copy();C[:3,:3]=rotation(A[axis]['direction'],pose['angles_deg'].get(axis,0))@M[:3,:3]
    for row in manifests[char['families'][i]]['parts']:
     frame=C if row['owner']=='child' else M;owner=node['id'] if row['owner']=='child' else node['parent'];com=frame[:3,:3]@np.array(row['local_com_mm'])+frame[:3,3]
     masses.append((owner,row['mass_g'],com))
   for q in allowances:masses.append((q['owner'],q['mass_g'],T[q['owner']][:3,:3]@np.array(q['local_mm'])+T[q['owner']][:3,3]))
   torques={}
   for axis in char['axes']:
    vec=sum((np.cross((com-A[axis]['origin'])/1000,[0,0,-g/1000*9.80665]) for owner,g,com in masses if downstream(owner,axis)),start=np.zeros(3));value=abs(float(np.dot(vec,A[axis]['direction'])));torques[axis]=value
    if value>maxima[axis]['gravity_Nm']:maxima[axis]={'gravity_Nm':value,'pose':pose['pose']}
   caseout.append({'pose':pose['pose'],'gravity_Nm':torques})
  rows=[]
  for i,axis in enumerate(char['axes']):
   f=char['families'][i];ro,ri,F=(14,6,354) if f=='LP6' else (7.4,2.6,210);radius=2/3*(ro**3-ri**3)/(ro**2-ri**2)/1000
   need=1.5*maxima[axis]['gravity_Nm']+.02
   # +25/-7.5 % is a catalogue-point sensitivity only, NOT a maximum preload.
   row={'axis':axis,'family':f,**maxima[axis],'required_hold_Nm':need,'margin_factor':1.5,'cable_torque_assumption_Nm':.02,'effective_radius_m':radius,'catalog_point_force_N':F,'preload_required_at_mu_008_N':need/(2*.08*radius),'preload_required_at_mu_022_N':need/(2*.22*radius),'catalog_point_torque_at_mu_008_Nm':2*.08*F*radius,'catalog_point_torque_at_mu_022_Nm':2*.22*F*radius,'friction_only_hand_force_at_30mm_60mm_N':[need/.03,need/.06],'minimum_budget_raising_hand_force_at_30mm_60mm_N':[(need+maxima[axis]['gravity_Nm'])/.03,(need+maxima[axis]['gravity_Nm'])/.06],'raising_force_at_catalog_mu_008_at_30mm_60mm_N':[(2*.08*F*radius+maxima[axis]['gravity_Nm'])/v for v in (.03,.06)],'raising_force_at_catalog_mu_022_at_30mm_60mm_N':[(2*.22*F*radius+maxima[axis]['gravity_Nm'])/v for v in (.03,.06)],'mu_needed_at_catalog_force':need/(2*F*radius),'decision':'CONDITIONAL_NOT_RATING'}
   row['low_mu_catalog_point_meets_budget']=row['catalog_point_torque_at_mu_008_Nm']>=need
   row['high_mu_catalog_point_meets_budget']=row['catalog_point_torque_at_mu_022_Nm']>=need
   row['key_loaded_sliding_parasitic_force_at_required_hold_N']=[mu*need/(.00315 if f=='LP6' else .00205) for mu in (.1,.3)]
   rows.append(row)
  reports.append({'character':ch,'side':side,'modeled_nine_module_mass_g':subset,'explicit_allocations':allowances,'arm_mass_budget_g':subset+sum(q['mass_g'] for q in allowances),'axes':rows,'cases':caseout,'support_case':'Unsupported arm, base held. Does not cover hands supporting body, falls or external props.'})
 out={'schema':'o7-actual-com-gravity-inclusive-hand-force-v1','characters':reports,'input_sha256':{p.relative_to(R).as_posix():sha(p) for p in sources},'physical_tested':False,'complete_body_mass_g':None,'mass_hard_limit_kg':None,'force_curve_maximum_known':False,'mechanical_qualification':False,'open':['Actual yoke CAD/COM replaces allowances','Spring force and friction distributions','Operating force acceptance and reversal stability','Full body contact loads and support reactions','Shaft, bolts, bond, fatigue and tolerance proof']}
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print([(c['character'],c['side'],round(c['arm_mass_budget_g'],1),[(r['axis'],round(r['required_hold_Nm'],3),r['low_mu_catalog_point_meets_budget']) for r in c['axes']]) for c in reports])
if __name__=='__main__':main()

