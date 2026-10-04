"""JINPAT LPMS-05D packaging candidate against the stopped twist bore.
Catalogue exterior bodies are envelopes, not supplier CAD or internal parts.
Retention, flexible lead transitions, electrical noise and drag remain tests.
"""
from solid_ops import *
from build_finite_twist import rotor_stub,housing

def main():
 dest=OUT/'slipring';dest.mkdir(exist_ok=True)
 # The 9.6 mm barrel and separately listed 1 mm rotor extension are retained.
 # Other catalogues use LPMS-05 and different length conventions: not conflated.
 body=cylinder(2.75,-34.8,-25.2);tip=cylinder(1,-25.2,-24.2)
 sleeve=(cylinder(4.15,-37.5,-24.95)+cylinder(8,-37.5,-35.5))-cylinder(2.85,-35,-24.9)-cylinder(1.4,-37.6,-34.9)
 shell=md.Manifold()
 for k,s in housing(-260,-40).items():shell+=s
 rotor=rotor_stub();intersections={'barrel_vs_rotor_mm3':(body^rotor).volume(),'barrel_vs_sleeve_mm3':(body^sleeve).volume(),'sleeve_vs_rotor_mm3':(sleeve^rotor).volume(),'sleeve_vs_housing_mm3':(sleeve^shell).volume()}
 assert max(abs(v) for v in intersections.values())<1e-6
 parts={'catalogue_barrel':body,'catalogue_rotor_tip':tip,'proposed_sleeve':sleeve,'existing_rotor':rotor}
 np.savez_compressed(dest/'envelopes.npz',**{k:tri(s) for k,s in parts.items()})
 for k,s in parts.items():export_stl(dest/(k+'.stl'),tri(s))
 out={'candidate':'JINPAT LPMS-05D, Shenzhen','catalogue_dimensions_mm':{'body_diameter':5.5,'body_length':9.6,'rotor_exposed_length':1,'rotor_diameter':2},'catalogue_circuits':5,'catalogue_current_A_each':1,'catalogue_voltage_V':48,'proposed_assignment':['3V3','GND','RS485_A','RS485_B','spare'],'model_dimensions_mm':{'existing_bore_diameter':8.8,'sleeve_outer_diameter':8.3,'sleeve_nominal_radial_clearance_to_rotor':.25,'sleeve_flange_diameter':16,'added_rear_axial_envelope':2},'envelope_intersections':intersections,'previous_wire_coil_candidate_case_diameter_mm':39,'existing_twist_case_cylinder_diameter_mm':25,'conditional_radial_envelope_reduction_mm':14,'manufacturing_released':False,'hardware_tested':False,'supplier_contacted':False,'selection':'Preferred compact candidate for component evaluation; not a released replacement','unresolved':['LPMS-05D dimensional drawing and lead exit revision must match order; do not replace with generic LPMS-05 without recheck','Only sleeve and catalogue bodies modeled; adhesive/mechanical retention, rotating coupling and strain relief not approved','Bend-axis leads and complete shoulder harness absent','RS485 waveform, error rate, power interruption, recovery and drag not measured','A supplier 1A rating or signal-family marketing does not certify this installation'],'primary_sources':[{'url':'https://www.sliprings.cn/upload/portal/20230920/cf5d5feb2190d6a1f043a01872a3288e.pdf','facts':'LPMS table: 5.5 x 9.6 body, 1 mm exposed rotor, diameter 2 mm, 5 circuits 1 A 48 V','access':'Search-index PDF table verified 2026-09-26; complete PDF open timed out'},{'url':'https://www.electricslipring.com/h-pd-388.html','facts':'LPMS-05D product page: 5 x 1A, 48V, gold contacts; lists dynamic resistance fluctuation at most 35 milliohm. Not a worst-case interruption bound.','access':'Opened 2026-09-26'},{'url':'https://www.slipring.cn/JINPATslipring97.html','facts':'Specific LPMS-05D size and distinction from customized signal variants','access':'Search result 2026-09-26'}]}
 save('slipring/study.json',out);print(json.dumps(intersections));print('Envelope only; sleeve retention, leads and signal behavior unqualified.')
if __name__=='__main__':main()
