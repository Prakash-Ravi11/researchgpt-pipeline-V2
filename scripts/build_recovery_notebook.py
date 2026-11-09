"""Build a complete recovery notebook and exact cell replacement instructions."""
import argparse
import json
from pathlib import Path
import re
import zipfile

from pipeline.inference.packages import validate_input, digest


def render(input_root, attempt='03'):
    if not re.fullmatch(r'[0-9]{2,8}', attempt):
        raise ValueError('use a distinct numeric attempt identifier')
    root = Path(input_root)
    sha = digest((root / 'input-manifest.json').read_bytes())
    manifest, _, _, runtime = validate_input(root, sha)
    profile = runtime['environment_profile']
    with zipfile.ZipFile(root / 'code.zip') as archive:
        bootstrap = archive.read('kaggle/bootstrap.py').decode('utf-8')
        requirements = archive.read(profile['requirements_file'])
        if digest(requirements) != profile['requirements_sha256']:
            raise ValueError('archived overlay requirements differ from runtime')
    cells = []

    def md(text):
        cells.append({'cell_type': 'markdown', 'metadata': {}, 'source': text.splitlines(keepends=True)})

    def code(text):
        compile(text, 'recovery-notebook-cell', 'exec')
        cells.append({'cell_type': 'code', 'execution_count': None, 'metadata': {},
                      'outputs': [], 'source': text.splitlines(keepends=True)})

    md('# ResearchGPT V2 — private recovery attempt ' + attempt + '\n\n'
       'Authoring status: **NOT EXECUTED on Kaggle**. Preserve attempts 01/02 and all historical inputs. '
       'This notebook stages exact code.zip.bin bytes, uses the existing Kaggle interpreter with an isolated '
       'working-directory dependency overlay, verifies the prepared CUDA13/T4 profile, and invokes the '
       'schema-constrained runner once. No verified scientific result is implied by generation/schema success.\n\n'
       'Upload four JSON files plus code.zip.bin from the new package as a private dataset version. '
       'Keep the notebook private, attach that version, select T4 x2 and enable Internet. '
       'Before ending/restarting an existing session, download/save attempts01/02; /kaggle/working is ephemeral. '
       'Only attempt02 has been verified locally. Then use a fresh GPU session. '
       'No cells delete or reuse an existing run/partial environment. '
       'Stop on any bootstrap/setup error; use the last cell to download available diagnostics.\n')
    code("from pathlib import Path\nimport hashlib, json, os, subprocess, sys, zipfile\n\n"
         f"rgpt_expected_sha = {sha!r}\nrgpt_attempt = {attempt!r}\n"
         "rgpt_input_root = Path('/kaggle/input')\nrgpt_work_root = Path('/kaggle/working')\n"
         "rgpt_physical_device = 0\n")
    code('# Bootstrap source is embedded from the hash-verified packaged snapshot.\n'
         '# Bootstrap module SHA256: ' + digest(bootstrap.encode()) + '\n' + bootstrap + '\n\n'
         "rgpt_bootstrap_report = rgpt_work_root / ('rgpt-bootstrap-' + rgpt_attempt + '.json')\n"
         "if rgpt_bootstrap_report.exists():\n    raise FileExistsError('Preserve existing bootstrap diagnostics; use a fresh session/attempt')\n"
         "try:\n    rgpt_input, rgpt_code, rgpt_bootstrap = bootstrap_input(rgpt_input_root, rgpt_work_root, rgpt_expected_sha, rgpt_attempt)\n"
         "    rgpt_bootstrap['status'] = 'READY'\n"
         "except Exception as rgpt_error:\n    rgpt_bootstrap = {'status':'FAILED','error_type':type(rgpt_error).__name__,'error':str(rgpt_error)}\n"
         "    rgpt_bootstrap_report.write_text(json.dumps(rgpt_bootstrap,indent=2))\n    raise\n"
         "rgpt_bootstrap_report.write_text(json.dumps(rgpt_bootstrap,indent=2))\nprint(json.dumps(rgpt_bootstrap,indent=2))\n")
    md('## Setup and GPU preflight\n\nNo venv/ensurepip and no base-package upgrades. '
       'The overlay installs only the exact prepared wheels with --no-deps; active dependency closure is then '
       'checked before a GPU tensor/NF4 operation. Base PyTorch/CUDA must match the prepared profile. '
       'No model weights are loaded here. A clean-runtime pass remains required.\n')
    code("rgpt_python = Path(sys.executable)\n"
         "rgpt_overlay = rgpt_work_root / ('rgpt-runtime-deps-' + rgpt_attempt)\n"
         "rgpt_setup_path = rgpt_work_root / ('rgpt-setup-' + rgpt_attempt + '.json')\n"
         "rgpt_setup_log = rgpt_work_root / ('rgpt-setup-' + rgpt_attempt + '.log')\n"
         "rgpt_environment_report = rgpt_work_root / ('rgpt-environment-' + rgpt_attempt + '.json')\n"
         "if any(p.exists() for p in (rgpt_overlay,rgpt_setup_path,rgpt_setup_log,rgpt_environment_report)):\n"
         "    raise FileExistsError('Preserve prior setup; use a fresh session or attempt identifier')\n"
         "rgpt_child_env = os.environ.copy()\n"
         "for rgpt_key in ('PIP_INDEX_URL','PIP_EXTRA_INDEX_URL','PIP_TRUSTED_HOST'):\n    rgpt_child_env.pop(rgpt_key,None)\n"
         "rgpt_child_env.update(PYTHONPATH=os.pathsep.join((str(rgpt_code),str(rgpt_overlay))),RGPT_OVERLAY_PATH=str(rgpt_overlay),\n"
         "                      PYTHONNOUSERSITE='1',USE_TF='0',USE_FLAX='0',CUDA_VISIBLE_DEVICES=str(rgpt_physical_device))\n"
         "rgpt_runtime = json.loads((rgpt_input/'runtime.json').read_text())\nrgpt_profile = rgpt_runtime['environment_profile']\n"
         "rgpt_setup = {'status':'FAILED','input_manifest_sha256':rgpt_expected_sha,'python_executable':str(rgpt_python),'overlay':str(rgpt_overlay)}\n"
         "def rgpt_setup_run(command):\n"
         "    result = subprocess.run(command,cwd=rgpt_code,env=rgpt_child_env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)\n"
         "    with rgpt_setup_log.open('a',encoding='utf-8') as log: log.write(result.stdout)\n"
         "    print(result.stdout)\n    if result.returncode: raise subprocess.CalledProcessError(result.returncode,command)\n"
         "try:\n"
         "    rgpt_requirements = (rgpt_code/rgpt_profile['requirements_file']).resolve()\n"
         "    if not rgpt_requirements.is_relative_to(rgpt_code.resolve()): raise ValueError('Unsafe requirements path')\n"
         "    if hashlib.sha256(rgpt_requirements.read_bytes()).hexdigest()!=rgpt_profile['requirements_sha256']: raise ValueError('Requirements hash mismatch')\n"
         "    rgpt_probe = \"import json,sys,torch; p=json.loads(sys.argv[1]); print(json.dumps({'python':sys.version,'executable':sys.executable,'torch':torch.__version__,'cuda':torch.version.cuda})); assert torch.__version__==p['torch_version'] and torch.version.cuda==p['torch_cuda'], 'Base torch/CUDA profile mismatch; stop without changing PyTorch'\"\n"
         "    rgpt_setup_run([str(rgpt_python),'-c',rgpt_probe,json.dumps(rgpt_profile)])\n"
         "    rgpt_overlay.mkdir()\n"
         "    rgpt_setup_run([str(rgpt_python),'-m','pip','install','--index-url','https://pypi.org/simple','--target',str(rgpt_overlay),\n"
         "                    '--no-deps','--only-binary=:all:','--no-compile','-r',str(rgpt_requirements)])\n"
         "    rgpt_setup_run([str(rgpt_python),'-m','kaggle.environment','--runtime',str(rgpt_input/'runtime.json'),'--overlay',str(rgpt_overlay),\n"
         "                    '--device',str(rgpt_physical_device),'--report',str(rgpt_environment_report)])\n"
         "    rgpt_preflight = json.loads(rgpt_environment_report.read_text())\n"
         "    if rgpt_preflight['status']!='READY': raise RuntimeError('GPU/dependency preflight failed')\n"
         "    rgpt_setup['status']='READY'\n"
         "except Exception as rgpt_error:\n"
         "    rgpt_setup.update(error_type=type(rgpt_error).__name__,error=str(rgpt_error))\n"
         "    rgpt_setup_path.write_text(json.dumps(rgpt_setup,indent=2))\n    raise\n"
         "rgpt_setup_path.write_text(json.dumps(rgpt_setup,indent=2))\nprint(json.dumps(rgpt_setup,indent=2))\n")
    md('## Inspect, then run once\n\nREADY confirms the recorded environment/GPU preflight, '
       'not scientific accuracy. The runner validates prompt length and schema grammar before model weights. '
       'EOS still requires valid schema and then separate trusted local evidence verification.\n')
    code("subprocess.run(['nvidia-smi','--query-gpu=index,name,memory.free,memory.total','--format=csv'],check=True)\n"
         "print(json.dumps({'input_manifest_sha256':rgpt_expected_sha,'requested_model':rgpt_runtime['requested_model'],\n"
         "                  'generation':rgpt_runtime['generation'],'quantization':rgpt_runtime['quantization'],\n"
         "                  'environment_profile':rgpt_profile},indent=2))\n")
    code("rgpt_result = rgpt_work_root / ('rgpt-result-' + rgpt_attempt)\n"
         "if rgpt_result.exists(): raise FileExistsError('Preserve existing inference artifacts; do not rerun/overwrite')\n"
         "rgpt_setup = json.loads(rgpt_setup_path.read_text())\n"
         "if rgpt_setup['status']!='READY' or rgpt_setup['input_manifest_sha256']!=rgpt_expected_sha: raise RuntimeError('Matching setup is not READY')\n"
         "rgpt_command = [str(rgpt_python),'-m','kaggle.run_inference','--input',str(rgpt_input),'--expected-input-sha256',rgpt_expected_sha,\n"
         "                '--device',str(rgpt_physical_device),'--output',str(rgpt_result)]\n"
         "rgpt_run = subprocess.run(rgpt_command,cwd=rgpt_code,env=rgpt_child_env,check=False)\n"
         "print(json.dumps({'runner_exit_code':rgpt_run.returncode,'result_directory':str(rgpt_result)}))\n"
         "if rgpt_run.returncode: print('FAILED. Preserve diagnostics; do not repair candidates or rerun Qwen automatically.')\n")
    md('## Download preserved diagnostics\n\nRun this cell after inference, including failures. '
       'After setup/bootstrap failure, run only this diagnostics cell manually, not the inference cell. '
       'Use Kaggle\'s Output file browser to download the printed debug ZIP; FileLink is not required. '
       'Keep it private. Stop the GPU session after retaining output.\n')
    code("rgpt_result = rgpt_work_root / ('rgpt-result-' + rgpt_attempt)\n"
         "rgpt_debug = rgpt_work_root / ('rgpt-codex-debug-' + rgpt_attempt + '.zip')\n"
         "if rgpt_debug.exists(): raise FileExistsError('Preserve existing debug archive')\n"
         "rgpt_files = [(rgpt_result/name,name) for name in ('raw_response.txt','candidates.json','execution.json','output-manifest.json','result.zip')]\n"
         "rgpt_files += [(rgpt_work_root/name,name) for name in ('rgpt-bootstrap-'+rgpt_attempt+'.json','rgpt-setup-'+rgpt_attempt+'.json',\n"
         "              'rgpt-setup-'+rgpt_attempt+'.log','rgpt-environment-'+rgpt_attempt+'.json')]\n"
         "if 'rgpt_input' in globals(): rgpt_files += [(rgpt_input/name,'input/'+name) for name in ('input-manifest.json','request.json','runtime.json')]\n"
         "rgpt_existing = [(p,n) for p,n in rgpt_files if p.is_file() and not p.is_symlink()]\n"
         "if not rgpt_existing: raise FileNotFoundError('No diagnostics exist; retain the notebook error')\n"
         "with zipfile.ZipFile(rgpt_debug,'x',zipfile.ZIP_DEFLATED) as archive:\n"
         "    for path,name in rgpt_existing: archive.writestr(name,path.read_bytes())\n"
         "print(json.dumps({'download_via_Output_browser':str(rgpt_debug),'sha256':hashlib.sha256(rgpt_debug.read_bytes()).hexdigest(),\n"
         "                  'result_zip_present':(rgpt_result/'result.zip').is_file()},indent=2))\n"
         "if (rgpt_result/'execution.json').is_file(): print((rgpt_result/'execution.json').read_text())\n")
    for i, cell in enumerate(cells):
        cell['id'] = 'rgpt-recovery-' + str(i + 1)
    return {'cells': cells, 'metadata': {'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
            'language_info': {'name': 'python'}, 'researchgpt': {'authoring_execution_status': 'NOT EXECUTED',
            'package_id': manifest['package_id'], 'input_manifest_sha256': sha, 'code_commit': manifest['code_commit'],
            'attempt': attempt, 'bootstrap_sha256': digest(bootstrap.encode())}}, 'nbformat': 4, 'nbformat_minor': 5}


