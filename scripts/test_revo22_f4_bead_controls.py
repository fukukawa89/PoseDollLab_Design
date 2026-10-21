from pathlib import Path
import numpy as np,json,zipfile,sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import box,vf,union
import verify_revo22_f4_full_bead as bead
import o22_recover_native_flag_paths as recover
from verify_revo22_f4_local_extrusion import check as screen
O=R/'.local/o22-bead-controls';bead.O=O;recover.O=O
results=[]
def case(name,prev,curr,body,expectcritical,expectisland):
 folder=O/'candidates'/name/'test'
 for s in ['projects','parts','verification']:(folder/s).mkdir(parents=True,exist_ok=True)
 v,f=vf(body);np.savez_compressed(folder/'parts'/f'{name}.npz',v=v,f=f,fin_v=np.empty((0,3)),fin_f=np.empty((0,3),int),teeth_v=np.empty((0,3)),teeth_f=np.empty((0,3),int))
 (folder/'verification/plate_manifest.json').write_text(json.dumps({'items':[{'rotation_matrix':np.eye(3).tolist(),'translation_mm':[0,0,0]}]}))
 lines=['G90','M83']
 for z,segments in [(.2,prev),(.4,curr)]:
  lines+=['; CHANGE_LAYER',f'; Z_HEIGHT: {z}','; LAYER_HEIGHT: 0.2','; FEATURE: Outer wall','; LINE_WIDTH: 0.4',f'G0 Z{z}']
  for x0,y0,x1,y1 in segments:lines += [f'G0 X{x0} Y{y0}',f'G1 X{x1} Y{y1} E1']
 path=folder/'projects/control.3mf'
 with zipfile.ZipFile(path,'w') as zz:zz.writestr('Metadata/plate_1.gcode','\n'.join(lines))
 screen(path,folder/'verification/local_extrusion.json');d=bead.check(name,'test');critical=d['critical_external_count'];islands=d['external_island_count'];assert (critical>0)==expectcritical,(name,critical);assert (islands>0)==expectisland,(name,islands);results.append({'case':name,'critical_external_count':critical,'external_island_count':islands,'passed':True})
full=box([9,9,0],[21,21,.4]);thin=box([9,9,.3],[21,21,.4])
case('aligned',[(10,10,20,10)],[(10,10,20,10)],full,False,False)
case('partial_bead_overlap',[(10,10,20,10)],[(10,10.3,20,10.3)],thin,False,False)
case('long_free_cantilever',[(10,9,10,11)],[(10,10,20,10)],thin,True,False)
case('fully_floating_roof',[(10,9,10,11)],[(15,10,20,10)],thin,True,True)
case('two_ended_long_roof',[(10,9,10,11),(20,9,20,11)],[(10,10,20,10)],thin,True,False)
case('internal_sparse_gap_separated',[(10,9,10,11),(20,9,20,11)],[(10,10,20,10)],full,False,False)
(O/'controls.json').write_text(json.dumps(results,indent=2));print('ANALYTIC_NATIVE_CONTROLS_PASSED',len(results))
