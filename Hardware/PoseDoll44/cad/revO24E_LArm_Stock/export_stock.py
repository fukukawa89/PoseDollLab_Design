from build_stock import *
import io,shutil
LABELS={'RP_keeper':'肩俯仰防脱压盖','RU_keeper':'上臂旋转防脱压盖','RF_keeper':'前臂旋转防脱压盖','ROOT':'固定输入握持座','SHOULDER_PITCH':'肩俯仰转子 / 外展固定叉','SHOULDER_ABDUCT':'肩外展转动叉 / 上臂旋转座','UPPER_ARM':'上臂转子 / 肘固定叉','ELBOW_OUTPUT':'肘转动叉 / 前臂旋转座','FOREARM':'前臂转子 / 腕固定叉','KEEP_E-P017':'手掌（锁母与垫片让位修正）','KEEP_E-P018':'双轴腕输出叉（原 E-P018）','KEEP_E-P019':'双轴腕中心件（原 E-P019）'}

def orientation(v):
 candidates=[]
 for ax,an in [([1,0,0],0),([1,0,0],90),([1,0,0],-90),([0,1,0],90),([0,1,0],-90),([1,0,0],180)]:
  R=rot(ax,an);vv=v@R[:3,:3].T;size=np.ptp(vv,axis=0);candidates.append((size[2]+100*max(0,max(size[:2])-162),R))
 _,R=min(candidates,key=lambda x:x[0]);R[:3,3]=-(v@R[:3,:3].T).min(0);return R

def run():
 a=load(OUT/'production_assembly.json');kit=load(OUT/'kit.json');z=np.load(OUT/'production_meshes.npz');zz={};reports=[];scene=trimesh.Scene();bs=[];mass=0
 inv={p['part_number']:p for p in kit['structural_parts']+kit['hardware']};old={p['part_number']:p for p in load(SRC/'kit.json')['structural_parts']}
 for p in a['parts']:
  i=str(p['i']);v=np.array(z[i+'v'],copy=True);f=np.array(z[i+'f'],copy=True);m=trimesh.Trimesh(v,f,process=False);r=inv[p['part_number']]
  if p['role']=='structure':
   before=m.volume;reused=p['source'] in ['E-P018','E-P019'];rel=f'stl_print/{p["part_number"]}.stl'
   if reused:
    o=old[p['source']];shutil.copyfile(SRC/o['stl'],OUT/rel);R=np.array(o['print_matrix']);pm=trimesh.load(OUT/rel,process=True)
   else:
    s=md.Manifold(md.Mesh64(v,np.array(f,dtype=np.uint64)));R=orientation(v)
    for tol in [.005,.01,.02,.03]:
     vv,ff=e.base.a.mesh_data(s.as_original().simplify(tol));pm=trimesh.Trimesh(vv,ff,process=False);pm.apply_transform(R)
     blob=pm.export(file_type='stl');pm=trimesh.load(io.BytesIO(blob),file_type='stl',process=True)
     if not pm.is_watertight:
      mesh=md.Mesh64(np.array(pm.vertices,dtype=np.float64,copy=True),np.array(pm.faces,dtype=np.uint64,copy=True),tolerance=.0001);mesh.merge();fixed=md.Manifold(mesh)
      if str(fixed.status())=='Error.NoError':
       vv,ff=e.base.a.mesh_data(fixed.simplify(.001));candidate=trimesh.Trimesh(vv,ff,process=True);blob=candidate.export(file_type='stl');pm=trimesh.load(io.BytesIO(blob),file_type='stl',process=True)
     if pm.is_watertight:break
    assert pm.is_watertight,p['name'];(OUT/rel).write_bytes(blob)
   assert pm.is_watertight and pm.volume>0,p['name']
   m=pm.copy();m.apply_transform(np.linalg.inv(R));ss=md.Manifold(md.Mesh64(np.array(m.vertices,copy=True),np.array(m.faces,dtype=np.uint64,copy=True)))
   comps=sum(x.volume()>.01 for x in ss.decompose());assert comps==1,(p['name'],comps)
   m.export(OUT/'parts_assembly'/f'{p["part_number"]}.stl')
   r.update(stl=rel,assembly_stl=f'parts_assembly/{p["part_number"]}.stl',sha256=sha(OUT/rel),kit_label=LABELS[p['name']],print_matrix=R.tolist(),print_bounds_mm=pm.bounds.tolist(),material='PLA',process='A1 mini / 0.4 mm / 0.12 mm / 5 walls / 100% infill',reuse_unchanged_stl=reused)
   reports.append(dict(part_number=p['part_number'],watertight=True,components=comps,stl_sha256=r['sha256'],volume_delta_mm3=m.volume-before,byte_identical_source_stl=p['source'] if reused else None))
  v=np.asarray(m.vertices);f=np.asarray(m.faces);zz[i+'v']=v;zz[i+'f']=f
  p.update(bounds_mm=m.bounds.tolist(),volume_mm3=float(m.volume),mass_centroid_mm=m.center_mass.tolist(),label=LABELS.get(p['name'],r['spec']))
  den=.00124 if p['role']=='structure' else .00785;mass+=m.volume*den
  w=m.copy();w.apply_transform(FA[p['frame']]);bs.append(w.bounds)
  mm=m.copy();mm.apply_scale(.001);mm.visual.vertex_colors=np.array([*e.COLORS.get(p['role'],[.6,.6,.6]),1])*255;mat=FA[p['frame']].copy();mat[:3,3]*=.001;scene.add_geometry(mm,node_name=p['part_number'],transform=mat)
 np.savez_compressed(OUT/'production_meshes.npz',**zz);put(OUT/'production_assembly.json',a)
 kit.update(revision='O24E_LArm_Stock',physical_dof=7,root_fixed_frame=ROOT,source_production_sha256=sha(SRC/'production_meshes.npz'),inventory_on_hand='UNKNOWN',custom_metal_count=0,cut_hardware_count=0)
 put(OUT/'kit.json',kit);scene.export(OUT/'O24E_left_arm_stock.glb');bs=np.array(bs);bb=[bs[:,0].min(0).tolist(),bs[:,1].max(0).tolist()]
 put(OUT/'envelope.json',dict(bounds_mm=bb,size_mm=np.ptp(bb,axis=0).tolist(),height_mm=float(bb[1][2]-bb[0][2]),estimated_mass_g=float(mass),scope='Single arm A pose only; not a new full-body height measurement. PLA 1.24 g/cm3 and steel 7.85 g/cm3; nominal mesh mass.'))
 put(OUT/'verification/stl_export.json',dict(status='PASS_EXPORT',geometry_sha256=sha(OUT/'production_meshes.npz'),rows=reports,production_geometry='Checks and viewer use the same final STL round-trip bodies.'))
 put(OUT/'source_fingerprints.json',{str(p.relative_to(H)):sha(p) for p in [SRC/'production_meshes.npz',SRC/'O24E_left_arm_mechanical.zip',H/'bench/revO24E/production_meshes.npz',T6/'assembly_meshes.npz',H/'bench/revO22/mechanical_procurement_O20.json']})
 print('EXPORTED',len(reports),'prints; mass',round(mass,2),'g',flush=True)
if __name__=='__main__':run()
