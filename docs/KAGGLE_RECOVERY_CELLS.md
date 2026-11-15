# Exact Kaggle cell replacement procedure

Preserve the original hosted notebook/version and attempts01/02. Prefer importing the new semantic_inference_recovery_v4.ipynb into a fresh private copy/session and attaching the new private dataset version. The code below is identical to that notebook. If editing a private copy of the original notebook, REPLACE each identified code cell in full, in this order; retain markdown cells as desired.

Replace every separate exploratory staging cell or standalone bitsandbytes upgrade cell (recognizable first line `python = str(rgpt_python)`) with the single comment `# Archived workaround: integrated validated staging/setup below; do not execute this cell.` Do not run a later cell that reassigns rgpt_input to the mounted dataset or installs into the base interpreter.

## Before a restart: ADD one archival cell to the historical notebook

Place this NEW separate cell immediately ABOVE the configuration cell whose first line is `from pathlib import Path`. Run it before stopping/restarting that existing session if the attempt01/02 directories have not both been downloaded. It performs no inference and never overwrites existing archives. Download every printed ZIP through the Output browser. Only the downloaded attempt02 archive has been verified locally; working files are ephemeral.

```python
from pathlib import Path
import zipfile
for preserved_attempt in ('01','02'):
    preserved_root = Path('/kaggle/working') / ('rgpt-result-' + preserved_attempt)
    preserved_zip = Path('/kaggle/working') / ('rgpt-preserved-' + preserved_attempt + '.zip')
    if not preserved_root.is_dir():
        print('Not present in this session:',preserved_root)
        continue
    if not preserved_zip.exists():
        with zipfile.ZipFile(preserved_zip,'x',zipfile.ZIP_DEFLATED) as archive:
            for name in ('raw_response.txt','candidates.json','execution.json','output-manifest.json','result.zip'):
                path = preserved_root/name
                if path.is_file(): archive.writestr(name,path.read_bytes())
    print('Download privately using Output browser:',preserved_zip)
```

## Code cell 1: REPLACE entire cell

Locate old first line: `from pathlib import Path`.

Configuration: actual new manifest SHA and attempt03.

Place immediately ABOVE the staging cell.

```python
from pathlib import Path
import hashlib, json, os, subprocess, sys, zipfile

rgpt_expected_sha = '7fe245a4080fe9b80da79f95741ffcc7a390fe8c38f298a24d59a62812879d3d'
rgpt_attempt = '03'
rgpt_input_root = Path('/kaggle/input')
rgpt_work_root = Path('/kaggle/working')
rgpt_physical_device = 0
```

Success: configuration variables set without error.

## Code cell 2: REPLACE entire cell

Locate old first line: `rgpt_matches = [p for p in rgpt_input_root.rglob('input-manifest.json')`.

Integrated staging/validation/extraction: one rgpt_input assignment to validated writable input.

Place immediately BELOW code cell 1 above.

