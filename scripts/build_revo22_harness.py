"""46 independent five-wire harnesses, actual attachment frames and motion slack.
Layout is an engineering routing template, not a fatigue/clearance qualification.
"""
import json,math,numpy as np
import build_revo22_assembly as a
b=a.b;g=a.g;B=a.B;D=B/'harness';D.mkdir(exist_ok=True)
p,m,base,changed,service,C=a.model();preset=g.read(B/'profiles/default_pose.json')['raw_deg'];posed,mat,frames=a.pose_parts(p,m,base,preset);fbase,_=a.owners(base)
wire=g.read(B/'profiles/wiring.json');nodes=[n for bank in wire['banks'] for n in bank['nodes']];joint={j['child']:j for j in a.profile['joints']};comps=g.read(B/'electronics/carrier/components.json')
# All anchor coordinates are body-local, recoverable in any measured pose.
anchors={};anchor_world={}
for body,F in frames.items():
 key='frame/'+body
 if key not in posed or body in ['pelvis','chest']:continue
 # Rear-most area of the actual printed frame near its centre; tie seats on its surface.
 t=g.tri(posed[key]);bb=np.array(posed[key].bounding_box());center=(bb[:3]+bb[3:])/2
 axis=F[:3,2];axis/=np.linalg.norm(axis);q=(t-center)@axis
 hits=[]
 for i,j in [(0,1),(1,2),(2,0)]:
  mask=q[:,i]*q[:,j]<0;u=q[mask,i]/(q[mask,i]-q[mask,j]);hits.extend(t[mask,i]+u[:,None]*(t[mask,j]-t[mask,i]))
 pts=np.array(hits) if hits else t.reshape(-1,3);back=-F[:3,0];surface=pts[np.argmax(pts@back)];point=surface+back*2
 anchors[body]={'owner':body,'part':key,'point_body_mm':(np.linalg.inv(F)@np.r_[point,1])[:3].tolist(),'surface_world_A_mm':surface.tolist(),'wire_offset_mm':2,'binding':'2.5mm tie around the existing fixed bone; not across a rotating seam'};anchor_world[body]=point
# Thorax exit at existing housing slot and pelvis trunk tie at the back of frame.
for body,point in [('chest',(C@np.array([58,98,17,1]))[:3]),('pelvis',np.array([-39.,0.,283.]))]:
 F=frames[body];anchors[body]={'owner':body,'part':'frame/'+body,'point_body_mm':(np.linalg.inv(F)@np.r_[point,1])[:3].tolist(),'binding':'Existing frame/housing tie, keep adjustment screw access'};anchor_world[body]=point

def lineage(body):
 out=[]
 while body not in ('chest','pelvis'):
  if body in anchors:out.append(body)
  if body not in joint:break
  body=joint[body]['parent']
 if body=='pelvis':out+=['pelvis','waist']
 return list(dict.fromkeys(out+['chest']))

def sensor_frame(n,qframes,qowners):
 key=n['sensor_part_O20'];A,source=service[key];mm=m.get(source)
 if mm is None:mm=next(m[k] for k in m if k.startswith(key+'/'))
 if mm['owner']=='rigid_frame':delta=qframes[mm['body']]@np.linalg.inv(fbase[mm['body']])
 else:
  _,oldowners=a.owners(base);delta=qowners[(mm['module'],mm['owner'])]@np.linalg.inv(oldowners[(mm['module'],mm['owner'])])
 E=delta@A
 if np.linalg.det(E[:3,:3])<0:E[:3,0]*=-1
 return E,mm

