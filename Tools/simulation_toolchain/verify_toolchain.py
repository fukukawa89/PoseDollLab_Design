"""Verify an isolated FreeCAD -> Gmsh -> CalculiX -> FreeCAD workflow.
Only synthetic benchmarks are generated. No doll design is modified.
Run using the Python shipped with the installed FreeCAD.
"""
from pathlib import Path
import os,sys,json,subprocess,hashlib,re,datetime
import FreeCAD as App
import Part,Fem,numpy as np,scipy
BIN=Path('D:/ProgramFiles/FreeCAD/bin');ROOT=Path(__file__).resolve().parent
sys.path.append(str(BIN.parent/'Mod/Fem'))
from feminout import importCcxFrdResults as frd
import ObjectsFem
import datetime as benchmark_clock
stamp=benchmark_clock.datetime.now(benchmark_clock.timezone.utc).astimezone(benchmark_clock.timezone(benchmark_clock.timedelta(hours=8))).strftime('%Y-%m-%d_%H%M%S')
OUT=ROOT/'runs'/stamp;OUT.mkdir(parents=True)
ENV=dict(os.environ);ENV.update(OMP_NUM_THREADS='2',CCX_NPROC_RESULTS='2',CCX_NPROC_EQUATION_SOLVER='2')
BASE=ROOT.parents[1]/'Hardware/PoseDoll44/bench/revO22';reference_paths=[BASE/'O22F2_Release/manifest.json',BASE/'a1mini_fins_v2/parts/X046.npz',BASE/'a1mini_fins_v2/design/X046.json']+list((BASE/'O22F2_Release/projects').glob('*.3mf'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):sha(p) for p in reference_paths}
def write(path,s):path.write_text(s,encoding='utf8')
def command(args,name):
 p=subprocess.run([str(x) for x in args],cwd=OUT,env=ENV,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 text=p.stdout.decode('utf8',errors='replace');write(OUT/(name+'.log'),text)
 if p.returncode or re.search(r'(?m)\*ERROR|^Error\s*:',text):raise RuntimeError(name+' failed: '+text[-2000:])
 return text

def nset(name,ids):
 ids=[str(int(i)) for i in ids];return '*NSET,NSET='+name+'\n'+'\n'.join(','.join(ids[i:i+12]) for i in range(0,len(ids),12))+'\n'
def parse_inp(path):
 nodes={};elements={};mode=None;current=[]
 for line in path.read_text().splitlines():
  line=line.strip()
  if not line or line.startswith('**'):continue
  if line.startswith('*'):
   mode='nodes' if line.upper().startswith('*NODE') and not line.upper().startswith('*NODE ') else 'tets' if line.upper().startswith('*ELEMENT') and 'C3D10' in line.upper() else None;continue
  if mode=='nodes':
   a=line.split(',');nodes[int(a[0])]=np.array(list(map(float,a[1:4])))
  elif mode=='tets':
   current.extend(int(x) for x in line.split(',') if x.strip())
   if len(current)==11:elements[current[0]]=current[1:];current=[]
 assert nodes and elements and not current
 return nodes,elements

def mesh(size,name):
 geo=f'''Merge "beam.step";
Physical Volume("SOLID") = Volume{{:}};
Mesh.MeshSizeMin = {size};
Mesh.MeshSizeMax = {size};
Mesh.ElementOrder = 2;
Mesh.SaveGroupsOfNodes = 1;
Mesh.MshFileVersion = 2.2;
'''
 write(OUT/(name+'.geo'),geo)
 command([BIN/'gmsh.exe',name+'.geo','-3','-order','2','-format','inp','-o',name+'.inp','-nt','2','-v','3'],name+'_gmsh')
 nodes,tets=parse_inp(OUT/(name+'.inp'))
 text='*NODE,NSET=NALL\n'+''.join(f'{i},{x[0]:.12g},{x[1]:.12g},{x[2]:.12g}\n' for i,x in nodes.items())+'*ELEMENT,TYPE=C3D10,ELSET=SOLID\n'+''.join(str(i)+','+','.join(map(str,e))+'\n' for i,e in tets.items())
 left=[i for i,x in nodes.items() if abs(x[0])<1e-7];right=[i for i,x in nodes.items() if abs(x[0]-100)<1e-7]
 text+=nset('LEFT',left)+nset('RIGHT',right)
 # Consistent uniform end-face traction on 6-node triangles: corner forces 0,
 # midside forces equal to surface area / 3. CalculiX C3D10 connectivity.
 faces=[(0,1,2,4,5,6),(0,3,1,7,8,4),(1,3,2,8,9,5),(2,3,0,9,7,6)]
 weights={};area=0
 for tet in tets.values():
  for face in faces:
   ids=[tet[k] for k in face];xyz=np.array([nodes[k] for k in ids])
   if not np.all(np.abs(xyz[:,0]-100)<1e-7):continue
   a=np.linalg.norm(np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0]))/2;area+=a
   for i in ids[3:]:weights[i]=weights.get(i,0)+a/3
 assert abs(area-100)<1e-5 and abs(sum(weights.values())-100)<1e-5
 print('MESH',name,len(nodes),len(tets),'area',area,flush=True)
 return {'name':name,'mesh_size_mm':size,'nodes':nodes,'tets':tets,'left':left,'right':right,'text':text,'weights':weights}

