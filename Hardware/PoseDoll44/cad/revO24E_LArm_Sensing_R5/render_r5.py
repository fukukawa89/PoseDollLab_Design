"""Blender runner sharing the accepted R4 camera/rig implementation, R5 meshes only."""
from pathlib import Path
base=Path(__file__).resolve().parent.parent/'revO24E_LArm_Stock_R4/render_stock.py'
s=base.read_text('utf8').replace('revO24E_LArm_Stock_R4','revO24E_LArm_Sensing_R5').replace('O24E_LArm_Stock_R4','O24E_LArm_Sensing_R5').replace('O24E_left_arm_stock_R4.blend','O24E_R5_sensing_arm.blend')
s=s.replace("kit['structural_parts']+kit['hardware']","sum([kit[x] for x in ['structural_parts','hardware','electronics','soft_parts']],[])")
s=s.replace("color=colors[p['role']]","color={'electronics':(.08,.48,.26),'magnet':(.8,.2,.16),'insulator':(.9,.8,.3)}.get(p['role'],colors.get(p['role'],(.55,.55,.55)))\n    if p['role']=='structure' and not p.get('baseline_name'):color=(.88,.64,.28)")
s=s.replace('mechanical trial; electronics reservations provided separately. Common hardware trial; final STL geometry.','R4 mechanically accepted; R5 seven actual magnetic measurement channels. Electrical physical validation pending. Final STL geometry.')
s=s.replace("shot('retained_wrist_centre.png'","shot('sensor_wrist_centre.png'").replace("shot('retained_shoulder.png'","shot('sensor_shoulder.png'")
exec(compile(s,str(Path(__file__)),'exec'))
