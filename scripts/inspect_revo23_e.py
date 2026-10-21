"""Export exact candidate meshes for focused Blender inspection."""
from build_revo23_wire_seats import *
ap=argparse.ArgumentParser();ap.add_argument('--mode',default='fists');args=ap.parse_args()
parts,p,cfg=load_e();F=frames(p,p['neutral_raw_deg'])
meshes={};items=[]
for key,item in parts.items():
    body=item['body']
    if args.mode=='fists':
        chosen=key=='frame/hand_l'
    elif args.mode=='collar':
        chosen=key=='frame/clavicle_r'
    elif args.mode=='arm':
        chosen=body.startswith(('upperarm_r','elbow_r','forearm_r','hand_r','wrist_r'))
    else:chosen=item['role']=='structure'
    if not chosen:continue
    i=str(len(items));v,f=vf(item['s']);M=F[item['token']]
    meshes[i+'v']=v@M[:3,:3].T+M[:3,3];meshes[i+'f']=f
    items.append(dict(i=i,key=key,color=[.70,.75,.81] if item['role']=='structure' else [.25,.40,.6]))
if args.mode=='collar':
    key='frame/clavicle_r';kz=np.load(DHISTORY/'source/retained_interfaces.npz')
    s=solid(kz[key+'|v'],kz[key+'|f']);M=F[parts[key]['token']]
    for a in s.decompose():
        i=str(len(items));v,f=vf(a);meshes[i+'v']=v@M[:3,:3].T+M[:3,3];meshes[i+'f']=f
        items.append(dict(i=i,key='land'+i,color=[1,.45,.1]))
    audit=read(EROOT/'load_paths_candidate/frame__clavicle_r.json')
    for row in audit['rows'][:1]:
        if row['cut_center_mm'] is None:continue
        c=np.asarray(row['cut_center_mm'])
        s=union([ball(pt,.5) for pt in np.asarray(row['cut_points_mm'])[::3]])
        i=str(len(items));v,f=vf(s);meshes[i+'v']=v@M[:3,:3].T+M[:3,3];meshes[i+'f']=f
        items.append(dict(i=i,key='cut'+i,color=[1,.05,.05]))
np.savez_compressed(EROOT/(args.mode+'_render.npz'),**meshes)
put(EROOT/(args.mode+'_render.json'),dict(items=items,mode=args.mode))
