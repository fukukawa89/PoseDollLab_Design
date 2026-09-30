"""Actual generic diagnostic slicing of every unique O15 print.
The supplier re-slices using the real A1/P1S and material profile. Diagnostic
G-code is kept out of the print/purchase package and must never run on a printer.
Parser/config are derived from the earlier O14 diagnostic with explicit scope.
"""
from common import *
from export_print_batch import hull,in_hull
import subprocess,re
TOOL=R/'.local/tools/prusaslicer-2.9.6/PrusaSlicer-2.9.6/prusa-slicer-console.exe'
CONFIG="""# Generic diagnostic only; NOT a Bambu A1/P1S machine profile.
layer_height = 0.2
first_layer_height = 0.2
nozzle_diameter = 0.4
filament_diameter = 1.75
bed_shape = 0x0,256x0,256x256,0x256
max_print_height = 256
perimeters = 6
top_solid_layers = 5
bottom_solid_layers = 5
fill_density = 100%
fill_pattern = rectilinear
support_material = 1
support_material_auto = 1
support_material_buildplate_only = 0
support_material_style = grid
support_material_threshold = 45
support_material_contact_distance = 0.2
support_material_interface_layers = 3
support_material_interface_spacing = 0
support_material_spacing = 2
support_material_with_sheath = 1
support_material_xy_spacing = 0.25
brim_width = 5
brim_separation = 0
skirts = 0
use_relative_e_distances = 1
binary_gcode = 0
gcode_comments = 0
elefant_foot_compensation = 0
first_layer_speed = 20
perimeter_speed = 40
external_perimeter_speed = 25
support_material_speed = 30
temperature = 0
first_layer_temperature = 0
bed_temperature = 0
first_layer_bed_temperature = 0
start_gcode = ; DIAGNOSTIC ONLY - DO NOT PRINT
end_gcode = ; END DIAGNOSTIC - NO MACHINE VALIDATION
"""

def parse(p):
 xyz=np.zeros(3);role='unknown';layer_z=None;segments=[];supports=[];first=[];stats={};last_e=0.;relative=True;mass=0.;moment=np.zeros(2);progress=[]
 for line in p.read_text().splitlines():
  if line.startswith(';TYPE:'):role=line[6:]
  if line.startswith(';Z:'):
   if mass:progress.append({'z_mm':layer_z,'extrusion_volume_weighted_xy_mm':(moment/mass).tolist()})
   layer_z=float(line[3:])
  if line.startswith('M82'):relative=False
  if line.startswith('M83'):relative=True
  if line.startswith('G92 E'):last_e=float(line.split('E')[1].split()[0])
  if not re.match(r'^G[01] ',line):continue
  d={a:float(v) for a,v in re.findall(r'([XYZE])(-?[0-9.]+)',line.split(';')[0])}
  nxt=xyz.copy()
  for i,a in enumerate('XYZ'):
   if a in d:nxt[i]=d[a]
  e=d.get('E',0 if relative else last_e);extrusion=e if relative else e-last_e
  if 'E' in d:last_e=e
  if extrusion>1e-7 and np.linalg.norm(nxt[:2]-xyz[:2])>1e-6:
   stats[role]=stats.get(role,0)+1
   record={'a':xyz.tolist(),'b':nxt.tolist(),'type':role,'layer_z':layer_z}
   if layer_z is not None and abs(layer_z-.2)<1e-5:
    first.append(record)
   if 'Support' in role:supports.append(record)
   mass+=extrusion;moment+=extrusion*(xyz[:2]+nxt[:2])/2
  xyz=nxt
 if mass:progress.append({'z_mm':layer_z,'extrusion_volume_weighted_xy_mm':(moment/mass).tolist()})
 pts=[v[:2] for s in first if 'Skirt' not in s['type'] and 'Brim' not in s['type'] for v in (s['a'],s['b'])]
 h=hull(pts);return {'extruding_segments_by_type':stats,'first_layer_segments':first,'support_segments':supports,'combined_first_layer_hull_mm':h.tolist(),'progress_extrusion_centroids':progress}

def main():
 manifest=read(OUT/'print_batch_manifest.json');folder=OUT/'print_slicing';folder.mkdir(exist_ok=True);cfg=folder/'generic_diagnostic.ini';cfg.write_text(CONFIG,encoding='utf8');rows=[];prior=read(folder/'report.json') if (folder/'report.json').exists() else {};old={r['id']:r for r in prior.get('rows',[])}
 for row in manifest['rows']:
  pid=row['id'];src=H/row['stl'];dst=folder/(pid+'_DIAGNOSTIC_DO_NOT_PRINT.gcode');bed=row['bed'];bounds=bed['bounds_mm'];center=[(bounds[i]+bounds[i+3])/2 for i in (0,1)];cmd=[str(TOOL),'--load',str(cfg),'--center',','.join(map(str,center)),'--export-gcode','--output',str(dst),str(src)]
  previous=old.get(pid)
  if previous and previous.get('exit_code')==0 and previous.get('stl_sha256')==sha(src) and dst.exists() and previous.get('gcode_sha256')==sha(dst) and prior.get('slicer_sha256')==sha(TOOL) and prior.get('config_sha256')==sha(cfg):
   rows.append({**previous,'reused_exact_same_stl_config_slicer_gcode':True});print('SLICE REUSE',pid,flush=True);continue
  run=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',errors='replace');(folder/(pid+'.log')).write_text(run.stdout+'\n'+run.stderr,encoding='utf8')
  result={'id':pid,'exit_code':run.returncode,'command':cmd,'stl_sha256':sha(src),'physically_printed':False}
  if run.returncode==0:
   d=parse(dst);h=np.array(d['combined_first_layer_hull_mm']);com=np.array(bed['COM_mm']);z=[a['a'][2] for a in d['support_segments']]
   result.update({'gcode_sha256':sha(dst),'support_segment_count':len(z),'support_z_range_mm':[min(z),max(z)] if z else None,'model_COM_in_first_layer_support_hull':in_hull(com[:2],h),'all_progress_centroids_in_hull':all(in_hull(np.array(v['extrusion_volume_weighted_xy_mm']),h) for v in d['progress_extrusion_centroids']),'extrusion_segments_by_type':d['extruding_segments_by_type'],'combined_first_layer_hull_mm':h.tolist()})
   d.pop('support_segments');(folder/(pid+'_footprint.json')).write_text(json.dumps(d,separators=(',',':')),encoding='utf8')
  rows.append(result);print('SLICE',pid,result['exit_code'],result.get('model_COM_in_first_layer_support_hull'),result.get('all_progress_centroids_in_hull'),flush=True);save('print_slicing/report.json',{'status':'RUNNING','rows':rows})
 failures=[r['id'] for r in rows if r['exit_code'] or not r.get('model_COM_in_first_layer_support_hull') or not r.get('all_progress_centroids_in_hull')]
 save('print_slicing/report.json',{'status':'GEOMETRIC_DIAGNOSTIC_PASS' if not failures else 'PRINT_ORIENTATION_NEEDS_REPAIR','failures':failures,'rows':rows,'slicer_sha256':sha(TOOL),'config_sha256':sha(cfg),'manifest_sha256':sha(OUT/'print_batch_manifest.json'),'scope':'Actual generic toolpaths and support footprints. No proof of bed adhesion, local layer connectivity, support removal or loaded layer strength. No qualified A1/P1S machine profile.','actual_slicing':True,'actual_printer_profile':False,'no_manufacturing_qualification':True})
if __name__=='__main__':main()