```python
# Bootstrap source is embedded from the hash-verified packaged snapshot.
# Bootstrap module SHA256: 5b0b6fdde09fc7c154540e73a28e41f61ed7019d73b048bf284f4e3d88bf6a4d
"""Standard-library-only trusted notebook bootstrap; embedded verbatim in v4."""
import hashlib
import io
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
import zipfile

PAYLOADS = {'packet.json', 'request.json', 'runtime.json', 'code.zip'}
MAX_PAYLOAD_BYTES = 32_000_000


def bootstrap_input(input_root, work_root, expected_sha, attempt='03'):
    """Restore transported ZIP bytes, validate, then stage/extract into fresh paths.

    A mounted code/ directory is never executable input. code.zip.bin is only a
    transport name for the original manifest's code.zip bytes, not a new archive.
    Nothing is deleted or reused, including partial staging from a failed call.
    """
    if not re.fullmatch(r'[a-f0-9]{64}', expected_sha) or not re.fullmatch(r'[A-Za-z0-9_-]{1,32}', attempt):
        raise ValueError('invalid retained SHA or attempt identifier')
    digest = lambda data: hashlib.sha256(data).hexdigest()
    matches = [p for p in Path(input_root).rglob('input-manifest.json')
               if not p.is_symlink() and p.stat().st_size <= 1_000_000
               and digest(p.read_bytes()) == expected_sha]
    if len(matches) != 1:
        raise ValueError('expected exactly one matching mounted manifest; found ' + str(len(matches)))
    mounted = matches[0].parent
    manifest_bytes = matches[0].read_bytes()
    manifest = json.loads(manifest_bytes)
    if set(manifest.get('files', {})) != PAYLOADS:
        raise ValueError('unexpected input manifest file set')
    if not re.fullmatch(r'[a-f0-9]{40}', manifest.get('code_commit', '')):
        raise ValueError('invalid source commit')
    blobs, transports = {}, {}
    for name in sorted(PAYLOADS):
        candidates = [mounted / name]
        if name == 'code.zip':
            candidates = [mounted / 'code.zip.bin', mounted / 'code.zip']
        existing = [p for p in candidates if p.is_file() and not p.is_symlink()]
        if not existing:
            raise FileNotFoundError('missing payload: ' + name + '; expanded code/ is not a substitute')
        entry = manifest['files'][name]
        if type(entry.get('bytes')) is not int or not 0 <= entry['bytes'] <= MAX_PAYLOAD_BYTES:
            raise ValueError('unsafe payload size: ' + name)
        for path in existing:
            if path.stat().st_size != entry['bytes']:
                raise ValueError('payload size mismatch: ' + path.name)
            data = path.read_bytes()
            if digest(data) != entry['sha256']:
                raise ValueError('payload hash mismatch: ' + path.name)
        blobs[name] = existing[0].read_bytes()
        transports[name] = existing[0].name
    archive = zipfile.ZipFile(io.BytesIO(blobs['code.zip']))
    with archive:
        members = archive.infolist()
        if sum(i.file_size for i in members) > MAX_PAYLOAD_BYTES:
            raise ValueError('code archive is too large')
        names = set()
        for info in members:
            name = info.filename
            path = PurePosixPath(name)
            if (not name or not path.parts or '\x00' in name or '\\' in name or path.is_absolute()
                    or '..' in path.parts or PureWindowsPath(name).drive
                    or stat.S_IFMT(info.external_attr >> 16) == stat.S_IFLNK
                    or name.rstrip('/').casefold() in names):
                raise ValueError('unsafe code archive member: ' + name)
            names.add(name.rstrip('/').casefold())
        if archive.testzip() is not None:
            raise ValueError('code archive CRC failure')
        work = Path(work_root).resolve(strict=True)
        staged = work / ('rgpt-staged-input-' + attempt)
        source = work / ('rgpt-source-' + manifest['code_commit'][:7] + '-' + attempt)
        if staged.exists() or source.exists():
            raise FileExistsError('staged/source path exists; preserve it and use a fresh session or attempt identifier')
        staged.mkdir()
        for name, data in blobs.items():
            (staged / name).write_bytes(data)
        (staged / 'input-manifest.json').write_bytes(manifest_bytes)
        source.mkdir()
        for info in members:
            target = source.joinpath(*PurePosixPath(info.filename).parts)
            if not target.resolve().is_relative_to(source):
                raise ValueError('archive path escaped source directory')
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(info))
    record = {'package_id': manifest['package_id'], 'input_manifest_sha256': expected_sha,
              'mounted_input': str(mounted), 'staged_input': str(staged), 'source': str(source),
              'code_commit': manifest['code_commit'], 'transport_names': transports,
              'code_zip_sha256': digest(blobs['code.zip'])}
    return staged, source, record


rgpt_bootstrap_report = rgpt_work_root / ('rgpt-bootstrap-' + rgpt_attempt + '.json')
if rgpt_bootstrap_report.exists():
    raise FileExistsError('Preserve existing bootstrap diagnostics; use a fresh session/attempt')
try:
    rgpt_input, rgpt_code, rgpt_bootstrap = bootstrap_input(rgpt_input_root, rgpt_work_root, rgpt_expected_sha, rgpt_attempt)
    rgpt_bootstrap['status'] = 'READY'
except Exception as rgpt_error:
    rgpt_bootstrap = {'status':'FAILED','error_type':type(rgpt_error).__name__,'error':str(rgpt_error)}
    rgpt_bootstrap_report.write_text(json.dumps(rgpt_bootstrap,indent=2))
    raise
rgpt_bootstrap_report.write_text(json.dumps(rgpt_bootstrap,indent=2))
print(json.dumps(rgpt_bootstrap,indent=2))
```

Success: printed status READY; stop and download diagnostics on any exception.

## Code cell 3: REPLACE entire cell

