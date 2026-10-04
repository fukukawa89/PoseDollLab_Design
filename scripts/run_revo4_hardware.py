"""Immutable hardware experiment. Run steps passing does NOT make candidates qualified."""
from revo4_evidence import *
def main():
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('run_id');a=ap.parse_args();r=Run(a.run_id,include_ue=False);py=str(REPO/'.venv/Scripts/python.exe')
 r.step('baseline',[py,'-X','utf8','scripts/stage_revo4_baseline.py'],expected_paths=[r.path/'baseline.json',r.path/'joint.json'])
 r.step('electronics',['D:/ProgramFiles/KiCad/10.0/bin/python.exe','-X','utf8','scripts/build_revo4_electronics.py'],dependencies=['baseline'],extra_env={'KICAD10_3DMODEL_DIR':'D:/ProgramFiles/KiCad/10.0/share/kicad/3dmodels'},expected_paths=[r.path/'electronics.json'],artifact_roots=[r.out/'electronics'])
 r.step('pcba_geometry',[py,'-X','utf8','Hardware/PoseDoll44/tools/run_cad.py','Hardware/PoseDoll44/cad/revO4/audit_layout.py'],dependencies=['electronics'],expected_paths=[r.path/'pcba_geometry.json'],artifact_roots=[r.out/'pcba'])
 r.step('backlash',[py,'-X','utf8','Hardware/PoseDoll44/tools/run_cad.py','Hardware/PoseDoll44/cad/revO4/check_backlash.py'],dependencies=['baseline'],expected_paths=[r.path/'backlash.json'],artifact_roots=[r.out/'backlash'])
 r.step('remote_link',['cmd.exe','/d','/c',str(REPO/'scripts/Run-RevO4-LinkTests.cmd'),str(r.out/'remote_link')],expected_paths=[r.out/'remote_link/pdr4_golden.bin'],artifact_roots=[r.out/'remote_link'])
 r.step('packaging',[py,'-X','utf8','scripts/packaging_revo4.py'],dependencies=['baseline','pcba_geometry'],expected_paths=[r.path/'packaging.json',r.out/'packaging_scene.json'])
 r.step('comparison',[py,'-X','utf8','scripts/analyze_revo4_hardware.py'],dependencies=['electronics','pcba_geometry','remote_link','packaging'],expected_paths=[r.path/'hardware_comparison.json'])
 result=r.finish();print(result['status']);return 0 if result['status']=='PASS_EXECUTION_ONLY' else 1
if __name__=='__main__':raise SystemExit(main())
