import math, sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from static_capture_reference import resolve_single_turn, CaptureRejected, FIXED

class AbsoluteBranch(unittest.TestCase):
    def count(self,degrees):return round((degrees%360)*FIXED/360)%FIXED
    def solve(self,degrees,sign=1):
        return resolve_single_turn(self.count(degrees),zero_rad=0,sign=sign,ratio=1,
            lower_rad=math.radians(-175),upper_rad=math.radians(175))
    def test_jump_between_static_poses(self):
        self.assertAlmostEqual(math.degrees(self.solve(170)),170,delta=.03)
        self.assertAlmostEqual(math.degrees(self.solve(-170)),-170,delta=.03)
    def test_sign(self):self.assertAlmostEqual(math.degrees(self.solve(170,-1)),-170,delta=.03)
    def test_unknown_multi_turn_rejected(self):
        with self.assertRaises(CaptureRejected):
            resolve_single_turn(0,zero_rad=0,sign=1,ratio=1,lower_rad=0,upper_rad=4*math.pi)
    def test_outside_limits_rejected(self):
        with self.assertRaises(CaptureRejected):self.solve(180)
    def test_ratio(self):
        v=resolve_single_turn(self.count(60),zero_rad=0,sign=1,ratio=2,
            lower_rad=0,upper_rad=math.pi/2)
        self.assertAlmostEqual(math.degrees(v),30,delta=.03)
if __name__=='__main__':unittest.main(verbosity=2)
