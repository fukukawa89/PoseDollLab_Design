import ast
from pathlib import Path
for name in ['verify_revo22_f5_contacts298.py','publish_revo22_f5_compact302.py','enhance_revo22_f5_delivery368.py','polish_revo22_f5_delivery439.py','package_revo22_f5_delivery375.py']:
 ast.parse((Path(__file__).parent/name).read_text(encoding='utf-8-sig'));print('SYNTAX_OK',name)
