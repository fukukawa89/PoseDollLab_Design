"""DC resistor-network audit of routed copper; no thermal/EMI claim."""
from pathlib import Path
import json,numpy as np,math
R=Path(__file__).resolve().parents[1];B=R/'Hardware/PoseDoll44/bench/revO22';D=B/'electronics/carrier'
data=json.loads((D/'copper_graph_input.json').read_text());planes=json.loads((D/'plane_resistor_network.json').read_text());rho=.0175*(1+.00393*40);thickness=.035

def net_solve(net,source,loads):
 ts=[t for t in data['tracks'] if t['net']==net];pads=[p for p in data['pads'] if p['net']==net];nodes=[];index={}
 def node(xy,layer):
  key=tuple(round(v,6) for v in xy)+(layer,)
  if key not in index:index[key]=len(nodes);nodes.append(key)
  return index[key]
 for t in ts:
  for l in ([0,2] if t['via'] else [t['layer']]):node(t['a'],l);node(t['b'],l)
 pnodes={}
 for p in pads:pnodes[(p['ref'],p['pin'])]=node(p['xy'],p['layers'][0])
 edges=[]
 for t in ts:
  if t['via']:edges.append((node(t['a'],0),node(t['a'],2),.0011));continue
  a=np.array(t['a']);z=np.array(t['b']);v=z-a;vv=v@v
  if vv<1e-16:continue
  on=[]
  for i,n in enumerate(nodes):
   if n[2]!=t['layer']:continue
   w=np.array(n[:2])-a;u=(w@v)/vv
   if -.00001<=u<=1.00001 and np.linalg.norm(w-u*v)<.0002:on.append((u,i))
  on.sort()
  for (u,i),(v,j) in zip(on,on[1:]):
   length=(v-u)*math.sqrt(vv)
   if length>1e-6:edges.append((i,j,rho*length/(1000*t['width']*thickness)))
 # Every pad shorts its contact area. A 10 micro-ohm edge keeps system finite.
 for p in pads:
  root=pnodes[(p['ref'],p['pin'])];x0,y0,x1,y1=p['bounds']
  for i,n in enumerate(nodes):
   if i!=root and n[2] in p['layers'] and x0-1e-6<=n[0]<=x1+1e-6 and y0-1e-6<=n[1]<=y1+1e-6:edges.append((root,i,.00001))
 # Add an embedded sub-network of real internal copper strips. Remaining copper is ignored.
 if net in planes:
  plane=planes[net];layer=plane['layer'];pidx=[node(xy,layer) for xy in plane['nodes']]
  for i,j,length,width in plane['edges']:edges.append((pidx[i],pidx[j],rho*length/(1000*width*plane['inner_copper_mm'])))
  for join in plane['joins']:
   external=node(join['xy'],0);internal=node(join['xy'],layer)
   edges.append((external,internal,.0011))
   edges.append((internal,pidx[join['node']],rho*max(join['length_mm'],.01)/(1000*join['width_mm']*plane['inner_copper_mm'])))
 sourceidx=pnodes[source];adj={i:set() for i in range(len(nodes))}
 for i,j,r in edges:adj[i].add(j);adj[j].add(i)
 reached={sourceidx};todo=[sourceidx]
 while todo:
  for j in adj[todo.pop()]:
   if j not in reached:reached.add(j);todo.append(j)
 assert all(pnodes[k] in reached for k in loads),('disconnected graph',net,[k for k in loads if pnodes[k] not in reached])
 active=sorted(reached-{sourceidx});indices={k:i for i,k in enumerate(active)};I=np.zeros(len(active));diag=np.zeros(len(active));ei=[];ej=[];conduct=[]
 for i,j,r in edges:
  if i not in reached:continue
  g=1/r
  if i!=sourceidx:diag[indices[i]]+=g
  if j!=sourceidx:diag[indices[j]]+=g
  if i!=sourceidx and j!=sourceidx:ei.append(indices[i]);ej.append(indices[j]);conduct.append(g)
 ei=np.array(ei);ej=np.array(ej);conduct=np.array(conduct)
 for key,current in loads.items():
  idx=pnodes[key]
  if idx!=sourceidx:I[indices[idx]]+=current
 def mul(x):return diag*x-np.bincount(ei,conduct*x[ej],minlength=len(active))-np.bincount(ej,conduct*x[ei],minlength=len(active))
 V=np.zeros(len(active));r=I.copy();z=r/diag;direction=z.copy();rz=r@z
 for iteration in range(20000):
  action=mul(direction);alpha=rz/(direction@action);V+=alpha*direction;r-=alpha*action
  if np.max(np.abs(r))<1e-10:break
  z=r/diag;next_rz=r@z;direction=z+(next_rz/rz)*direction;rz=next_rz
 else:raise RuntimeError('DC network convergence failed')
 get=lambda idx:0 if idx==sourceidx else float(V[indices[idx]])
 return {ref+':'+pin:get(idx) for (ref,pin),idx in pnodes.items() if idx in reached}