Locate old first line: `rgpt_env = rgpt_work_root / 'rgpt-inference-env' (or hosted rgpt_python = Path(sys.executable))`.

Overlay setup and real GPU/NF4 preflight: no venv, ensurepip, or base upgrades.

Place immediately BELOW code cell 2 above.

```python
rgpt_python = Path(sys.executable)
rgpt_overlay = rgpt_work_root / ('rgpt-runtime-deps-' + rgpt_attempt)
rgpt_setup_path = rgpt_work_root / ('rgpt-setup-' + rgpt_attempt + '.json')
rgpt_setup_log = rgpt_work_root / ('rgpt-setup-' + rgpt_attempt + '.log')
rgpt_environment_report = rgpt_work_root / ('rgpt-environment-' + rgpt_attempt + '.json')
if any(p.exists() for p in (rgpt_overlay,rgpt_setup_path,rgpt_setup_log,rgpt_environment_report)):
    raise FileExistsError('Preserve prior setup; use a fresh session or attempt identifier')
rgpt_child_env = os.environ.copy()
for rgpt_key in ('PIP_INDEX_URL','PIP_EXTRA_INDEX_URL','PIP_TRUSTED_HOST'):
    rgpt_child_env.pop(rgpt_key,None)
rgpt_child_env.update(PYTHONPATH=os.pathsep.join((str(rgpt_code),str(rgpt_overlay))),RGPT_OVERLAY_PATH=str(rgpt_overlay),
                      PYTHONNOUSERSITE='1',USE_TF='0',USE_FLAX='0',CUDA_VISIBLE_DEVICES=str(rgpt_physical_device))
rgpt_runtime = json.loads((rgpt_input/'runtime.json').read_text())
rgpt_profile = rgpt_runtime['environment_profile']
rgpt_setup = {'status':'FAILED','input_manifest_sha256':rgpt_expected_sha,'python_executable':str(rgpt_python),'overlay':str(rgpt_overlay)}
def rgpt_setup_run(command):
    result = subprocess.run(command,cwd=rgpt_code,env=rgpt_child_env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    with rgpt_setup_log.open('a',encoding='utf-8') as log: log.write(result.stdout)
    print(result.stdout)
    if result.returncode: raise subprocess.CalledProcessError(result.returncode,command)
try:
    rgpt_requirements = (rgpt_code/rgpt_profile['requirements_file']).resolve()
    if not rgpt_requirements.is_relative_to(rgpt_code.resolve()): raise ValueError('Unsafe requirements path')
    if hashlib.sha256(rgpt_requirements.read_bytes()).hexdigest()!=rgpt_profile['requirements_sha256']: raise ValueError('Requirements hash mismatch')
    rgpt_probe = "import json,sys,torch; p=json.loads(sys.argv[1]); print(json.dumps({'python':sys.version,'executable':sys.executable,'torch':torch.__version__,'cuda':torch.version.cuda})); assert torch.__version__==p['torch_version'] and torch.version.cuda==p['torch_cuda'], 'Base torch/CUDA profile mismatch; stop without changing PyTorch'"
    rgpt_setup_run([str(rgpt_python),'-c',rgpt_probe,json.dumps(rgpt_profile)])
    rgpt_overlay.mkdir()
    rgpt_setup_run([str(rgpt_python),'-m','pip','install','--index-url','https://pypi.org/simple','--target',str(rgpt_overlay),
                    '--no-deps','--only-binary=:all:','--no-compile','-r',str(rgpt_requirements)])
    rgpt_setup_run([str(rgpt_python),'-m','kaggle.environment','--runtime',str(rgpt_input/'runtime.json'),'--overlay',str(rgpt_overlay),
                    '--device',str(rgpt_physical_device),'--report',str(rgpt_environment_report)])
    rgpt_preflight = json.loads(rgpt_environment_report.read_text())
    if rgpt_preflight['status']!='READY': raise RuntimeError('GPU/dependency preflight failed')
    rgpt_setup['status']='READY'
except Exception as rgpt_error:
    rgpt_setup.update(error_type=type(rgpt_error).__name__,error=str(rgpt_error))
    rgpt_setup_path.write_text(json.dumps(rgpt_setup,indent=2))
    raise
rgpt_setup_path.write_text(json.dumps(rgpt_setup,indent=2))
print(json.dumps(rgpt_setup,indent=2))
```

Success: printed status READY; stop and download diagnostics on any exception.

