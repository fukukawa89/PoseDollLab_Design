"""O3 run evidence: seal every produced file, then verify the full set before/after consumption."""
from pathlib import Path
import datetime, hashlib, json, os, re, subprocess, sys
from revo2_evidence import REPO, HW, sha, read, git_head
VERIFY = HW / 'verification/revO3'
GENERATED = HW / 'generated/revO3'
class BlockedInput(RuntimeError):
    pass

def save(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, dict) and os.environ.get('REVO3_RUN_ID'):
        value = {'run_id': os.environ['REVO3_RUN_ID'], **value}
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')

def sources():
    from revo2_evidence import sources as old_sources
    result = old_sources()
    for folder in (REPO/'Firmware/PoseDollFullBody/revO3', HW/'docs/revO3_review_source'):
        for p in folder.rglob('*'):
            if p.is_file() and not any(x in ('__pycache__','managed_components') or x.startswith('build-') for x in p.parts) and p.suffix not in ('.pyc','.obj','.exe','.log') and p.name not in ('sdkconfig','sdkconfig.old'):
                result[p.relative_to(REPO).as_posix()] = sha(p)
    return dict(sorted(result.items()))

def run_paths(run_id=None):
    rid = run_id or os.environ.get('REVO3_RUN_ID')
    if not rid or not re.fullmatch(r'[A-Za-z0-9_-]+', rid):
        raise ValueError('Explicit safe REVO3_RUN_ID required')
    return VERIFY/'runs'/rid, GENERATED/'runs'/rid

def _relative(path):
    p=Path(path).resolve()
    try: return p.relative_to(REPO.resolve()).as_posix()
    except ValueError as e: raise BlockedInput('Artifact outside repository: '+str(path)) from e

def _files(paths):
    found=set()
    for name in paths:
        p=REPO/name if not Path(name).is_absolute() else Path(name)
        if not p.exists(): raise BlockedInput('Missing artifact root: '+str(p))
        found.update(x for x in p.rglob('*') if x.is_file()) if p.is_dir() else found.add(p)
    return {_relative(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(found)}

def merkle(files):
    # Canonical flat Merkle root binds paths, sizes and file hashes, not just names.
    return hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',',':')).encode()).hexdigest()

def seal_artifacts(path, producer, run_id, roots):
    roots=[_relative(p) for p in roots]
    files=_files(roots)
    if not files: raise BlockedInput('Producer emitted empty artifact set')
    manifest={'schema':'revo3-artifact-set-v1','run_id':run_id,'producer':producer,'roots':roots,'files':files,'merkle_root':merkle(files)}
    save(path,manifest)
    return {'path':_relative(path),'sha256':sha(path),'merkle_root':manifest['merkle_root'],'file_count':len(files)}

def verify_artifacts(record, run_id=None):
    path=REPO/record['path']
    if not path.is_file() or sha(path)!=record['sha256']:
        raise BlockedInput('Producer manifest missing/replaced: '+record['path'])
    data=read(path)
    if run_id is not None and data.get('run_id')!=run_id: raise BlockedInput('Artifact set run_id mismatch')
    if data.get('merkle_root')!=record['merkle_root'] or merkle(data['files'])!=record['merkle_root']:
        raise BlockedInput('Producer artifact root changed')
    actual=_files(data['roots'])
    if actual!=data['files']:
        changed=sorted(p for p in set(actual)|set(data['files']) if actual.get(p)!=data['files'].get(p))
        raise BlockedInput('Produced files missing/replaced/added: '+', '.join(changed[:12]))
    return data

class ArtifactReader:
    """Consumers explicitly identify every STEP/JSON/native artifact they open."""
    def __init__(self, producer):
        deps=json.loads(os.environ.get('REVO3_DEPENDENCIES','{}'))
        if producer not in deps: raise BlockedInput('No verified producer supplied: '+producer)
        self.record=deps[producer];self.data=verify_artifacts(self.record,os.environ.get('REVO3_RUN_ID'));self.used={}
    def path(self, path):
        rel=_relative(path);record=self.data['files'].get(rel)
        if record is None or not Path(path).is_file() or sha(path)!=record['sha256']:
            raise BlockedInput('Consumer file is absent, unsealed or replaced: '+rel)
        self.used[rel]=record['sha256'];return Path(path)
    def json(self,path): return read(self.path(path))
    def receipt(self):
        verify_artifacts(self.record,os.environ.get('REVO3_RUN_ID'))
        return {'producer_manifest':self.record,'actually_read_sha256':self.used}

