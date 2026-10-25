"""Final numeric sequence; geometry generation must already be complete."""
from validate import *
import runpy

if __name__=='__main__':
    for script in ['verify_current.py','strength.py','closure_checks.py','clearances.py']:
        sys.argv=[str(HERE/script)];runpy.run_path(str(HERE/script),run_name='__main__')
