"""Independent saved-geometry checks; run after fullbody.py has finished."""
from validate import *
import engineering,ue_mapping,audit_hardware

if __name__=='__main__':
    checks();collision();p,z,s=read_assembly();engineering.axes(p,z);ue_mapping.main();audit_hardware.main()
