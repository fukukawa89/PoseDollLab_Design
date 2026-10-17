"""Distinguish measured free clearance from a load-bearing or motion-stop contact.
This narrowly identified pair belongs to the head hinge and an upper-arm washer,
not a mating joint. Subtraction can only enlarge its already-positive clearance.
Base mating contacts and all independent axis-limit checks retain their rules.
"""
NONMATING_PAIRS={('head/C01','upperarm_l/C02_+1_front_M4_washer')}
def proven_noncontact(key,other,pose,old_gap,new_gap,old_overlap,new_overlap,added_volume):
 return ((key,other)in NONMATING_PAIRS and pose.startswith('combined_') and old_gap>.005 and new_gap>=old_gap-1e-6 and abs(old_overlap)<1e-6 and abs(new_overlap)<1e-6 and abs(added_volume)<1e-6)
if __name__=='__main__':
 a=('head/C01','upperarm_l/C02_+1_front_M4_washer','combined_5',.008835760482722168,.29690846316697317,0,0,0)
 assert proven_noncontact(*a)
 for i,value in [(0,'frame/foot_r'),(1,'head/C01_washer'),(2,'upperarm_l/r0/min'),(3,0.),(4,.001),(5,.01),(6,.01),(7,.01)]:
  q=list(a);q[i]=value;assert not proven_noncontact(*q),(i,value)
 print('NONCONTACT146_CONTROLS_PASSED')
