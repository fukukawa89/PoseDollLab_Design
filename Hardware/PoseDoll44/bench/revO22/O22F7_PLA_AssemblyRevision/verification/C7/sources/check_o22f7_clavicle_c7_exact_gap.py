from pathlib import Path
src=Path('scripts/check_o22f7_clavicle_c6_function.py').read_text('utf-8-sig').replace('W005_C6.npz','W005_C7.npz');exec(src.split('cache={};new_hits=')[0])
from o22_triangle_gap import gap
raws=dict(poses);rows=[]
for issue in read(C/'W005_C6_function_review.json')['new_interferences_or_close_contacts']:
 raw=raws[issue['pose']];ff,oo=kin.owners(raw);t=owners[issue['part']];od=(ff[t[1]] if t[0]=='f' else oo[t[1:]])@inverse0[t];own=ff['clavicle_l.protract_frame']@invown;obs=b.g.move(world[issue['part']],I@np.linalg.inv(own)@od)
 rec=dict(issue,verified_delta_gap=gap(b.g.tri(new['added']),b.g.tri(obs),.2),root_gap=gap(b.g.tri(new['root']),b.g.tri(obs),.2));rows.append(rec);print(rec,flush=True)
put(C/'W005_C7_exact_gap_review.json',{'rows':rows,'candidate_sha256':sha(C/'W005_C7.npz')})
