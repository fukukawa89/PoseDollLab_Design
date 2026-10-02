"""Index concrete deliverables and engineering gates; NOT_RUN is never converted to PASS."""
import datetime
from revo_common import *
def main():
    electronics=read(VERIFY/'electronics_placement.json')
    firmware=read(VERIFY/'firmware/builds.json')
    size=read(VERIFY/'size_tradeoff.json')
    joints=read(VERIFY/'joint_study.json')
    status=dict(revision='RevO-Desktop-iteration1',as_of_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        mainline='Rev O desktop redesign',fallback='Rev N1 ~91cm preserved in place with SHA-256 inventory',
        anchor_reference_height_mm=480,selected_final_height_mm=None,
        complete_body_CAD_delivered=False,new_joint_CAD_delivered=True,new_size_layout_CAD_delivered=True,
        new_pcb_native_placement_delivered=True,new_pcb_routed=False,new_firmware_delivered=True,
        physical_tested=False,manufacturing_released=False,
        gates={
          'baseline':read(VERIFY/'offline/results.json')['status'] if (VERIFY/'offline/results.json').exists() else 'NOT_RUN',
          'firmware_compile':'PASS' if len(firmware['builds'])==7 and all(r['status']=='PASS' for r in firmware['builds'].values()) else 'FAIL',
          'native_schematic_ERC':'PASS' if all(r['checks']['erc']['status']=='PASS' for r in electronics['boards']) else 'FAIL',
          'PCB_DRC':'FAIL','node_in_upperarm_layout':'FAIL','body_mass_budget':'FAIL',
          'joint_solid_intersections':'PASS' if all(not r['solid_intersections'] for r in joints.values()) else 'FAIL',
          'joint_axial_insertion':'FAIL' if any(r['coaxial_insertion_check']['status']=='FAIL' for r in joints.values()) else 'NOT_RUN',
          'joint_service_reservations':'FAIL' if any(r['reservation_intersections'] for r in joints.values()) else 'PASS',
          'preload_and_operating_force':'NOT_RUN_PHYSICAL','multi_axis_assembly':'NOT_RUN',
          'full_body_motion_paths':'NOT_RUN','final_physical_height_and_mass':'NOT_RUN',
          'power_protection_and_tether':'NOT_RUN','magnetic_crosstalk':'NOT_RUN','60Hz_hardware_soak':'NOT_RUN','UE_editor_capture_undo_clutch':'NOT_RUN'},
        next_work=[
          'Redesign N3/N4 as split controller/fanout or prove a rigid torso placement; do not jump to 550 mm.',
          'Redesign the one-piece bearing eye / integral rotor collar to permit insertion and removal before prototype B.',
          'Resolve actual 0.2 mm thermal-via process vs 0.3 mm rules; route and re-run DRC.',
          'Choose catalog spring stacks / measured lining and revise L6 plus clavicle force range from load budget.',
          'Reduce modeled hardware and allocated mass by at least 187 g before the 1.2 kg target can be claimed.',
          'Resolve tool around shaft and exact mating plug reservations; add retained keeper/PCB fasteners.',
          'Finish nested shoulder/hip/wrist geometry, real mechanical profiles and path checks, then full assemblies.',
          'Print only A01/A02 fit coupons; record measurements before releasing B–F samples.'],
        raw_report_paths=['verification/revO/size_tradeoff.json','verification/revO/joint_study.json','verification/revO/electronics_placement.json','verification/revO/firmware/builds.json','verification/revO/offline/results.json'])
    save(VERIFY/'status.json',status)
    print('Rev O iteration indexed. Full-body release blocked by recorded design gates; no physical pass claimed.')
if __name__=='__main__':main()
