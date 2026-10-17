import numpy as np
from o22_mesh_identity import body_sha

def reference_mesh(n,design):
 v=n['source_v'];f=n.get('source_f',n['f'])
 if 'nominal_source_v' not in n:return v,f
 q=design['nominal_reference'];nv=n['nominal_source_v'];nf=n['nominal_source_f']
 assert q['nominal_reference_qualified'] and q['max_bidirectional_sampled_boundary_distance_mm']<.0001
 assert q['nominal_mesh_sha256']==body_sha({'v':nv,'f':nf})
 assert q['frozen_source_mesh_sha256']==body_sha({'v':v,'f':f})
 return nv,nf


def reference_solid(n,design):
 from build_revo22_fins import solid
 if 'registered_reference_print_v' in n:
  q=design['registered_reference'];v=n['registered_reference_print_v'];f=n['registered_reference_print_f']
  assert q['qualified'] and q['max_bidirectional_sampled_boundary_distance_mm']<.0001
  assert q['printed_reference_mesh_sha256']==body_sha({'v':v,'f':f})
  assert q['frozen_source_mesh_sha256']==body_sha({'v':n['source_v'],'f':n.get('source_f',n['f'])})
  assert np.max(abs(np.array(q['orientation_matrix'])-np.array(design['orientation']['matrix'])))<1e-12
  assert np.max(abs(np.array(q['source_translation_mm'])-np.array(design['orientation']['source_translation_mm'])))<1e-12
  return solid(v,f)
 v,f=reference_mesh(n,design)
 return solid(v@np.array(design['orientation']['matrix']).T+np.array(design['orientation']['source_translation_mm']),f)
