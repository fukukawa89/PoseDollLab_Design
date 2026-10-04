"""Immutable run directories, checked dependencies, and complete source fingerprints."""
from pathlib import Path
import datetime, hashlib, json, os, re, subprocess, sys
REPO=Path(__file__).resolve().parents[1]
HW=REPO/'Hardware/PoseDoll44'
VERIFY=HW/'verification/revO2'
GENERATED=HW/'generated/revO2'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    if isinstance(v,dict) and os.environ.get('REVO2_RUN_ID'):v={'run_id':os.environ['REVO2_RUN_ID'],**v}
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def sources():
    paths=set()
    for folder in ['scripts','Hardware/PoseDoll44/cad','Hardware/PoseDoll44/tools','Hardware/PoseDoll44/mechanical_manifest','Firmware/PoseDollFullBody/main','Firmware/PoseDollFullBody/tools','Firmware/PoseDollFullBody/revO2','Tools/PoseDollHardwareBridge','Tools/PoseDollSimulator','Shared','Hardware/PoseDoll44/reference/ue58','scripts/tests']:
        for p in (REPO/folder).rglob('*'):
            if p.is_file() and not any(t.startswith('build') or t in ('__pycache__','managed_components','vendor') for t in p.relative_to(REPO/folder).parts[:-1]) and (p.suffix in ('.py','.c','.h','.json','.ps1','.cmd','.txt','.defaults','.html','.cjs') or p.name.startswith('sdkconfig.') or p.name=='Kconfig.projbuild'):
                if p.name not in ('local_toolchain.json','sdkconfig','sdkconfig.old'):paths.add(p)
    paths.add(HW/'electronics/sensor_revM_side/sensor_revM_side.step')
    paths.update(p for p in (REPO/'requirements.txt',REPO/'pyproject.toml',REPO/'pytest.ini') if p.is_file())
    paths.update((HW/'docs/revO2_review_source').glob('*'))
    return {p.relative_to(REPO).as_posix():sha(p) for p in sorted(paths) if p.is_file()}
def run_paths(run_id=None):
    run_id=run_id or os.environ.get('REVO2_RUN_ID')
    if not run_id or not re.fullmatch(r'[A-Za-z0-9_-]+',run_id):raise ValueError('Explicit safe REVO2_RUN_ID required')
    return VERIFY/'runs'/run_id,GENERATED/'runs'/run_id
def git_head():return subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO).decode().strip()

class Run:
    def __init__(self,run_id):
        self.run_id=run_id;self.path,self.out=run_paths(run_id)
        if self.path.exists() or self.out.exists():raise FileExistsError(f'Run is immutable: {self.path}')
        self.path.mkdir(parents=True);self.out.mkdir(parents=True)
        self.inputs=sources();self.steps={}
        self.meta={'schema':'revo2-run-v1','run_id':run_id,'base_commit':git_head(),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha256':self.inputs,'python':sys.version,'physical_tested':False,'manufacturing_released':False}
        save(self.path/'inputs.json',self.meta)
    def step(self,name,command,dependencies=(),extra_env=None,expected_paths=()):
        report={'run_id':self.run_id,'command':list(map(str,command)),'dependencies':list(dependencies),'status':'NOT_RUN','outputs':{}}
        bad=[d for d in dependencies if self.steps.get(d,{}).get('status')!='PASS']
        for d in dependencies:
            for rel,digest in self.steps.get(d,{}).get('outputs',{}).items():
                p=REPO/rel
                if not p.is_file() or sha(p)!=digest:bad.append(d+':output_missing_or_replaced')
        if bad:report.update(status='BLOCKED_DEPENDENCY',blocked_by=bad,exit_code=None)
        else:
            env=os.environ.copy();env['REVO2_RUN_ID']=self.run_id;env['PYTHONUTF8']='1';env.update(extra_env or {})
            start=datetime.datetime.now(datetime.timezone.utc)
            try:
                result=subprocess.run(command,cwd=REPO,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
                log=self.path/(name+'.txt');log.write_bytes(result.stdout)
                report.update(exit_code=result.returncode,status='PASS' if result.returncode==0 else 'FAIL',log=log.relative_to(REPO).as_posix(),log_sha256=sha(log))
                print(name,report['status'],result.stdout.decode('utf-8',errors='replace')[-2500:],flush=True)
            except OSError as e:report.update(status='BLOCKED_TOOL_UNAVAILABLE',exit_code=None,error=str(e))
            report['duration_s']=(datetime.datetime.now(datetime.timezone.utc)-start).total_seconds()
        missing=[str(p) for p in expected_paths if not Path(p).is_file()]
        if report['status']=='PASS' and missing:report.update(status='FAIL_EXPECTED_OUTPUT_MISSING',missing_outputs=missing)
        if report['status']=='PASS':report['outputs']={Path(p).relative_to(REPO).as_posix():sha(p) for p in expected_paths}
        self.steps[name]=report;save(self.path/(name+'_execution.json'),report)
        return report['status']=='PASS'
    def finish(self):
        current=sources();changed=[p for p in set(current)|set(self.inputs) if current.get(p)!=self.inputs.get(p)]
        status='PASS_EXECUTION_ONLY' if self.steps and all(v['status']=='PASS' for v in self.steps.values()) else 'INCOMPLETE_OR_FAILED'
        if changed:status='FAIL_INPUT_CHANGED_DURING_RUN'
        outputs={p.relative_to(REPO).as_posix():sha(p) for folder in (self.path,self.out) for p in folder.rglob('*') if p.is_file() and p.name!='run.json'}
        report={**self.meta,'status':status,'source_changed_during_run':changed,'steps':self.steps,'output_sha256':outputs,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
        save(self.path/'run.json',report);save(VERIFY/'latest.json',{'run_id':self.run_id,'report':(self.path/'run.json').relative_to(REPO).as_posix(),'execution_status':status})
        return report
