from pathlib import Path
src=Path('scripts/check_o22f7_clavicle_c5_function.py').read_text('utf-8-sig');exec(src.split('cache={};new_hits=')[0])
rows=[];raws=dict(poses);parts={k:new[k] for k in ['root','distal','nut_0','screw_0']};parts['added']=new['added']
for issue in read(C/'W005_C5_function_review.json')['new_interferences_or_close_contacts']:
 raw=raws[issue['pose']];ff,oo=kin.owners(raw);t=owners[issue['part']];obstacle_delta=(ff[t[1]] if t[0]=='f' else oo[t[1:]])@inverse0[t];own=ff['clavicle_l.protract_frame']@invown;rel=I@np.linalg.inv(own)@obstacle_delta;obstacle=b.g.move(world[issue['part']],rel);r=dict(issue,details={k:{'overlap':float((s^obstacle).volume()),'gap':float(s.min_gap(obstacle,.1))} for k,s in parts.items()});rows.append(r);print(r,flush=True)
put(C/'W005_C5_contact_components.json',{'rows':rows})