def route(n,q):
 ff,oo=a.owners(q);E,mm=sensor_frame(n,ff,oo);owner_body=mm['body']
 if owner_body not in ff:
  jj=next(j for j in a.profile['joints'] if j['id']==mm['module']);owner_body=jj['parent'] if mm['owner'] in ('P','parent') else jj['child']
 chain=lineage(owner_body);pts=[(E@np.array([0,4.05,15.55,1]))[:3],(E@np.array([0,12,15.55,1]))[:3]]
 pts += [(ff[k]@np.r_[anchors[k]['point_body_mm'],1])[:3] for k in chain if k in anchors]
 # Label maps into the exact native connector value (A01, B01, C01).
 cc=next(c for c in comps if c.get('value','').startswith(n['connector']+' ') or c.get('value','')==n['connector']) if any(c.get('value','').startswith(n['connector']+' ') or c.get('value','')==n['connector'] for c in comps) else None
 if cc is None:
  order=nodes.index(n);cc=next(c for c in comps if c['ref']=='J'+str(order+4))
 mount=ff['chest']@np.linalg.inv(fbase['chest'])@C;x,y=cc['pcb'];pts.append((mount@np.array([x-75,y-75,14,1]))[:3])
 return np.array(pts),chain,mm,cc

cases={'A':preset}
for name in ['left_elbow','asymmetric','right_forearm']:cases[name]=g.read(B/'ue'/f'{name}.payload.json')['joint_angles_deg']
# Independent axis samples bound endpoint separation. They do not assert joint combinations are clear.
for rid in a.profile['raw_order']:
 lo,hi=a.profile['raw_limits_deg'][rid]
 for value in np.linspace(lo,hi,5):cases[rid+'='+str(value)]=dict(preset,**{rid:float(value)})
rows=[]
for n in nodes:
 points,chain,mm,cc=route(n,preset);lens=[]
 for name,q in cases.items():
  pointsq,_,_,_=route(n,q);lens.append((float(np.linalg.norm(np.diff(pointsq,axis=0),axis=1).sum()),name))
 nominal=float(np.linalg.norm(np.diff(points,axis=0),axis=1).sum());mx,witness=max(lens)
 # 8mm nominal bend radius, loose 180-degree U at each crossed moving body.
 crossings=max(1,len(chain)-1);slack=crossings*math.pi*8+25
 length=int(math.ceil((mx+slack)/25)*25)
 rows.append({**n,'carrier_reference':cc['ref'],'sensor_owner':mm['body'],'anchor_chain':chain,'A_centerline_mm':points.tolist(),'A_polyline_length_mm':nominal,'sampled_max_polyline_length_mm':mx,'max_witness':witness,'loop_radius_nominal_mm':8,'minimum_assembly_bend_radius_mm':7,'moving_loop_allowance_mm':crossings*math.pi*8,'termination_and_service_allowance_mm':25,'proposed_cut_each_wire_mm':length,'cut_length_released':False,'within_600mm_power_envelope':length<=600,'note':'Polyline is a routing guide. Round corners on 14mm mandrel; reserve U loops at moving transitions. First article must demonstrate no pull/pinch through usable range.'})
# Long calculated routes cannot be hidden by clipping to the voltage model.
maxlen=max(r['proposed_cut_each_wire_mm'] for r in rows)
report={'schema':'POSEDOLL-O22-HARNESS/1','status':'ENGINEERING_LAYOUT_PHYSICAL_FITTING_REQUIRED','wire':'5 separate AWG30 flexible stranded copper, insulation OD 0.4..0.7mm, conductor resistance <=0.4ohm/m at test temperature','pin_order':['GND black','SENSOR_3V45 red','CLK blue','DO green','CSN yellow'],'all_independent_home_runs':True,'daisy_chain':False,'anchors':anchors,'rows':rows,'sampled_poses':len(cases),'continuous_collision_or_fatigue_proof':False,'physical_test':False,'active_total_each_color_m':sum(r['proposed_cut_each_wire_mm'] for r in rows)/1000,'maximum_proposed_length_mm':maxlen,'representative_left_arm':[r['raw_id'] for r in rows if r['raw_id'].startswith(('clavicle_l','upperarm_l','elbow_l','forearm_l','hand_l'))]}
b.put(D/'routing_plan.json',report);print('HARNESS',len(rows),'MAX',maxlen,'M EACH COLOR',report['active_total_each_color_m']);print('OVER600',[(r['raw_id'],r['proposed_cut_each_wire_mm']) for r in rows if not r['within_600mm_power_envelope']])
