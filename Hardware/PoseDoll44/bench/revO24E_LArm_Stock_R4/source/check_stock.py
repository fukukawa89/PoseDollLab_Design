from build_stock import *
import time,itertools

def saved():
 a=load(OUT/'production_assembly.json')['parts'];z=np.load(OUT/'production_meshes.npz')
 s=[md.Manifold(md.Mesh64(np.array(z[str(p['i'])+'v'],copy=True),np.array(z[str(p['i'])+'f'],dtype=np.uint64,copy=True))) for p in a]
 return a,s

def motion(quick=False,dense=False):
 a,ss=saved();digest=sha(OUT/'production_meshes.npz')
 anatomy={ROOT:0,'l_shoulder_flex':0,'l_shoulder_abduct':0,'l_upperarm_roll':0,'l_elbow_flex':1,'l_forearm_roll':1,'l_wrist_flex':2,'l_wrist_deviation':2}
 pairs=np.array(list(itertools.combinations(range(len(a)),2)));rows=[];findings={}
 cases={'neutral':POSES['neutral']}
 if not quick:cases=POSES
 if dense:
  cases=dict(neutral=POSES['neutral'])
  for axis in PROFILE['axes']:
   lo,hi=axis['limits_deg'];angles=np.linspace(lo,hi,math.ceil((hi-lo)/2)+1)
   for no,val in enumerate(angles):
    q=dict(POSES['neutral']['angles']);q[axis['id']]=float(val);cases[f'{axis["id"]}/{no}']=dict(angles=q)
  for name,p in POSES.items():
   if name.startswith('ROM/') or name=='neutral':continue
   for no,t in enumerate(np.linspace(0,1,21)):
    q={ax['id']:(1-t)*POSES['neutral']['angles'].get(ax['id'],0)+t*p['angles'].get(ax['id'],0) for ax in PROFILE['axes']};cases[f'path/{name}/{no}']=dict(angles=q)
 for name,p in cases.items():
  f=frames(p['angles']);world=[moved(s,f[x['frame']]) for x,s in zip(a,ss)];bb=np.array([e.bounds(s) for s in world]);hits=[];advisory=[];fits=[]
  active=np.all(bb[pairs[:,0],1]>=bb[pairs[:,1],0]-.0001,axis=1)&np.all(bb[pairs[:,1],1]>=bb[pairs[:,0],0]-.0001,axis=1)
  for i,j in pairs[active]:
   if name!='neutral' and a[i]['frame']==a[j]['frame']:continue
   vol=(world[i]^world[j]).volume()
   if vol>.02:
    retention=((a[i]['sku']=='FW4' and (a[i]['name'].endswith('_F1') or a[i]['name'] in ['KEEP_E-H1133','KEEP_E-H1141','KEEP_E-H1149','KEEP_E-H1157']) and a[j]['name'] in ['SHOULDER_PITCH','UPPER_ARM','KEEP_E-P019']) or (a[j]['sku']=='FW4' and (a[j]['name'].endswith('_F1') or a[j]['name'] in ['KEEP_E-H1133','KEEP_E-H1141','KEEP_E-H1149','KEEP_E-H1157']) and a[i]['name'] in ['SHOULDER_PITCH','UPPER_ARM','KEEP_E-P019']))
    if retention and vol<.15:
     fits.append(dict(a=a[i]['name'],b=a[j]['name'],volume_mm3=vol,reason='declared 0.06 mm radial locating-pad interference; elastic/print fit not physically qualified'));continue
    h=dict(a=a[i]['name'],b=a[j]['name'],volume_mm3=float(vol));required=abs(anatomy[a[i]['frame']]-anatomy[a[j]['frame']])<=1
    (hits if required else advisory).append(h)
    if required:findings.setdefault(h['a']+' / '+h['b'],[]).append([name,round(vol,4)])
  rows.append(dict(pose=name,count=len(hits),collisions=hits,advisory_count=len(advisory),advisory_pairs=advisory,intended_retention_fits=fits))
  if not dense or len(rows)%50==0 or hits:print('POSE',len(rows),name,len(hits),len(advisory),flush=True)
 put(OUT/'verification'/('motion_dense.json' if dense else 'motion_quick.json' if quick else 'motion.json'),dict(status='PASS_SAMPLED' if not findings else 'FAIL',geometry_sha256=digest,cases=rows,pairs=findings,scope='All independent bodies in same or adjacent anatomical segments; same-frame overlaps checked once at neutral. Non-adjacent hand/upper-arm contacts advisory. Dense uses <=2 degree single-axis steps and 21 samples on each A-to-named-pose path. Finite sampling is not a full configuration-space proof.'))
 print('HITS',json.dumps(findings,ensure_ascii=False),flush=True)

if __name__=='__main__':motion('--quick' in sys.argv,'--dense' in sys.argv)
