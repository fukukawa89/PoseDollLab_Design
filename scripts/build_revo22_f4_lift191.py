"""Lift the unmodified part 2 mm to admit a broad bed root below the existing through-hole."""
from pathlib import Path
import sys,json,numpy as np,copy,shutil
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,vf,union,md,box
from verify_revo22_f4_body_change import check as fit
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def lift(pid,parent,label):
 src=O/'candidates'/pid/parent;dst=O/'candidates'/pid/label
 for sub in ['parts','design','verification']:(dst/sub).mkdir(parents=True,exist_ok=True)
 n=dict(np.load(src/'parts'/f'{pid}.npz'));d=json.loads((src/'design'/f'{pid}.json').read_text());h=2.;body=solid(n['v'],n['f']);oldfin=solid(n['fin_v'],n['fin_f']);oldteeth=solid(n['teeth_v'],n['teeth_f']);foot=oldfin.slice(.1).extrude(h+.001);fin=oldfin.translate([0,0,h])+foot;teeth=oldteeth.translate([0,0,h]);s=body.translate([0,0,h]);cs=md.CrossSection.batch_boolean([body.slice(z)for z in[.1,.2,.3]],md.OpType.Add);tabs=[]
 for island in cs.decompose():
  b=island.bounds();c=np.array([(b[0]+b[2])/2,(b[1]+b[3])/2]);w=max(4.,b[2]-b[0]+.8);t=max(4.,b[3]-b[1]+.8);pad=box([c[0]-w/2,c[1]-t/2,0],[c[0]+w/2,c[1]+t/2,1.6]);tt=island.extrude(.8).translate([0,0,1.5]);assert (pad^s).volume()<1e-6;assert(tt^s).volume()>.005;assert(tt^pad).volume()>.005;fin=fin+pad;teeth=teeth+tt;num=len(d['segments'])+1;d['segments'].append({'number':num,'bounds_mm':list(pad.bounding_box()),'height_mm':1.6,'blade_width_mm':w,'blade_thickness_mm':t,'brace_count':0,'teeth_count':1,'on_build_plate':True,'bed_connected_portal':True,'minimum_base_leg_width_mm':w,'minimum_fin_width_mm':min(w,t),'base_pedestal_for_lifted_part':True});d['teeth'].append({'bounds_mm':list(tt.bounding_box()),'part_bite_mm3':float((tt^s).volume()),'fin_root_mm3':float((tt^pad).volume()),'contact_point_mm':[*c,2.1],'fin_number':num,'base_lift_contact':True});tabs.append(num)
 for row in d['segments']:
  if row['number']in tabs:continue
  row['height_mm']+=h
  if 'bounds_mm'in row:row['bounds_mm'][2]=0.;row['bounds_mm'][5]+=h
 for row in d['teeth']:
  if row.get('base_lift_contact'):continue
  if'contact_point_mm'in row:row['contact_point_mm'][2]+=h
  if'bounds_mm'in row:row['bounds_mm'][2]+=h;row['bounds_mm'][5]+=h
 n['v']=n['v']+[0,0,h];n['fin_v'],n['fin_f']=vf(fin);n['teeth_v'],n['teeth_f']=vf(teeth);d['orientation']['source_translation_mm'][2]+=h;d['print_lift191']={'height_mm':h,'reason':'A low through-hole lacked room for a wide bed root. Raise the unchanged part and extend every previous fin root to the bed; add separate short base contacts.'};d.update(support_volume_mm3=float((fin+teeth).volume()),support_count=len(d['segments']));np.savez_compressed(dst/'parts'/f'{pid}.npz',**n);(dst/'design'/f'{pid}.json').write_text(json.dumps(d,indent=2));shutil.copy2(src/'verification/plate_manifest.json',dst/'verification/plate_manifest.json')
 ap=src/'verification/full_bead_contacts_v5.json';ap=ap if ap.exists()else src/'verification/full_bead_contacts_v2.json';q=json.loads(ap.read_text());q['construction_reference_only']=True
 for k in['external_islands','critical_external_runs']:
  for x in q[k]:x['z_mm']+=h
 (dst/'verification/full_bead_contacts_v5.json').write_text(json.dumps(q,indent=2))
 if'body_change'in d or'nominal_reference'in d:fit(pid,label)
 print('LIFT191_CREATED',pid,label,'base_tabs',len(tabs),flush=True)
if __name__=='__main__':lift(*sys.argv[1:])