ports=[p['ref'] for p in data['pads'] if p['net']=='/SENSOR_3V45' and p['pin']=='2' and p['ref'].startswith('J')];assert len(ports)==46
rail={(ref,'2'):.014 for ref in ports};logic={'U1':'20','U2':'20','U3':'24','U4':'24','U5':'24'};rail.update({(r,p):.016 for r,p in logic.items()});total=sum(rail.values())
ground={(r,'1'):.014 for r in ports};ground.update({(r,'10' if r in ['U1','U2'] else '12'):.016 for r in logic})
pos=net_solve('/SENSOR_3V45',('F5','2'),rail);neg=net_solve('/GND',('U7','2'),ground);reg=net_solve('/REG_3V45',('L1','2'),{('F5','1'):total})
vmin=.588*(1+316000*.998/(66500*1.002));vmax=.612*(1+316000*1.002/(66500*.998));fuse_r=.15
# AWG30 purchase acceptance at 60C: <=0.4ohm/m/conductor; longest branch 0.75m.
wire_drop=.014*(2*.75*.4+2*.05);rows=[]
for r in ports:
 copper=pos[r+':2']+neg[r+':1']+reg['F5:1'];remote=vmin-total*fuse_r-copper-wire_drop
 rows.append({'port':r,'pcb_drop_v':copper,'remote_min_v_at_750mm':remote})
report={'schema':'POSEDOLL-O22-POWER/1','status':'DC_BUDGET_PASS' if min(x['remote_min_v_at_750mm'] for x in rows)>=3.10 and vmax<=3.6 else 'FAIL',
 'not_a_physical_test':True,'copper_um':35,'copper_temperature_C':60,'feedback_resistor_tolerance':.001,'feedback_resistor_TCR_ppm_K':25,'feedback_temperature_excursion_K':40,'sensor_current_A_each':.014,'logic_allowance_A':.080,'total_A':total,
 'regulator_tolerance_included_V':[vmin,vmax],'fuse_hot_resistance_acceptance_ohm':fuse_r,'fuse_is_not_guaranteed_by_nominal_datasheet':True,
 'branch_cable_max_m':.75,'wire_loop_plus_contact_drop_V':wire_drop,'input_nominal_V':5,'minimum_required_input_at_U7_V':4.05,
 'ports':rows,'individual_maxima':{'positive':max(pos.values()),'negative':max(neg.values()),'pre_fuse':reg['F5:1']},'remote_min_V':min(x['remote_min_v_at_750mm'] for x in rows),'analytical_guard_above_sensor_3V_V':min(x['remote_min_v_at_750mm'] for x in rows)-3,
 'requires_physical':['Measure far VDD at 46x14mA +80mA full load','Oscilloscope far VDD ripple and SSI setup/hold','Output-fuse hot resistance <=0.15ohm','Regulator and connector temperature rise'],
 'plane_model':'Only embedded 0.7mm orthogonal strips on 1mm grid are counted; clearance-cut copper and unused copper ignored; inner copper 17.5um' }
(B/'verification/power_budget.json').write_text(json.dumps(report,indent=2));print(report['status'],report['remote_min_V'],report['regulator_tolerance_included_V'])
