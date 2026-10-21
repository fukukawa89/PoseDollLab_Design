from common import *
import importlib
for name in ('hinge','twist','core','tut','wide_tut','three_axis','clavicle_core','ankle_core'):
 print('REBUILD',name,flush=True)
 importlib.import_module(name).main()
save('module_generation_sources.json',{'sources_sha256':{p.name:sha(p) for p in Path(__file__).parent.glob('*.py')},'parts_sha256':{p.name:sha(p) for p in OUT.glob('*_parts.npz')},'physical_tested':False})
