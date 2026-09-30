"""Recheck nominal worn O6 geometry with bounded O7 detent advancement."""
from pathlib import Path
import argparse,hashlib,itertools,json,sys
import cadquery as cq
R=Path(__file__).resolve().parents[4];H=R/'Hardware/PoseDoll44'
sys.path.insert(0,str(H/'cad/revO3'));from compact_joint import ring
sys.path.insert(0,str(H/'cad/revO6'));from small_joint import spring
from thread_geometry import overlap_volume
from preload_schedule import advance

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--joint',type=Path,required=True);ap.add_argument('--old-check',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.joint=a.joint.resolve();m=json.loads((a.joint/'manifest.json').read_text());g=m['geometry'];s={};paths=[a.joint/'manifest.json',Path(__file__),Path(__file__).with_name('preload_schedule.py'),H/'cad/revO3/compact_joint.py',H/'cad/revO6/small_joint.py',H/'cad/revO6/thread_geometry.py',a.old_check]
 for row in m['parts']:
  p=a.joint/row['step_file'];assert sha(p)==row['step_sha256'];paths.append(p);s[row['part_id']]=cq.importers.importStep(str(p)).val()
 inputs={p.resolve().relative_to(R).as_posix():sha(p) for p in paths};hw=g['spring_hwork_mm'];top=g['spring_stack_top_z_mm'];names=['disc_spring_'+str(i+1) for i in range(4)];states=[];cache={}
 assert not m['nominal_intersections']
 for wf,wr in g['wear_pairs_mm']:
  for cf,cr in g['compression_pairs_mm']:
   plan=advance([wf,wr],[cf,cr],g['thread_pitch_mm'],hw,g['spring_hfree_mm']);df=wf+cf;dr=plan['total_wear_compression_mm'];dz=plan['cap_advance_mm'];height=plan['spring_height_mm'];cur=dict(s)
   cur['front_friction_lining']=ring(g['lining_ro_mm'],g['lining_ri_mm'],g['front_lining_z_mm'][0]+df,g['front_lining_z_mm'][1]);cur['rear_friction_lining']=ring(g['lining_ro_mm'],g['lining_ri_mm'],g['rear_lining_z_mm'][0]+dr,g['rear_lining_z_mm'][1]+df);cur['floating_brake_disc']=s['floating_brake_disc'].translate((0,0,df))
   for n in ('integral_rear_sliding_carrier','spring_front_washer'):cur[n]=s[n].translate((0,0,dr))
   for n in ('threaded_adjuster_cap','spring_rear_washer'):cur[n]=s[n].translate((0,0,dz))
   cur['threaded_adjuster_cap']=cur['threaded_adjuster_cap'].rotate((0,0,0),(0,0,1),plan['cap_rotation_deg'])
   for i,n in enumerate(names):cur[n]=spring(g['spring_ro_mm'],g['spring_ri_mm'],g['spring_t_mm'],top-4*hw+dz+i*height,height,i%2==1)
   sig={n:() for n in cur}
   for n in ('front_friction_lining','floating_brake_disc'):sig[n]=(round(df,6),)
   sig['rear_friction_lining']=(round(df,6),round(dr,6))
   for n in ('integral_rear_sliding_carrier','spring_front_washer'):sig[n]=(round(dr,6),)
   for n in ('threaded_adjuster_cap','spring_rear_washer'):sig[n]=(round(dz,6),)
   for n in names:sig[n]=(round(dz,6),round(height,6))
   changed={n for n in cur if cur[n] is not s[n]};hits=[]
   for n,j in itertools.combinations(cur,2):
    if n not in changed and j not in changed:continue
    key=(n,sig[n],j,sig[j])
    if key not in cache:cache[key]=overlap_volume(cur[n],cur[j])
    if cache[key]>1e-4:hits.append({'a':n,'b':j,'volume_mm3':cache[key]})
   states.append({'wear_mm':[wf,wr],'compression_mm':[cf,cr],**plan,'intersections':hits});print('life',wf,wr,cf,cr,'h',height,'hits',len(hits),flush=True)
   save(a.out/'progress.json',{'status':'RUNNING_INCOMPLETE','states':states})
 old=json.loads(a.old_check.read_text());oldover=[x for x in old['states'] if x['spring_height_mm']<hw-1e-9]
 assert all(sha(R/k)==v for k,v in inputs.items())
 save(a.out/'lifecycle.json',{'schema':'o7-bounded-nominal-preload-v1','status':'FAIL' if any(x['intersections'] for x in states) else 'PASS_SCOPED_GEOMETRY_AND_NOMINAL_SCHEDULE','states':states,'old_states_past_catalog_nominal_deflection':len(oldover),'old_max_nominal_overtravel_per_disc_mm':max([hw-x['spring_height_mm'] for x in oldover] or [0]),'new_overtravel_states':sum(not x['nominal_catalog_deflection_not_exceeded'] for x in states),'unique_pair_evaluations':len(cache),'force_rating_known':False,'mechanical_overtravel_stop_exists':False,'scope':'Nominal detent schedule only. Actual free heights, thicknesses, tolerances and stack force curve must be measured; no lifetime/strength or automatic preload assurance. Lower compression may lower holding torque.','input_sha256':inputs,'physical_tested':False,'manufacturing_released':False})
 (a.out/'progress.json').unlink()
if __name__=='__main__':main()