def instructions(notebook):
    old = ['from pathlib import Path', "rgpt_matches = [p for p in rgpt_input_root.rglob('input-manifest.json')",
           "rgpt_env = rgpt_work_root / 'rgpt-inference-env' (or hosted rgpt_python = Path(sys.executable))",
           "subprocess.run(['nvidia-smi', '--query-gpu=index,name,memory.free,memory.total', '--format=csv'], check=True)",
           "rgpt_result = rgpt_work_root / 'rgpt-result-01' (or hosted rgpt-result-02)",
           "rgpt_result_zip = rgpt_result / 'result.zip'"]
    descriptions = ['Configuration: actual new manifest SHA and attempt03.',
                    'Integrated staging/validation/extraction: one rgpt_input assignment to validated writable input.',
                    'Overlay setup and real GPU/NF4 preflight: no venv, ensurepip, or base upgrades.',
                    'Inspect prepared configuration and actual available GPUs.',
                    'One controlled inference; preserves attempts01/02 and refuses existing attempt03.',
                    'Build private debug ZIP and download using Output browser, including failures.']
    text = ('# Exact Kaggle cell replacement procedure\n\n'
            'Preserve the original hosted notebook/version and attempts01/02. Prefer importing the new '
            'semantic_inference_recovery_v4.ipynb into a fresh private copy/session and attaching the new private dataset version. '
            'The code below is identical to that notebook. If editing a private copy of the original notebook, '
            'REPLACE each identified code cell in full, in this order; retain markdown cells as desired.\n\n'
            'Replace every separate exploratory staging cell or standalone bitsandbytes upgrade cell '
            '(recognizable first line `python = str(rgpt_python)`) with the single comment '
            '`# Archived workaround: integrated validated staging/setup below; do not execute this cell.` '
            'Do not run a later cell that reassigns rgpt_input to the mounted dataset or installs into the base interpreter.\n\n')
    text += ('## Before a restart: ADD one archival cell to the historical notebook\n\n'
             'Place this NEW separate cell immediately ABOVE the configuration cell whose first line is '
             '`from pathlib import Path`. Run it before stopping/restarting that existing session if the '
             'attempt01/02 directories have not both been downloaded. It performs no inference and never '
             'overwrites existing archives. Download every printed ZIP through the Output browser. '
             'Only the downloaded attempt02 archive has been verified locally; working files are ephemeral.\n\n'
             '```python\nfrom pathlib import Path\nimport zipfile\n'
             "for preserved_attempt in ('01','02'):\n"
             "    preserved_root = Path('/kaggle/working') / ('rgpt-result-' + preserved_attempt)\n"
             "    preserved_zip = Path('/kaggle/working') / ('rgpt-preserved-' + preserved_attempt + '.zip')\n"
             "    if not preserved_root.is_dir():\n        print('Not present in this session:',preserved_root)\n        continue\n"
             "    if not preserved_zip.exists():\n"
             "        with zipfile.ZipFile(preserved_zip,'x',zipfile.ZIP_DEFLATED) as archive:\n"
             "            for name in ('raw_response.txt','candidates.json','execution.json','output-manifest.json','result.zip'):\n"
             "                path = preserved_root/name\n"
             "                if path.is_file(): archive.writestr(name,path.read_bytes())\n"
             "    print('Download privately using Output browser:',preserved_zip)\n```\n\n")
    for i, (cell, first, description) in enumerate(zip([c for c in notebook['cells'] if c['cell_type'] == 'code'], old, descriptions), 1):
        text += f'## Code cell {i}: REPLACE entire cell\n\nLocate old first line: `{first}`.\n\n{description}\n\n'
        text += 'Place immediately ' + ('ABOVE the staging cell.\n\n' if i == 1 else f'BELOW code cell {i-1} above.\n\n')
        text += '```python\n' + ''.join(cell['source']) + '```\n\n'
        text += ('Success: configuration variables set without error.\n\n' if i == 1 else
                 'Success: printed status READY; stop and download diagnostics on any exception.\n\n' if i in (2, 3) else
                 'Success: GPUs/config displayed; inspect matching T4/profile before continuing.\n\n' if i == 4 else
                 'Success: exit code0 and execution status COMPLETED mean schema-valid proposals only. On nonzero exit, download artifacts and stop; do not retry automatically.\n\n' if i == 5 else
                 'Success: printed debug ZIP path exists in Output browser. Download it privately and stop GPU session. Missing result.zip means no completed runner artifact, not success.\n\n')
    return text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--notebook', type=Path, required=True)
    parser.add_argument('--instructions', type=Path, required=True)
    parser.add_argument('--attempt', default='03')
    args = parser.parse_args()
    notebook = render(args.input, args.attempt)
    for path in (args.notebook, args.instructions):
        if path.exists():
            raise FileExistsError('preserve existing handoff: ' + str(path))
    with args.notebook.open('x', encoding='utf-8') as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)
        f.write('\n')
    args.instructions.write_text(instructions(notebook), encoding='utf-8')
    print(json.dumps(notebook['metadata']['researchgpt'], indent=2))


if __name__ == '__main__':
    main()