def solve(m,name,case):
 inp=m['text']+'*MATERIAL,NAME=TEST\n*ELASTIC\n200000.,'+('0.0\n' if case=='axial' else '0.3\n')+'*CONDUCTIVITY\n1.0\n*SOLID SECTION,ELSET=SOLID,MATERIAL=TEST\n'
 if case=='thermal':inp+='*INITIAL CONDITIONS,TYPE=TEMPERATURE\nNALL,293.15\n*STEP\n*HEAT TRANSFER,STEADY STATE\n1.,1.\n*BOUNDARY\nLEFT,11,11,293.15\nRIGHT,11,11,393.15\n*NODE FILE\nNT\n*EL FILE\nHFL\n*NODE PRINT,NSET=NALL\nNT\n*END STEP\n'
 else:
  inp+='*STEP\n*STATIC\n*BOUNDARY\nLEFT,1,3,0.\n'
  if case=='axial':inp+='RIGHT,1,1,0.01\n'
  else:inp+='*CLOAD\n'+''.join(f'{i},3,{-w/100:.14g}\n' for i,w in m['weights'].items())
  inp+='*NODE FILE\nU,RF\n*EL FILE\nS,E\n*NODE PRINT,NSET=LEFT,TOTALS=YES\nRF\n*NODE PRINT,NSET=RIGHT\nU\n*END STEP\n'
 write(OUT/(name+'.inp'),inp);log=command([BIN/'ccx.exe','-i',name],name+'_ccx');assert 'Job finished' in log
 parsed=frd.read_frd_result(str(OUT/(name+'.frd')))
 print('SOLVED',name,[(list(s.keys())) for s in parsed['Results']],flush=True)
 return parsed

def values(result,key):
 rs=[r for r in result['Results'] if key in r];assert rs,(key,[list(r) for r in result['Results']]);return rs[-1][key]

