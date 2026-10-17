"""Remove a small unsupported tip until its section joins the printable body envelope.
Candidate only: bounded subtraction, hardware protection, independent native/fit checks.
"""
from pathlib import Path
import sys,json,numpy as np,shapely,concurrent.futures,traceback
from shapely.geometry import box as rect
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from build_revo22_fins import solid,vf,union,box,md
from o22_reference_mesh import reference_solid
from o22_cross_section_geometry import polygon
from o22_material_components import material_components
from o22_f3_gcode import extract_paths
from repair_revo22_f4_guarded_chamfer import context
from inspect_revo22_f4_nut_contacts import core_guards
from slice_revo22_f4_candidate import run
from verify_revo22_f4_full_bead import check
from refine_revo22_f4_full_bead import refine
from verify_revo22_f4_body_change import check as fit
from verify_revo22_f4_repaired_geometry import check as geom
O=R/'Hardware/PoseDoll44/bench/revO22/a1mini_fins_v4'
def cs(poly):
 polys=list(poly.geoms) if poly.geom_type=='MultiPolygon' else [poly] if poly.geom_type=='Polygon' else []
 paths=[]
 for p in polys:
  p=shapely.orient_polygons(p);paths.append(np.array(p.exterior.coords)[:-1]);paths.extend(np.array(h.coords)[:-1]for h in p.interiors)
 return md.CrossSection(paths)
def trial(pid,parent,label):
 src=O/'candidates'/pid/parent;dst=O/'candidates'/pid/label
 for sub in ['parts','design','verification']:(dst/sub).mkdir(parents=True,exist_ok=True)
 n=dict(np.load(src/'parts'/f'{pid}.npz'));d=json.loads((src/'design'/f'{pid}.json').read_text());aud=refine(pid,parent);it=json.loads((src/'verification/plate_manifest.json').read_text())['items'][0];M=np.array(it['rotation_matrix']);off=np.array(it['translation_mm']);body=solid(n['v'],n['f']);original=reference_solid(n,d);parts,key,T=context(d,pid)
 import repair_revo22_f4_guarded_chamfer as ctx
 proj=src/'projects'/json.loads((src/'verification/local_extrusion.json').read_text())['project'];_,raw=extract_paths(proj);a=np.asarray(raw).reshape(-1,9);a=a[a[:,7]==0];zs=np.unique(a[:,5]);rows=[]
 for issue in aud['external_islands']:
  b=issue['bounds_mm'];z=issue['z_mm'];prevz=zs[zs<z-.01][-1];ar=a[abs(a[:,5]-prevz)<.002];xy=(np.stack([ar[:,:2],ar[:,3:5]],axis=1)-off[:2])@M[:2,:2];back=shapely.union_all(shapely.buffer(shapely.linestrings(xy),ar[:,8]/2,quad_segs=6));pts=(np.array([[x,y,z-.1]for x in[b[0],b[2]]for y in[b[1],b[3]]])-off)@M;lo=pts.min(0);hi=pts.max(0);roi=rect(lo[0]-2.5,lo[1]-2.5,hi[0]+2.5,hi[1]+2.5);z0=float(prevz-.1);dz=.1;allowed=back.buffer(-.03).buffer(.03);pieces=[];quiet=0
  for j in range(1,81):
   zz=z0+j*dz;sect=polygon(body.slice(zz+dz*.5));allowed=allowed.buffer(.6*dz,quad_segs=6);kept=sect.intersection(allowed);missing=sect.difference(allowed).intersection(roi)
   if missing.area>1e-6:pieces.append(cs(missing).extrude(dz+.00002).translate([0,0,zz-.00001]));quiet=0
   else:quiet+=1
   # Unaffected material outside the local neighborhood stays available as a parent.
   allowed=kept.union(sect.difference(roi))
   if quiet>=6 and j>8:break
  cut=union(pieces);delta=body^cut
  if delta.volume()<1e-6:continue
  wa=delta.transform(np.linalg.inv(T)[:3,:]);guards=[];hardware=[]
  for k,s in parts.items():
   if k==key or wa.min_gap(s,.35)>.34:continue
   sku=ctx.CACHE[1][k].get('sku')or''
   # All existing hardware contact envelopes are preserved, including washers.
   guard=union([s.translate([x,y,z])for x in[-.08,0,.08]for y in[-.08,0,.08]for z in[-.08,0,.08]])
   guards.append(guard.transform(T[:3,:]));hardware.append(k)
  cut=cut-union(guards);delta=body^cut;proposal=body-cut;vol=float(delta.volume())
  if vol>8 or float((original-proposal).volume())>min(60.,original.volume()*.008)or len(material_components(proposal))!=len(material_components(body)):
   print('ENVELOPE80_REJECT',pid,z,vol,'components',len(material_components(proposal)),flush=True);continue
  if (proposal-original).volume()>1e-6:print('ENVELOPE80_IDENTITY_REJECT',pid,z,flush=True);continue
  body=proposal;row={'native_issue':issue,'local_bounds_mm':list(cut.bounding_box()),'removed_volume_mm3':vol,'printable_slope_xy_per_z':.6,'slice_step_mm':dz,'protected_hardware':hardware,'method':'Track the actual previous bead footprint through successive original body sections; remove only the disconnected local tip until it joins the printable envelope.'};rows.append(row);print('ENVELOPE80_CUT',pid,z,vol,flush=True)
 delta=original-body;fin=solid(n['fin_v'],n['fin_f']);teeth=solid(n['teeth_v'],n['teeth_f']);teeth=union([c for c in material_components(teeth)if(c^body).volume()>.005 and(c^fin).volume()>.005]);fin=union([c for c in material_components(fin)if(c^teeth).volume()>.005]);n['source_f']=n.get('source_f',n['f']);n['v'],n['f']=vf(body);n['removed_body_v'],n['removed_body_f']=vf(delta);n['fin_v'],n['fin_f']=vf(fin);n['teeth_v'],n['teeth_f']=vf(teeth);bc=d.get('body_change',{});bc.update(kind='bounded_print_envelope_tip_relief',removed_volume_mm3=float(delta.volume()),added_volume_mm3=0.,chamfers=bc.get('chamfers',[])+rows,source_body_volume_mm3=float(original.volume()),assembly_contact_validation_pending=True);d.update(body_change=bc,source_mesh_preserved=False);np.savez_compressed(dst/'parts'/f'{pid}.npz',**n);(dst/'design'/f'{pid}.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
 if not rows:return {'id':pid,'added_cuts':0}
 run(pid,label);check(pid,label);q=refine(pid,label)
 if q['native_review_resolved']:fit(pid,label);geom(pid,label)
 return {k:q[k]for k in['id','label','external_island_count','critical_external_count','native_review_resolved']}
def one(spec):
 try:return trial(*spec.split(':'))
 except Exception:return {'spec':spec,'error':traceback.format_exc()}
if __name__=='__main__':
 out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as pool:
  for f in concurrent.futures.as_completed([pool.submit(one,s)for s in sys.argv[1:]]):
   out.append(f.result());print('ENVELOPE80_RESULT',out[-1],flush=True);(O/'envelope80_progress.json').write_text(json.dumps(out,indent=2))