## Code cell 4: REPLACE entire cell

Locate old first line: `subprocess.run(['nvidia-smi', '--query-gpu=index,name,memory.free,memory.total', '--format=csv'], check=True)`.

Inspect prepared configuration and actual available GPUs.

Place immediately BELOW code cell 3 above.

```python
subprocess.run(['nvidia-smi','--query-gpu=index,name,memory.free,memory.total','--format=csv'],check=True)
print(json.dumps({'input_manifest_sha256':rgpt_expected_sha,'requested_model':rgpt_runtime['requested_model'],
                  'generation':rgpt_runtime['generation'],'quantization':rgpt_runtime['quantization'],
                  'environment_profile':rgpt_profile},indent=2))
```

Success: GPUs/config displayed; inspect matching T4/profile before continuing.

## Code cell 5: REPLACE entire cell

Locate old first line: `rgpt_result = rgpt_work_root / 'rgpt-result-01' (or hosted rgpt-result-02)`.

One controlled inference; preserves attempts01/02 and refuses existing attempt03.

Place immediately BELOW code cell 4 above.

```python
rgpt_result = rgpt_work_root / ('rgpt-result-' + rgpt_attempt)
if rgpt_result.exists(): raise FileExistsError('Preserve existing inference artifacts; do not rerun/overwrite')
rgpt_setup = json.loads(rgpt_setup_path.read_text())
if rgpt_setup['status']!='READY' or rgpt_setup['input_manifest_sha256']!=rgpt_expected_sha: raise RuntimeError('Matching setup is not READY')
rgpt_command = [str(rgpt_python),'-m','kaggle.run_inference','--input',str(rgpt_input),'--expected-input-sha256',rgpt_expected_sha,
                '--device',str(rgpt_physical_device),'--output',str(rgpt_result)]
rgpt_run = subprocess.run(rgpt_command,cwd=rgpt_code,env=rgpt_child_env,check=False)
print(json.dumps({'runner_exit_code':rgpt_run.returncode,'result_directory':str(rgpt_result)}))
if rgpt_run.returncode: print('FAILED. Preserve diagnostics; do not repair candidates or rerun Qwen automatically.')
```

Success: exit code0 and execution status COMPLETED mean schema-valid proposals only. On nonzero exit, download artifacts and stop; do not retry automatically.

## Code cell 6: REPLACE entire cell

Locate old first line: `rgpt_result_zip = rgpt_result / 'result.zip'`.

Build private debug ZIP and download using Output browser, including failures.

Place immediately BELOW code cell 5 above.

```python
rgpt_result = rgpt_work_root / ('rgpt-result-' + rgpt_attempt)
rgpt_debug = rgpt_work_root / ('rgpt-codex-debug-' + rgpt_attempt + '.zip')
if rgpt_debug.exists(): raise FileExistsError('Preserve existing debug archive')
rgpt_files = [(rgpt_result/name,name) for name in ('raw_response.txt','candidates.json','execution.json','output-manifest.json','result.zip')]
rgpt_files += [(rgpt_work_root/name,name) for name in ('rgpt-bootstrap-'+rgpt_attempt+'.json','rgpt-setup-'+rgpt_attempt+'.json',
              'rgpt-setup-'+rgpt_attempt+'.log','rgpt-environment-'+rgpt_attempt+'.json')]
if 'rgpt_input' in globals(): rgpt_files += [(rgpt_input/name,'input/'+name) for name in ('input-manifest.json','request.json','runtime.json')]
rgpt_existing = [(p,n) for p,n in rgpt_files if p.is_file() and not p.is_symlink()]
if not rgpt_existing: raise FileNotFoundError('No diagnostics exist; retain the notebook error')
with zipfile.ZipFile(rgpt_debug,'x',zipfile.ZIP_DEFLATED) as archive:
    for path,name in rgpt_existing: archive.writestr(name,path.read_bytes())
print(json.dumps({'download_via_Output_browser':str(rgpt_debug),'sha256':hashlib.sha256(rgpt_debug.read_bytes()).hexdigest(),
                  'result_zip_present':(rgpt_result/'result.zip').is_file()},indent=2))
if (rgpt_result/'execution.json').is_file(): print((rgpt_result/'execution.json').read_text())
```

Success: printed debug ZIP path exists in Output browser. Download it privately and stop GPU session. Missing result.zip means no completed runner artifact, not success.

