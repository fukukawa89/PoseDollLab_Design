"""Real UE accepts only the valid simulated PDG5 -> PDS1 path. Isolated test project."""
from pathlib import Path
import json,os,subprocess,time,traceback,unreal
root=Path(unreal.Paths.project_dir());out=root/'reports/o5';out.mkdir(parents=True,exist_ok=True)
result={'passed':False,'scope':'synthetic PDG5 bytes -> production BridgeCore -> real UE TCP -> Capture; no serial/MCU/hardware','cases':[]};proc=None

def cmd(a,arg='',expect=True):
 r=json.loads(unreal.PoseDollEditorLibrary.session_command(a,arg))
 if expect is not None:assert r['ok']==expect,(a,r)
 return r

def wait(pred):
 end=time.monotonic()+5
 while time.monotonic()<end:
  cmd('tick');s=cmd('status')
  if pred(s):return s
  time.sleep(.01)
 raise AssertionError(cmd('status'))
try:
 level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 assert level.new_level('/Game/PoseDollO5/BridgeBytes')
 actor=actors.spawn_actor_from_class(unreal.SkeletalMeshActor,unreal.Vector(),unreal.Rotator())
 actor.skeletal_mesh_component.set_skeletal_mesh_asset(unreal.load_asset('/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple'))
 seq=unreal.AssetToolsHelpers.get_asset_tools().create_asset('O5BridgeBytes','/Game/PoseDollO5',unreal.LevelSequence,unreal.LevelSequenceFactoryNew())
 seq.set_display_rate(unreal.FrameRate(24,1));seq.set_playback_end(120);seq.add_possessable(actor)
 assert unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(seq)
 assert unreal.PoseDollEditorLibrary.bind_target(seq,actor.skeletal_mesh_component)
 for idx,case in enumerate(['normal','missing','crc','boot']):
  ready=out/'bridge_ready';ready.unlink(missing_ok=True)
  proc=subprocess.Popen([os.environ['POSEDOLL_TEST_PYTHON'],'-X','utf8',str(Path(os.environ['POSEDOLL_DESIGN_ROOT'])/'Tools/PoseDollHardwareBridge/synthetic_ue_peer.py'),'--ue-root',str(root),'--case',case,'--ready',str(ready)],creationflags=0x08000000)
  until=time.monotonic()+5
  while not ready.exists():
   assert time.monotonic()<until;time.sleep(.01)
  cmd('connect','static');wait(lambda s:s.get('static_source') and s['state']=='Ready')
  unreal.LevelSequenceEditorBlueprintLibrary.set_current_time(20+idx*10);before=cmd('status')['captures']
  cid=cmd('snapshot_capture')['capture_id'];s=wait(lambda s:s['snapshot_state'] in ('Committed','Fault','Cancelled','TimedOut'))
  assert s['captures']==before+int(case=='normal'),(case,s)
  if case=='normal':assert s['snapshot_state']=='Committed' and s['capture_id']==cid
  result['cases'].append({'case':case,'captures_added':s['captures']-before,'result':s})
  cmd('disconnect');proc.wait(timeout=5);proc=None
 result['passed']=True
except:result['exception']=traceback.format_exc();unreal.log_error(result['exception'])
finally:
 cmd('disconnect',expect=None)
 if proc is not None:
  try:proc.wait(timeout=5)
  except subprocess.TimeoutExpired:proc.terminate()
 unreal.LevelSequenceEditorBlueprintLibrary.close_level_sequence();(out/'bridge_editor.json').write_text(json.dumps(result,indent=2),encoding='utf-8');unreal.SystemLibrary.quit_editor()
