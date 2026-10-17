from pathlib import Path
r=Path('PoseDoll_HW44_Plan/design/scripts')
p=r/'transfer_revo22_f5_family289.py';s=p.read_text();s=s.replace(" dropped=[]", " strict=ban\n if d.get('connector_void_policy')=='whole_stem_extraction':\n  from build_revo22_f5_magnet340 import run as mg\n  mg(pid);mn=np.load(O/'guards_magnet'/f'{pid}.npz');strict=solid(mn['v'],mn['f']).transform(np.c_[Q2,t2]);mv,mf=vf(strict);np.savez_compressed(dst/'verification/strict_magnet_guards.npz',v=mv,f=mf)\n dropped=[]")
s=s.replace('(teeth^(ban-body))','(teeth^(strict-body))').replace('(tt^(ban-body))','(tt^(strict-body))').replace("['root','tip','target','removal_vector']", "['root','tip','target','removal_vector','stem_removal_vector']")
p.write_text(s)
p=r/'stage_revo22_f5_compact296.py';s=p.read_text().replace("'f5_fin_groups.npz','guards.npz'", "'f5_fin_groups.npz','guards.npz','strict_magnet_guards.npz'");p.write_text(s)
s=(r/'add_revo22_f5_gusset338.py').read_text()
s=s.replace("s=solid(n['v'],n['f']);hull=md.Manifold.hull_points(n['v'])", "body=solid(n['v'],n['f']);fin=solid(n['fin_v'],n['fin_f']);teeth=solid(n['teeth_v'],n['teeth_f']);s=fin+teeth;hull=md.Manifold.hull_points(np.r_[n['fin_v'],n['teeth_v']])")
s=s.replace("mesh=trimesh.Trimesh(n['v'],n['f'],process=False)","mesh=trimesh.Trimesh(*vf(s),process=False)")
s=s.replace("ref=solid(n.get('f5_pre_relief_v',n['v']),n.get('f5_pre_relief_f',n['f']))", "ref=s")
s=s.replace("if(add^guard).volume()>1e-6 or(add^solid(n['fin_v'],n['fin_f'])).volume()>1e-6:continue", "if (gusset^body).volume()>1e-7 or gusset.min_gap(body,.1)<.06:continue")
a=s.index("     ab=np.array(add.bounding_box())");b=s.index("     proposal=s+gusset",a);s=s[:a]+s[b:]
s=s.replace("     s=proposal;records.append", "     fin+=gusset;s=proposal;records.append")
s=s.replace("min(10.,ref.volume()*.002)","30.").replace("kind='permanent_inner_gusset'", "kind='temporary_fin_gusset'")
a=s.index(" n.setdefault('f5_pre_relief_v'");b=s.index(";return True",a)
s=s[:a]+" n['fin_v'],n['fin_f']=vf(fin);np.savez_compressed(b/'parts'/f'{pid}.npz',**n);shutil.copy2(a/'verification/guards.npz',b/'verification/guards.npz');d.update(trial=label,temporary_fin_gussets=d.get('temporary_fin_gussets',[])+records,support_volume_mm3=float((fin+teeth).volume()),support_count=len(material_components(fin)));put(b/'design'/f'{pid}.json',d)"+s[b:]
s=s.replace("src=cc[0][2]","src='counter332_route0'").replace('gusset338','fin343').replace('GUSSET338','FIN343')
(r/'repair_revo22_f5_fin343.py').write_text(s)
