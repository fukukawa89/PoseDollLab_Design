"""Strict current-run completeness checks. A successful command is not an engineering gate."""
from revo2_evidence import *
ROLES={'G0','N1','N2','N3','N4','N5','N6'}
BOARDS={'proximal5','distal4','distal4_narrow'}
REPORTS={'joint','assembly','electronics','pcba_geometry','packaging','legacy_mass_reference','mass_properties_revO2','mechanics_analysis','firmware_builds','baseline','offline','browser','power_budget'}

def exact_set(records,key,expected):
 if not isinstance(records,list) or not all(isinstance(q,dict) and key in q for q in records):raise ValueError('Invalid record schema')
 values=[q[key] for q in records]
 if len(values)!=len(expected) or set(values)!=set(expected):raise ValueError('Missing/duplicate/unexpected records: '+repr(values))

def checked_report(path,rid,expected_hash=None):
 if not Path(path).is_file():raise ValueError('BLOCKED_MISSING_CURRENT_RUN_REPORT: '+str(path))
 if expected_hash is not None and sha(path)!=expected_hash:raise ValueError('FAIL_CHANGED_REPORT')
 data=read(path)
 if not isinstance(data,dict):raise ValueError('Invalid report object')
 if data.get('run_id')!=rid:raise ValueError('FAIL_WRONG_RUN_ID')
 return data

def assess(directory,rid,execution,hashes=None):
 issues=[];reports={}
 if hashes is not None and set(hashes)!=REPORTS:issues.append('Missing/extra producer-captured report hashes')
 for name in sorted(REPORTS):
  try:reports[name]=checked_report(directory/(name+'.json'),rid,(hashes or {}).get(name))
  except (ValueError,KeyError,OSError,TypeError) as e:issues.append(str(e))
 try:
  exact_set(reports['firmware_builds']['builds'],'role',ROLES)
  exact_set(reports['electronics']['boards'],'kind',BOARDS)
  exact_set(reports['pcba_geometry']['boards'],'kind',BOARDS)
  exact_set(reports['packaging']['characters'],'character',{'manny','quinn'})
  if set(reports['mass_properties_revO2']['characters'])!={'manny','quinn'}:raise ValueError('Missing mass character')
  j=reports['joint'];a=reports['assembly'];names=[q['part_id'] for q in j['parts']]
  if not j.get('single_connected_solid_per_part'):raise ValueError('Disconnected part geometry not accepted')
  if len(names)!=48 or len(set(names))!=48 or a['coverage']['missing'] or a['coverage']['installed_parts']!=48:raise ValueError('Incomplete joint parts/assembly coverage')
  if len(a['steps'])<35:raise ValueError('Incomplete assembly path records')
  for path,digest in reports['electronics'].get('library_input_sha256',{}).items():
   if not Path(path).is_file() or sha(path)!=digest:raise ValueError('Native KiCad input library changed')
  for c in reports['mass_properties_revO2']['characters'].values():
   if len(c['load_rows'])!=41:raise ValueError('Incomplete 41-axis load set')
   exact_set(c['load_rows'],'axis_id',set(read(HW/'mechanical_manifest/network_revO.json')['protocol_order'][3:]))
 except (KeyError,ValueError) as e:issues.append(str(e))
 bad=[k for k,v in execution.items() if v['status']!='PASS']
 if bad:issues.append('Failed or blocked producers: '+', '.join(bad))
 baseline=reports.get('baseline',{})
 if baseline.get('status')!='PASS':issues.append('Fallback/source preservation not verified')
 nominal=reports.get('joint',{}).get('nominal_solid_status')=='PASS_NOMINAL_GEOMETRY_ONLY' and reports.get('assembly',{}).get('status')=='PASS_SAMPLED_NOMINAL_ONLY'
 boardrows=reports.get('electronics',{}).get('boards',[])
 erc=bool(boardrows) and len(boardrows)==3 and all(x['checks']['erc']['status']=='PASS' for x in boardrows)
 drc=bool(boardrows) and len(boardrows)==3 and all(x['checks']['drc']['status']=='PASS' for x in boardrows)
 builds=reports.get('firmware_builds',{}).get('builds',[]);compile_pass=len(builds)==7 and all(x['status']=='PASS' and x.get('config_role_checked') for x in builds)
 return {'schema':'revo2-status-v1','run_id':rid,'evidence_issues':issues,'gates':{'V0':{'status':'PASS' if not issues else 'FAIL','scope':'Fresh outputs, expected sets, source fingerprints and raw producer results; not engineering acceptance'},'V1':{'status':'PARTIAL' if nominal else 'FAIL','nominal_CAD_and_sampled_paths':nominal,'blocking':['Integral drive-slot tolerance, wear and parasitic axial friction unqualified','Supplier tolerance and joint/cap/plate strength qualification pending','Mating plug/output coupler and full small-fastener tool access incomplete']},'V2':{'status':'BLOCKED','blocking':['Candidate placements still fail or have only sparse surface corner checks','Some native component models and exact mating datums missing','Complete chest mechanisms, shoulder wire sweep and service paths missing']},'V3':{'status':'BLOCKED_DEPENDENCY','requires':['V1','V2'],'physical_tests':'NOT_RUN'},'V4':{'status':'BLOCKED_DEPENDENCY','requires':['V2'],'new_candidate_schematics_ERC':'PASS' if erc else 'FAIL','PCB_DRC':'PASS' if drc else 'FAIL','seven_role_compile':'PASS' if compile_pass else 'FAIL','physical_power_and_8_14ms_soak':'NOT_RUN'},'V5':{'status':'BLOCKED_DEPENDENCY','requires':['V1','V2','V3','V4'],'full_body_and_UE':'NOT_RUN'}},'nominal_joint_CAD_delivered':nominal,'physical_tested':False,'manufacturing_released':False,'final_device_profile_delivered':False,'fallback_91cm_preserved':baseline.get('status')=='PASS','mass_budget_g':{k:v['total_budget_g'] for k,v in reports.get('mass_properties_revO2',{}).get('characters',{}).items()},'source_contract':str((HW/'docs/revO2_review_source/iteration2_contract.json').relative_to(REPO))}
if __name__=='__main__':raise SystemExit('Use run_revo2.py so producer dependencies cannot be bypassed.')
