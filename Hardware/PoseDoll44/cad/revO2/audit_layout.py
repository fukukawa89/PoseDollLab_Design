"""Audit actual legacy part COM and export new PCBA geometry with separately labelled mating studies."""
from compact_joint import *
import importlib.util,os

def main():
 verify,out=run_paths();families={}
 spec=importlib.util.spec_from_file_location('o1_mass_reference',ROOT/'cad/revO/compact_joint.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
 for family in ('S4','M6'):
  rows=old.module(family);parts=[]
  if isinstance(rows,tuple):rows=rows[0]
  for q in rows:
   if q['role']!='solid':continue
   s=q['shape'];mat=q['material'];density=old.DENSITY[mat];unc=.1
   if q['name'].startswith('sensor_pcba_existing_'):
    i=int(q['name'].rsplit('_',1)[1]);mat=['ceramic','ceramic','ceramic','ceramic','package','connector','FR4'][i];density=DENSITY[mat];unc=.25
   if q['name']=='integral_rotor_shaft_and_magnet_seat':mat='al7075';density=DENSITY[mat]
   owner='child' if q['name'] in ('integral_rotor_shaft_and_magnet_seat','diametric_6x2p5_magnet','removable_magnet_keeper') else 'parent'
   c=s.Center();parts.append({'part_id':q['name'],'material':mat,'mass_g':s.Volume()*density,'local_com_mm':[c.x,c.y,c.z],'owner':owner,'uncertainty_fraction':unc,'mass_source':'Recomputed O1 BRep volume and COM, distinct sensor material classes; physical PCBA weight unavailable','retained_design_status':'O1 NONASSEMBLABLE; mass reference only'})
  families[family]=parts
 save(verify/'legacy_mass_reference.json',families)
 boardreports=[]
 for kind in ('proximal5','distal4','distal4_narrow'):
  folder=out/'electronics'/kind;layout=read(folder/'layout.json');model=folder/('PoseDoll_RevO2_'+kind+'.step')
  real=cq.importers.importStep(str(model)).val();bb=bounds(real)
  assembly=cq.Assembly(name=kind+'_MATING_STUDY_NOT_QUALIFIED');assembly.add(real,name='KiCad_export_available_models',color=cq.Color('#277b73'))
  # KiCad export has X right, Y negative downward, PCB top Z=0.
  plugs=[];tails=[]
  for c in layout['components']:
   if not c['ref'].startswith('J') or c['ref']=='JP1':continue
   if c['ref']=='J50':n=14;w=15;h=2.8;depth=5.0;vertical=True
   elif c['ref'] in ('J1','J2','J3'):continue # Exact larger branch plugs still missing: never claim complete PCBA envelope.
   else:n=6;w=7;h=2.8;depth=5.0;vertical=True
   # Drawing-derived housing, open mating recess, contact cavities, latch ridge, individual wire tails.
   shell=box(w,depth,h,(0,0,h/2)).cut(box(w-1.0,depth-1.0,h,(0,0,-.6)))
   for i in range(n):shell=shell.cut(cyl(.23,-.05,h+.05).translate((i-(n-1)/2,0,0)))
   shell=shell.fuse(box(w-1,.5,.3,(0,depth/2-.25,h+.15)))
   if vertical:
    shell=shell.translate((0,0,2.9));wire=[cyl(.4,5.7,12.7).translate((i-(n-1)/2,0,0)) for i in range(n)]
   else:
    shell=shell.rotate((0,0,0),(1,0,0),90).translate((0,4.8,1.8));wire=[cq.Solid.makeCylinder(.4,8,cq.Vector(i-(n-1)/2,4.8,1.8),cq.Vector(0,1,0)) for i in range(n)]
   transform=lambda s:s.rotate((0,0,0),(0,0,1),c['rotation_deg']).translate((c['center_xy_mm'][0],-c['center_xy_mm'][1],0))
   shell=transform(shell);plugs.append({'ref':c['ref'],'bounds_mm':bounds(shell),'shape_source':'JST drawing dimensional construction; recess/latch simplified, mating offset unqualified','part':'SHR-'+str(n).zfill(2)+'V-S','wire_count':n,'wire_OD_mm':.8,'unplug_distance_mm':12})
   assembly.add(shell,name=c['ref']+'_mating_housing_study',color=cq.Color('#e4dcc2'))
   for i,wshape in enumerate(wire):
    ws=transform(wshape);tails.append(bounds(ws));assembly.add(ws,name=c['ref']+'_wire_'+str(i+1),color=cq.Color('#bd9554'))
  assembly.save(str(folder/(kind+'_with_mating_study.step')))
  missing=[]
  log=(folder/'step_export.log').read_text(errors='replace')
  for line in log.splitlines():
   if 'Could not add 3D model for' in line:missing.append(line.split(' for ')[-1].rstrip('.'))
  boardreports.append({'kind':kind,'actual_export_bounds_mm':bb,'actual_export_solids':len(real.Solids()),'missing_component_models':missing,'mating_studies':plugs,'wire_tail_bounds_mm':tails,'mating_and_bend_fit_status':'BLOCKED_EXACT_MATING_DATUM_AND_BRANCH_PLUGS_MISSING','complete_pcba_status':'BLOCKED_MISSING_COMPONENT_MODELS' if missing else 'MODELS_PRESENT_NOT_MATED','mechanical_qualification':False})
 save(verify/'pcba_geometry.json',{'boards':boardreports,'status':'PARTIAL_GEOMETRY_NOT_V2_PASS','mass_note':'Do not apply one density to the mixed-material KiCad assembly','physical_tested':False})
if __name__=='__main__':main()