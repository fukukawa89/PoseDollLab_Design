"""Update non-geometric design notes after a metadata correction."""
import bpy,json
from pathlib import Path
B=Path(__file__).resolve().parents[2]/'bench/revO24D'
bpy.ops.wm.open_mainfile(filepath=str(B/'O24D_full_body.blend'))
for p in json.loads((B/'assembly.json').read_text('utf8'))['parts']:
    bpy.data.objects[p['name']]['design_note']=p['notes']
bpy.ops.wm.save_as_mainfile(filepath=str(B/'O24D_full_body.blend'))
import runpy
runpy.run_path(str(Path(__file__).with_name('verify_blender.py')),run_name='__main__')