class Run:
    def __init__(self, run_id):
        self.run_id=run_id;self.path,self.out=run_paths(run_id)
        if self.path.exists() or self.out.exists(): raise FileExistsError('Run is immutable: '+run_id)
        self.path.mkdir(parents=True);self.out.mkdir(parents=True)
        self.inputs=sources();self.steps={}
        self.meta={'schema':'revo3-run-v1','run_id':run_id,'base_commit':git_head(),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha256':self.inputs,'physical_tested':False,'manufacturing_released':False}
        save(self.path/'inputs.json',self.meta)
    def step(self,name,command,dependencies=(),extra_env=None,expected_paths=(),artifact_roots=()):
        report={'run_id':self.run_id,'command':list(map(str,command)),'dependencies':list(dependencies),'status':'NOT_RUN'}
        deps={}
        try:
            for dep in dependencies:
                source=self.steps.get(dep,{})
                if source.get('status')!='PASS': raise BlockedInput('Failed/missing producer: '+dep)
                if source.get('artifacts'):
                    verify_artifacts(source['artifacts'],self.run_id);deps[dep]=source['artifacts']
                else: raise BlockedInput('Dependency has no sealed output set: '+dep)
        except (BlockedInput,KeyError,ValueError,OSError) as e:
            report.update(status='BLOCKED_DEPENDENCY',reason=str(e),exit_code=None)
        else:
            env=os.environ.copy();env.update(REVO3_RUN_ID=self.run_id,PYTHONUTF8='1',REVO3_DEPENDENCIES=json.dumps(deps));env.update(extra_env or {})
            started=datetime.datetime.now(datetime.timezone.utc)
            log=self.path/(name+'.txt')
            try:
                with log.open('wb') as stream:
                    result=subprocess.run(command,cwd=REPO,env=env,stdout=stream,stderr=subprocess.STDOUT)
                report.update(status='PASS' if result.returncode==0 else 'FAIL',exit_code=result.returncode,log=_relative(log),log_sha256=sha(log))
                missing=[str(p) for p in expected_paths if not Path(p).is_file()]
                if report['status']=='PASS' and missing: report.update(status='FAIL_EXPECTED_OUTPUT_MISSING',missing=missing)
                # Detect dependency mutation during the consumer, too. Do not re-seal changed input.
                for record in deps.values(): verify_artifacts(record,self.run_id)
                if report['status']=='PASS':
                    roots=list(dict.fromkeys([str(log),*map(str,expected_paths),*map(str,artifact_roots)]))
                    if roots: report['artifacts']=seal_artifacts(self.path/'artifacts'/(name+'.json'),name,self.run_id,roots)
            except BlockedInput as e: report.update(status='BLOCKED_CHANGED_INPUT',reason=str(e))
            except OSError as e: report.update(status='BLOCKED_TOOL_OR_INPUT',reason=str(e),exit_code=None)
            report['duration_s']=(datetime.datetime.now(datetime.timezone.utc)-started).total_seconds()
        self.steps[name]=report;save(self.path/(name+'_execution.json'),report)
        print(name,report['status'],report.get('reason',''),flush=True)
        if report['status']!='PASS' and report.get('log'): print((REPO/report['log']).read_text(encoding='utf-8',errors='replace')[-2200:],flush=True)
        return report['status']=='PASS'
    def finish(self):
        current=sources()
        changed=[p for p in set(self.inputs)|set(current) if self.inputs.get(p)!=current.get(p)]
        problems=[]
        for name,step in self.steps.items():
            if step.get('artifacts'):
                try: verify_artifacts(step['artifacts'],self.run_id)
                except (BlockedInput,ValueError,KeyError,OSError) as e: problems.append({'producer':name,'error':str(e)})
        status='PASS_EXECUTION_ONLY' if self.steps and all(s['status']=='PASS' for s in self.steps.values()) and not problems and not changed else 'INCOMPLETE_OR_FAILED'
        outputs={_relative(p):sha(p) for root in (self.path,self.out) for p in root.rglob('*') if p.is_file() and p.name!='run.json'}
        result={**self.meta,'status':status,'source_changed_during_run':changed,'artifact_integrity_errors':problems,'steps':self.steps,'output_sha256':outputs,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
        save(self.path/'run.json',result);save(VERIFY/'latest.json',{'run_id':self.run_id,'execution_status':status,'report':_relative(self.path/'run.json')})
        return result