report={'scope':'toolchain verification only; synthetic material and loads; no doll analysis or edits','local_date_zone':'Asia/Hong_Kong','run':str(OUT),'FreeCAD':App.Version(),'Python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__,'binaries':{n:{'path':str(BIN/n),'sha256':sha(BIN/n)} for n in ['python.exe','freecadcmd.exe','gmsh.exe','ccx.exe']}}
try:
 doc=App.newDocument('Toolchain_Cantilever');obj=doc.addObject('PartDesign::Feature','BenchmarkBeam');obj.Shape=Part.makeBox(100,10,10);doc.recompute();assert obj.Shape.isValid() and abs(obj.Shape.Volume-10000)<1e-8;obj.Shape.exportStep(str(OUT/'beam.step'));doc.saveAs(str(OUT/'BenchmarkGeometry.FCStd'));App.closeDocument(doc.Name)
 coarse=mesh(4,'beam_coarse');fine=mesh(2.5,'beam_fine')
 cases={};cases['axial']=solve(coarse,'axial_patch','axial');cases['bending_coarse']=solve(coarse,'bending_coarse','bending');cases['bending_fine']=solve(fine,'bending_fine','bending');cases['thermal']=solve(coarse,'steady_heat','thermal')
 # Keep a compact parse diagnostic before assessing the numerical results.
 write(OUT/'result_keys.json',json.dumps({k:[{j:type(v).__name__ for j,v in s.items()} for s in d['Results']] for k,d in cases.items()},indent=2))
 d=values(cases['axial'],'disp');err=max(abs(d[i].x-coarse['nodes'][i][0]*.0001) for i in d);assert err<1e-6,err
 bending=[]
 for name,m in [('bending_coarse',coarse),('bending_fine',fine)]:
  d=values(cases[name],'disp');u=-sum(d[i].z*w for i,w in m['weights'].items())/100;ref=1*100**3/(3*200000*(10*10**3/12));shear=1*100/((5/6)*(200000/(2*1.3))*100)
  bending.append({'case':name,'nodes':len(m['nodes']),'tetra10_elements':len(m['tets']),'tip_deflection_mm':u,'euler_bernoulli_mm':ref,'timoshenko_mm':ref+shear,'relative_error_vs_timoshenko':abs(u/(ref+shear)-1)})
 assert all(x['relative_error_vs_timoshenko']<.04 for x in bending),bending
 convergence=abs(bending[0]['tip_deflection_mm']/bending[1]['tip_deflection_mm']-1);assert convergence<.02,convergence
 th=values(cases['thermal'],'temp');terr=max(abs(float(t)-(293.15+coarse['nodes'][i][0])) for i,t in th.items());assert terr<.01,terr
 report['checks']={'cad_validity_and_volume':True,'axial_linear_displacement_max_error_mm':err,'bending':bending,'bending_mesh_change_fraction':convergence,'steady_temperature_max_error_K':terr,'all_benchmarks_passed':True}
 # Import actual solver results into a separate native FreeCAD project.
 doc=App.newDocument('ToolchainVerified');analysis=ObjectsFem.makeAnalysis(doc,'BenchmarkAnalysis');frd.importFrd(str(OUT/'bending_fine.frd'),analysis=analysis,result_name_prefix='VerifiedCantilever_');doc.recompute();assert any(o.TypeId=='Fem::FemResultObjectPython' for o in doc.Objects);doc.saveAs(str(OUT/'VerifiedCantilever.FCStd'));report['freecad_result_import']=True;App.closeDocument(doc.Name)
 doc=App.openDocument(str(OUT/'VerifiedCantilever.FCStd'));objects=[{'name':o.Name,'nodes':len(o.NodeNumbers),'displacements':len(o.DisplacementVectors),'stresses':len(o.vonMises)} for o in doc.Objects if o.TypeId=='Fem::FemResultObjectPython'];assert objects and all(o['displacements']>6000 and o['stresses']>6000 for o in objects);report['saved_FreeCAD_document_reopened']=objects;App.closeDocument(doc.Name)
except Exception as e:
 report['error']=repr(e);write(OUT/'verification.json',json.dumps(report,ensure_ascii=False,indent=2));raise
finally:
 report['doll_reference_hashes_unchanged']={p:sha(Path(p))==h for p,h in before.items()};assert all(report['doll_reference_hashes_unchanged'].values());write(OUT/'verification.json',json.dumps(report,ensure_ascii=False,indent=2));write(ROOT/'latest_run.txt',str(OUT)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
