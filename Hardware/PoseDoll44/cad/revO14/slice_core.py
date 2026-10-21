"""Offline generic FDM diagnostic slicing. Never send this G-code to a printer."""
from pathlib import Path
import sys,json,subprocess,hashlib,re
import numpy as np
from prepare_print_bed import H,R,OUT,B,hull,in_hull
TOOL=R/'.local/tools/prusaslicer-2.9.6/PrusaSlicer-2.9.6/prusa-slicer-console.exe'
D=OUT/'slicing';D.mkdir(exist_ok=True)
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
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
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
 cfg=D/'generic_diagnostic.ini';cfg.write_text(CONFIG,encoding='utf-8');bed=json.loads((OUT/'bed_geometry.json').read_text());rows=[]
 for r in bed['parts']:
  k=r['part'];bbox=r['new']['bounds_mm'];center=[(bbox[i]+bbox[i+3])/2 for i in (0,1)];src=B/'print_beds'/f'{k}_flat_face.stl';dst=D/f'{k}_DIAGNOSTIC_DO_NOT_PRINT.gcode'
  cmd=[str(TOOL),'--load',str(cfg),'--center',','.join(map(str,center)),'--export-gcode','--output',str(dst),str(src)]
  run=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace');(D/f'{k}.log').write_text(run.stdout+'\n'+run.stderr,encoding='utf-8')
  if run.returncode:raise RuntimeError(k+' slicing failed: '+run.stdout+run.stderr)
  data=parse(dst);h=np.array(data['combined_first_layer_hull_mm']);com=np.array(r['new']['solid_COM_mm']);z=[s['a'][2] for s in data['support_segments']]
  row={'part':k,'exit_code':run.returncode,'command':cmd,'stl_sha256':sha(src),'gcode_sha256':sha(dst),'first_layer_z_mm':.2,'support_extrusion_segments':len(z),'support_z_range_mm':[min(z),max(z)] if z else None,'final_model_COM_in_model_plus_support_first_layer_hull':in_hull(com[:2],h),'extrusion_progress_centroids_in_hull':all(in_hull(np.array(a['extrusion_volume_weighted_xy_mm']),h) for a in data['progress_extrusion_centroids']),'extruding_segments_by_type':data['extruding_segments_by_type'],'combined_first_layer_hull_mm':h.tolist(),'model_COM_mm':com.tolist()}
  (D/f'{k}_paths.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8');rows.append(row);print(k,row['support_extrusion_segments'],row['final_model_COM_in_model_plus_support_first_layer_hull'],flush=True)
 report={'slicer':'PrusaSlicer 2.9.6 portable official release','tool_sha256':sha(TOOL),'archive_sha256':sha(TOOL.parent.parent/'PrusaSlicer-2.9.6.zip'),'config_sha256':sha(cfg),'rows':rows,'actual_slicing':True,'actual_printer_profile':False,'physically_printed':False,'scope':'Actual toolpaths with support and brim. Convex-hull checks are geometric diagnostics, not a proof of layer connectivity, bed adhesion, support removability, mechanical strength or A1/P1S compatibility. G-code deliberately has no qualified machine/material configuration and must not be printed.','manufacturing_released':False}
 (D/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
