"""Seed independent manifests and seven-role firmware without changing Rev M/N1."""
from pathlib import Path
import copy
import shutil
import sys
from revo_common import *

def firmware():
    old = REPO/'Firmware/PoseDollFullBody'
    out = old/'revO'
    (out/'main').mkdir(parents=True, exist_ok=True)
    text = (old/'main/main.c').read_text(encoding='utf-8')
    text = text.replace('/* Six-node PD41 diagnostic firmware;', '/* Rev O G0 + six remote nodes. PD41 v1 remains unchanged;')
    text = text.replace('#include "pd41_core.h"', '#include "pd41_core.h"\n#include "pd41_gateway.h"')
    text = text.replace('static spi_device_handle_t sensor;', '#if !CONFIG_PD_EXTERNAL_GATEWAY\nstatic spi_device_handle_t sensor;\n#endif')
    text = text.replace('#if CONFIG_PD_NODE_ID == 1', '#if CONFIG_PD_EXTERNAL_GATEWAY')
    text = text.replace('static uint16_t even_parity', '#if !CONFIG_PD_EXTERNAL_GATEWAY\nstatic uint16_t even_parity')
    text = text.replace('static bool on_rx(', '#endif\nstatic bool on_rx(')
    text = text.replace('static bool acquire(', '#if !CONFIG_PD_EXTERNAL_GATEWAY\nstatic bool acquire(')
    text = text.replace('#if CONFIG_PD_EXTERNAL_GATEWAY\nstatic void gateway_event', '#endif\n#if CONFIG_PD_EXTERNAL_GATEWAY\nstatic void gateway_event')
    start = text.index('static void gateway_event')
    end = text.index('static void gateway(void)', start)
    text = text[:start] + '''static void gateway_event(pd_cohort_t *cohort,const rx_event_t *e){
    (void)pd_o_dispatch(cohort,e->id,e->bytes,e->us);
}
''' + text[end:]
    local = '(void)pd_boot(&cohort,1,boot_id);(void)pd_ack(&cohort,1,cohort.epoch,boot_id);'
    text = text.replace(local, '')
    start = text.index('        }else{\n            uint16_t words[9]')
    end = text.index('        while(clock_us()<start+PD_DEADLINE_US)', start)
    text = text[:start] + '        }\n' + text[end:]
    text = text.replace('/* N1 alone still emits an explicit missing full-body diagnostic below. */', '/* G0 reports all six remote nodes missing after reset; no synthetic local N1. */')
    text = text.replace('    spi_setup();can_setup();', '    can_setup();\n#if !CONFIG_PD_EXTERNAL_GATEWAY\n    spi_setup();\n#endif')
    (out/'main/main.c').write_text(text, encoding='utf-8')
    (out/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.16)\ninclude($ENV{IDF_PATH}/tools/cmake/project.cmake)\nset(COMPONENTS main)\nproject(posedoll_revo_pd41)\n',encoding='utf-8')
    (out/'main/CMakeLists.txt').write_text('idf_component_register(SRCS "main.c" "pd41_gateway.c" "../../main/pd41_core.c" INCLUDE_DIRS "." "../../main" REQUIRES esp_driver_spi esp_driver_gpio esp_driver_usb_serial_jtag esp_driver_twai esp_timer esp_hw_support)\n',encoding='utf-8')
    (out/'main/Kconfig.projbuild').write_text('''menu "PoseDoll Rev O"
config PD_EXTERNAL_GATEWAY
    bool "External G0 gateway (no sensors)"
    default y
config PD_NODE_ID
    int "Remote measurement node N1..N6 (ignored on G0)"
    range 1 6
    default 1
endmenu
''',encoding='utf-8')
    defaults=(old/'sdkconfig.defaults').read_text(encoding='utf-8')
    (out/'sdkconfig.defaults').write_text(defaults+'\nCONFIG_PD_EXTERNAL_GATEWAY=y\n',encoding='utf-8')
    save(out/'source_origin.json', {'status':'DIGITAL_FIRMWARE_CANDIDATE_NOT_FLASHED','legacy_main_sha256':sha(old/'main/main.c'),'shared_unmodified_core_sha256':sha(old/'main/pd41_core.c'),'legacy_config_sha256':sha(old/'main/pd41_config.h'),'measurement_count':41,'protocol_slots':44,'gateway_role':'G0','remote_nodes':[1,2,3,4,5,6]})

