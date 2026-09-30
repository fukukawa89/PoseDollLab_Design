"""Independent conservative CAD screen for the Chinese supplier trial.
This checks real inherited STEP solids against proposed component envelopes.
It does not certify unmodelled terminals, solder joints, plug engagement or loads.
"""
from pathlib import Path
import cadquery as cq
import json,hashlib,itertools
R=Path(__file__).resolve().parents[4];HW=R/'Hardware/PoseDoll44'
OUT=HW/'generated/revO5CN/runs/cn_20260924_r1';OUT.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def box(x,y,z,c):return cq.Workplane('XY').box(x,y,z).translate(c).val()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 base=HW/'generated/revO3/runs/o3_20260924_r3/joint';manifest=base/'manifest.json';m=read(manifest)
 inputs=[Path(__file__),manifest,HW/'cad/revO3/compact_joint.py',HW/'mechanical_manifest/requirements_revO5CN.json',HW/'electronics/sensor_revO5CN/result.json']
 pcb=read(HW/'electronics/sensor_revO5CN/result.json')
 assert pcb['board_mm']==[12,10,1]
 origins=pcb['component_origins']
 assert origins['U1']==[100,100] and origins['J1']==[100,100]
 def xy(ref):return origins[ref][0]-100,100-origins[ref][1]
 old={};metadata={}
 for p in m['parts']:
  f=base/p['step_file'];assert sha(f)==p['step_sha256'];inputs.append(f);old[p['part_id']]=cq.importers.importStep(str(f)).val();metadata[p['part_id']]=p
 before={str(p.relative_to(R)):sha(p) for p in inputs}
 # Actual O3 solid board is 0.910 mm although its KiCad nominal is 1 mm.
 oldpcb=metadata['sensor_pcba_6']['bounds_mm'];support_z=oldpcb[2];old_top=oldpcb[5]
 proposed_thickness=1.0;top=support_z+proposed_thickness;clamp_shift=top-old_top
 outline=[(-5,-5),(5,-5),(6,-4),(6,4),(5,5),(-5,5),(-6,4),(-6,-4)]
 board=cq.Workplane('XY',origin=(0,0,support_z)).polyline(outline).close().extrude(proposed_thickness).val()
 # Maximum package/body envelopes from drawings; include terminals within this
 # envelope only where supplier dimensions support it. Copper/solder not resolved.
 proposed={'PCB_CN1_1mm':board,'MT6701QT_max_body':box(3.1,3.1,.8,(0,0,support_z-.4)),
 'CJT_header_max_body':box(7.25,5.15,3.2,(0,0,top+1.6)),
 'C1_body':box(1.6,.8,.8,(*xy('C1'),support_z-.4)),
 'C2_body':box(2,1.25,1.25,(*xy('C2'),support_z-.625)),
 'R1_body':box(1.6,.8,.45,(*xy('R1'),support_z-.225)),
 'R2_body':box(1.6,.8,.45,(*xy('R2'),support_z-.225))}
 obstacles={k:s for k,s in old.items() if not k.startswith('sensor_pcba_')}
 unadjusted=[]
 for k,s in obstacles.items():
  vol=s.intersect(board).Volume()
  if vol>1e-6:unadjusted.append({'a':'PCB_CN1_1mm','b':k,'intersection_mm3':vol})
 for name in list(obstacles):
  if name.startswith(('pcb_edge_clamp_','pcb_clamp_screw_')):obstacles[name]=obstacles[name].translate((0,0,clamp_shift))
 clashes=[]
 for name,s in proposed.items():
  assert s.isValid() and len(s.Solids())==1
  for other,t in obstacles.items():
   vol=s.intersect(t).Volume()
   if vol>1e-6:clashes.append({'a':name,'b':other,'intersection_mm3':vol})
 for (name,s),(other,t) in itertools.combinations(proposed.items(),2):
  vol=s.intersect(t).Volume()
  if vol>1e-6:clashes.append({'a':name,'b':other,'intersection_mm3':vol})
 # Catalog substitute is deliberately checked before anyone changes its BOM name.
 springs=[]
 guide_name='keyed_pressure_plate'
 for i in range(4):
  z=-8.95+i*.59;h=.59;t=.5;cone=h-t
  profile=[(3.1,z+cone),(6.25,z),(6.25,z+t),(3.1,z+h)]
  if i%2:profile=[(x,2*z+h-y) for x,y in profile]
  s=cq.Workplane('XZ').polyline(profile).close().revolve(360,(0,0),(0,1)).val()
  springs.append({'part':'Raleigh_B12_5_'+str(i+1),'guide_intersection_mm3':s.intersect(old[guide_name]).Volume()})
 a=cq.Assembly(name='O5CN_sensor_installation_envelope_trial')
 for name,s in obstacles.items():a.add(s,name=name,color=cq.Color(.60,.66,.70))
 for name,s in proposed.items():a.add(s,name=name,color=cq.Color(.1,.5,.35) if name.startswith('PCB') else cq.Color(.23,.25,.28))
 a.save(str(OUT/'sensor_installation_trial.step'))
 for name,s in proposed.items():cq.exporters.export(s,str(OUT/(name+'.step')))
 bb=cq.Compound.makeCompound(list(proposed.values())+list(obstacles.values())).BoundingBox()
 report={'schema':'cn1-cad-screen-v1','input_sha256':before,'PCB_support_z_mm':support_z,'old_exported_board_thickness_mm':old_top-support_z,'new_board_thickness_mm':proposed_thickness,'PCB_top_mm':top,'clamp_and_screw_raise_mm':clamp_shift,'unadjusted_clamp_intersections':unadjusted,'adjusted_component_envelope_intersections':clashes,'status':'PASS_NOMINAL_COMPONENT_ENVELOPES_ONLY' if not clashes else 'FAIL','magnet_to_package_face_gap_mm':support_z-.8-metadata['diametric_magnet']['bounds_mm'][5],'old_module_dimensions_mm':m['dimensions_mm'],'new_envelope_dimensions_mm':[bb.xlen,bb.ylen,bb.zlen],'spring_direct_swap':{'guide':guide_name,'nominal_guide_ID_mm':12.16,'candidate_OD_mm':12.5,'diametral_interference_mm':12.5-12.16,'cases':springs,'status':'REJECT' if any(x['guide_intersection_mm3']>1e-6 for x in springs) else 'INCOMPLETE'},'physical_tested':False,'manufacturing_released':False,'limitations':['Package/connector conservative body envelopes, not qualified full PCBA STEP','CJT mating plug engagement, wire bend/service path not qualified','MT6701 magnetic gap to package face is geometric, not accuracy or magnetic-field validation','Nominal 0.09 mm clamp/screw lift corrects board-thickness mismatch; stack tolerance and thread engagement not yet qualified','No shared shoulder/RF collision is closed by this local study','Spring comparison uses catalog-height 0.59 mm, not a measured force curve']}
 for name,h in before.items():assert sha(R/name)==h,name
 save(OUT/'cad_screen.json',report);print(json.dumps({k:report[k] for k in ('status','clamp_and_screw_raise_mm','adjusted_component_envelope_intersections','spring_direct_swap')},indent=2))
if __name__=='__main__':main()
