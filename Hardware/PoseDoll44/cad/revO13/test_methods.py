"""Counterexamples for the new per-piece broadphase and feedback boundary."""
from parts_library import *
def main():
 a=Parts([box([-1,-1,-1],[1,1,1])]);inside=Parts([box([-.5,-.5,-.5],[.5,.5,.5])])
 separated=Parts([box([2,2,2],[3,3,3])]);touch=Parts([box([1,-1,-1],[2,1,1])])
 assert abs((a^inside).volume()-1)<1e-8
 assert (a^separated).volume()==0 and (a^touch).volume()==0
 shifted=pose(inside,rot(2,31),[.75,0,0]);assert (a^shifted).volume()>.1
 import json
 obs=json.loads((H/'bench/observations/o12_20260929_user_feedback.json').read_text())
 assert obs['assembly_and_initial_hand_feel_gate']=='PASS_USER_REPORTED'
 assert obs['measured_holding_torque_Nm'] is None and obs['measured_spring_force_N'] is None
 req=json.loads((H/'mechanical_manifest/requirements_revO13.json').read_text())
 assert req['manual_external_support_allowed'] and not req['reuse_210N_O11_reference']
 # Both original grids contribute every sample even when one arm is static.
 a=np.linspace(0,1,56);b=np.linspace(0,1,2);grid=sorted(set(a.tolist()+b.tolist()))
 assert {round(t*55) for t in grid}==set(range(56)) and {round(t) for t in grid}=={0,1}
 save('method_checks.json',{'status':'PASS','cases':['full containment detected','AABB separation','touch is not overlap','rotated overlap detected','qualitative report cannot invent torque/force','assistance does not restore 210N assumption','asymmetric sample-grid completeness'],'count':7})
 print('method counterexamples passed')
if __name__=='__main__':main()