def main():
    req=read(REPO.parent/'PoseDoll_RevO/revO_desktop_requirements.json')
    save(HW/'mechanical_manifest/revO_requirements_source.json',req)
    base=read(HW/'mechanical_manifest/network_revM.json')
    network=copy.deepcopy(base)
    network.update(revision='O-desktop-design-in-progress',gateway={'name':'G0','role':'external_gateway','measurement_channels':0},source_revM_sha256=sha(HW/'mechanical_manifest/network_revM.json'))
    network['can'].update(node_count=7,measurement_node_count=6,gateway_node='G0',linear_node_order=['G0','N1','N5','N6','N2','N3','N4'],termination_nodes=['G0','N4'],physical_wire_length_validated=False)
    network['power'].update(external_input_V=5,selection='5V_INITIAL_DESIGN_BASELINE_12V_COMPARISON_PENDING',budget_validated=False,power_topology='external_5V_and_internal_six_fused_branches',old_boards_12V_compatible=False)
    network['firmware_project']='Firmware/PoseDollFullBody/revO'
    network['board_layout_status']='PLACEMENT_STUDY_NOT_ROUTED_NOT_RELEASED'
    network['pin_assignment_status']='LEGACY_GPIO_MAP_RETAINED_NEW_BOARD_CONNECTIVITY_MUST_MATCH'
    for n in network['nodes']:
        n['role']='remote_measurement'
    save(HW/'mechanical_manifest/network_revO.json',network)
    specs={
      'revision':'O-iteration1','status':'SPACE_AND_COMPONENT_STUDY_NOT_MANUFACTURING_RELEASE',
      'anatomy':{'anchor_height_mm':480,'study_heights_mm':[420,450,480,520,550],'characters':['manny','quinn']},
      'hardware_fixed':{'magnet_diameter_mm':6,'magnet_thickness_mm':2.5,'sensor_airgap_target_mm':1.5,'sensor_board_mm':[12,10,1.0],'sensor_package_face_offset_mm':1.995,'minimum_mount_wall_mm':1.6,'pcb_service_travel_mm':12,'cable_min_bend_radius_assumed_mm':12,'small_journal_mm':4,'medium_large_journal_mm':6},
      'joint_families':{
        'S4':{'journal_mm':4,'friction_outer_radius_mm':8,'friction_inner_radius_mm':3.2,'body_outer_radius_mm':10,'preload_explore_N':[15,100]},
        'M6':{'journal_mm':6,'friction_outer_radius_mm':10,'friction_inner_radius_mm':4.2,'body_outer_radius_mm':12,'preload_explore_N':[30,200]},
        'L6':{'journal_mm':6,'friction_outer_radius_mm':12,'friction_inner_radius_mm':4.2,'body_outer_radius_mm':14,'preload_explore_N':[50,350]}},
      'uncertainty':{'friction_mu_range_assumed':[0.08,0.22],'spring_specification':'CUSTOM_WAVE_SPRING_RFQ_NOT_SELECTED','tolerances':'FIT_COUPON_AND_SUPPLIER_REVIEW_REQUIRED'},
      'physical_tested':False,'manufacturing_released':False}
    save(HW/'mechanical_manifest/desktop_revO.json',specs)
    firmware()
    print('Rev O manifests and separate G0/N1..N6 firmware prepared; historical sources untouched.')

if __name__=='__main__':
    main()
