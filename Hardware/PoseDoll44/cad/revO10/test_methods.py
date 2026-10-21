"""Regression checks for the specific O10 geometry/checker failure modes."""
from solid_ops import *
from surface_distance import AllTriangleDistance,UnsignedCertificate
from build_face_brake import disc_spring
from evaluate_bench import evaluate

def main():
 cases=[]
 cube=box([-1,-1,-1],[1,1,1]);t=tri(cube);d=AllTriangleDistance(t)
 for p,answer in [([0,0,0],1),([4,0,0],3),([1,0,0],0)]:assert abs(d.EvaluateFunction(p)-answer)<1e-9
 cases.append('unsigned distance agrees with analytic cube, inside and outside')
 line=np.array([[[5,0,0],[6,0,0],[7,0,0]]],float);d=AllTriangleDistance(np.r_[t,line]);assert abs(d.EvaluateFunction([6,.2,0])-.2)<1e-9 and d.counts['discarded_facets']==0
 cases.append('zero-area facet retained as segments, not silently removed')
 outer=box([-2,-2,-2],[2,2,2]);assert abs((cube^outer).volume()-8)<1e-9
 cases.append('containment has positive independent CSG volume despite separated surfaces')
 a,b=disc_spring(0),disc_spring(.45,flip=True);assert a.volume()>1 and abs(a.volume()-b.volume())<1e-6 and (a^b).volume()<1e-8
 cases.append('opposing series discs are both nonempty, equal volume, nonoverlapping')
 m=dict(np.load(OUT/'face_brake/parts.npz'));assert all(from_tri(t).volume()>0 for t in m.values()) and len([k for k in m if 'spring' in k])==8
 cases.append('all 28 face-brake parts nonempty; all eight discs included')
 assert (from_tri(m['C01'])^pose(from_tri(m['C02']),rot(0,75)@rot(1,75))).volume()>1
 cases.append('retained 75/75 fork collision is detected by volume')
 plan=json.loads((H/'bench/revO10/plan.json').read_text());blank=json.loads((H/'bench/revO10/measurement_template.json').read_text());assert evaluate(blank,plan)['status']=='INCOMPLETE'
 test={'sample_id':'SYNTHETIC_TEST_ONLY','material_and_finish':'synthetic','compressed_spring_stack_height_mm':.9,'direction':'positive','hanging_mass_g':250.,'load_perpendicular_arm_mm':100.,'lever_mass_g':0.,'lever_perpendicular_com_arm_mm':0.,'hold_duration_s':60.,'angle_drift_deg':.1,'angle_uncertainty_deg':.05,'running_torque_Nm':.25,'breakaway_torque_Nm':.30,'measured_axial_force_N':None}
 r=evaluate(test,plan);assert r['status']=='MATERIAL_STACK_SCREEN_CANDIDATE' and r['measured_axial_force_N'] is None and not r['full_joint_pass']
 test['angle_drift_deg']=.29;test['angle_uncertainty_deg']=.05;assert evaluate(test,plan)['drift_screen']=='INCONCLUSIVE_RESOLUTION'
 test['hanging_mass_g']=float('nan');assert evaluate(test,plan)['status']=='INVALID'
 cases.extend(['blank observations never pass','synthetic passing coupon never becomes a full joint pass or inferred preload','measurement uncertainty remains inconclusive','nonfinite observation rejected'])
 save('method_regression.json',{'status':'PASS','cases':cases,'test_observations_are_synthetic':True,'hardware_tested':False,'input_sha256':{str(p.relative_to(H)):sha(p) for p in [Path(__file__),Path(__file__).with_name('surface_distance.py'),Path(__file__).with_name('evaluate_bench.py'),OUT/'face_brake/parts.npz',H/'bench/revO10/plan.json']}});print('PASS',len(cases),'regression groups')
if __name__=='__main__':main()

