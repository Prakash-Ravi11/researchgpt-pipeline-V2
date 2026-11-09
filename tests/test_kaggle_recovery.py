"""Actual run02 response replay and CPU-only staging/environment recovery tests."""
import copy
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import zipfile

import jsonschema
import pytest

from kaggle.bootstrap import bootstrap_input
from kaggle.environment import check_dependencies, check_profile
from pipeline.extraction.clients import parse_object
from pipeline.extraction.prompt import FIELDS
from pipeline.extraction.selection import SYSTEM
from pipeline.inference.packages import create_input, create_result, digest, import_result, validate_input, write_json
from scripts.build_recovery_notebook import render, instructions
from tests.test_inference_packages import package
from tests.test_semantic_binding import source_fixture


def code_archive(inp, manifest, members=None):
    members = members or {'kaggle/bootstrap.py': Path('kaggle/bootstrap.py').read_bytes()}
    with zipfile.ZipFile(inp / 'code.zip', 'x', zipfile.ZIP_DEFLATED) as archive:
        for name, content in members.items():
            archive.writestr(name, content)
    blob = (inp / 'code.zip').read_bytes()
    manifest['files']['code.zip'] = {'bytes': len(blob), 'sha256': digest(blob)}
    write_json(inp / 'input-manifest.json', manifest)


def mounted(tmp_path, transport='code.zip.bin', members=None):
    inp, manifest, _, _, _ = package(tmp_path / 'canonical')
    code_archive(inp, manifest, members)
    mount = tmp_path / 'input' / 'datasets' / 'private-owner' / 'fixture'
    mount.mkdir(parents=True)
    for name in ('packet.json', 'request.json', 'runtime.json', 'input-manifest.json'):
        (mount / name).write_bytes((inp / name).read_bytes())
    (mount / transport).write_bytes((inp / 'code.zip').read_bytes())
    # Simulate Kaggle's expanded archive directory; bootstrap must ignore it.
    (mount / 'code').mkdir()
    (mount / 'code/untrusted.py').write_text('raise AssertionError("never execute expanded code")')
    work = tmp_path / 'working'
    work.mkdir()
    return inp, mount, work, digest((inp / 'input-manifest.json').read_bytes())


@pytest.mark.parametrize('transport', ['code.zip.bin', 'code.zip'])
def test_exact_zip_transport_stages_original_manifest_and_safe_source(tmp_path, transport):
    inp, mount, work, sha = mounted(tmp_path, transport)
    staged, source, record = bootstrap_input(tmp_path / 'input', work, sha)
    assert record['transport_names']['code.zip'] == transport
    assert staged != mount and source.name.endswith('-03')
    assert (staged / 'code.zip').read_bytes() == (inp / 'code.zip').read_bytes()
    assert (staged / 'input-manifest.json').read_bytes() == (inp / 'input-manifest.json').read_bytes()
    assert (source / 'kaggle/bootstrap.py').read_bytes() == Path('kaggle/bootstrap.py').read_bytes()
    assert not (source / 'untrusted.py').exists()
    validate_input(staged, sha)
    for name in ('rgpt-result-01', 'rgpt-result-02', 'rgpt-inference-env'):
        (work / name).mkdir()
        (work / name / 'historical.txt').write_text('keep')
    with pytest.raises(FileExistsError):
        bootstrap_input(tmp_path / 'input', work, sha)
    assert all((work / name / 'historical.txt').read_text() == 'keep'
               for name in ('rgpt-result-01', 'rgpt-result-02', 'rgpt-inference-env'))


def test_bin_tampering_is_not_hidden_by_fallback_or_manifest_edit(tmp_path):
    inp, mount, work, sha = mounted(tmp_path)
    (mount / 'code.zip').write_bytes((inp / 'code.zip').read_bytes())
    data = bytearray((mount / 'code.zip.bin').read_bytes())
    data[-1] ^= 1
    (mount / 'code.zip.bin').write_bytes(data)
    with pytest.raises(ValueError, match='hash mismatch'):
        bootstrap_input(tmp_path / 'input', work, sha)
    assert not list(work.iterdir())


def test_retained_manifest_hash_and_unique_input_are_mandatory(tmp_path):
    _, mount, work, sha = mounted(tmp_path)
    with pytest.raises(ValueError, match='found 0'):
        bootstrap_input(tmp_path / 'input', work, '0' * 64)
    duplicate = tmp_path / 'input/duplicate'
    duplicate.mkdir()
    (duplicate / 'input-manifest.json').write_bytes((mount / 'input-manifest.json').read_bytes())
    with pytest.raises(ValueError, match='found 2'):
        bootstrap_input(tmp_path / 'input', work, sha)


@pytest.mark.parametrize('member', ['../escape.py', '/absolute.py', 'C:relative.py', 'C:\\escape.py', '.'])
def test_safe_extraction_rejects_unsafe_members_even_with_matching_hash(tmp_path, member):
    _, _, work, sha = mounted(tmp_path, members={member: b'bad'})
    with pytest.raises(ValueError, match='unsafe code archive member'):
        bootstrap_input(tmp_path / 'input', work, sha)
    assert not list(work.iterdir())


def test_complete_actual_saved_response_has_twelve_violations_not_only_metrics():
    raw = Path('tests/fixtures/qwen3_failed_run_02_raw.txt').read_bytes()
    assert digest(raw) == '842dcf34f28772df33624991c0f76084160e1772576a2cd6436ed822459f4b39'
    exact_schema = json.loads(Path('tests/fixtures/qwen3_failed_run_02_schema.json').read_text())
    data = parse_object(raw.decode())
    errors = list(jsonschema.Draft202012Validator(exact_schema).iter_errors(data))
    assert len(errors) == 12 and {e.path[0] for e in errors} == set(FIELDS)
    assert sum(e.validator == 'type' for e in errors) == 11
    assert data['metrics'] == ['BLEU score', 'training cost']
    assert all(isinstance(v, str) for values in data.values() for v in values)
    # A genuine permitted source-ID proposal is schema-valid, not a label repair.
    _, _, bundle, _ = source_fixture()
    valid = {f: [] for f in FIELDS}
    assert bundle.bundle_id in exact_schema['properties']['metrics']['items']['properties']['evidence_id']['enum']
    valid['metrics'] = [{'evidence_id': bundle.bundle_id}]
    jsonschema.validate(valid, exact_schema)
    valid['metrics'] = [{'evidence_id': 'span:other-paper:1@0:10'}]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(valid, exact_schema)


@pytest.mark.parametrize('status,expected', [('FAILED', 'remote_inference_not_completed'),
                                          ('COMPLETED', 'remote_output_schema_invalid')])
def test_full_actual_response_never_imports_as_verified_even_if_claimed_completed(tmp_path, status, expected):
    inp, _, _, runtime, _ = package(tmp_path)
    _, _, request, _ = validate_input(inp)
    raw = Path('tests/fixtures/qwen3_failed_run_02_raw.txt').read_bytes()
    data = parse_object(raw.decode())
    execution = {'status': status, 'requested_model': runtime['requested_model'],
                 'generation': runtime['generation'], 'quantization': runtime['quantization'],
                 'response_contract': request['response_contract'], 'finish_reason': 'eos',
                 'prompt_tokens': 1776, 'generated_tokens': 349, 'runtime_seconds': 88.69490617500014,
                 'execution_kind': 'saved_response_replay_fixture', 'metrics_are_new_measurements': False}
    remote = tmp_path / 'failed-response-copy'
    create_result(remote, inp, raw, data, execution)
    out = import_result(inp, remote, output_root=tmp_path / 'retained')
    assert out.status == 'EXTRACTION_FAILED' and out.errors[0]['code'] == expected
    assert all(v.verification_state == 'FAILED' for vs in out.fields.values() for v in vs)
    assert (remote / 'raw_response.txt').read_bytes() == raw
    assert (tmp_path / 'retained/raw_response.txt').read_bytes() == raw


def test_profile_is_specific_and_never_upgrades_base_torch_or_numpy():
    profile = json.loads(Path('kaggle/runtime-cu130.json').read_text())
    facts = {'python_version': '3.13.0', 'torch_version': '2.11.0+cu130', 'torch_cuda': '13.0',
             'packages': copy.deepcopy(profile['overlay_pins'])}
    check_profile(profile, facts)
    for key, value in [('torch_version', '2.8.0+cu126'), ('torch_cuda', '12.6'), ('python_version', '3.9.0')]:
        with pytest.raises(RuntimeError):
            check_profile(profile, {**facts, key: value})
    facts['packages']['bitsandbytes'] = '0.47.0'
    with pytest.raises(RuntimeError, match='bitsandbytes'):
        check_profile(profile, facts)
    pins = dict(line.split('==') for line in Path(profile['requirements_file']).read_text().splitlines()
                if line and not line.startswith('#'))
    assert pins == profile['overlay_pins'] and not {'torch', 'numpy'} & set(pins)


def test_overlay_transitive_dependencies_are_checked_without_install_fallback():
    distributions = {'root': SimpleNamespace(version='1.0', requires=['dependency>=2']),
                     'dependency': SimpleNamespace(version='2.0', requires=[])}
    assert check_dependencies(['root==1.0'], distributions.__getitem__)['dependency'] == '2.0'
    distributions['dependency'].version = '1.0'
    with pytest.raises(RuntimeError, match='incompatible active dependency'):
        check_dependencies(['root==1.0'], distributions.__getitem__)


def test_environment_failure_writes_diagnostics_without_running_model(tmp_path, monkeypatch):
    import kaggle.environment as environment
    runtime = tmp_path / 'runtime.json'
    write_json(runtime, {'environment_profile': {}})
    report = tmp_path / 'environment.json'
    def reject(*args, **kwargs):
        raise RuntimeError('planned profile mismatch')
    monkeypatch.setattr(environment, 'verify_environment', reject)
    monkeypatch.setattr(sys, 'argv', ['environment', '--runtime', str(runtime), '--overlay', str(tmp_path), '--report', str(report)])
    with pytest.raises(SystemExit) as exc:
        environment.main()
    data = json.loads(report.read_text())
    assert exc.value.code == 2 and data['status'] == 'FAILED'
    assert data['error'] == 'planned profile mismatch' and data['python_executable'] == sys.executable


def test_generated_notebook_uses_packaged_bootstrap_and_one_integrated_overlay_setup(tmp_path):
    original, _, packet, runtime, _ = package(tmp_path / 'base')
    profile = json.loads(Path('kaggle/runtime-cu130.json').read_text())
    requirements = Path(profile['requirements_file']).read_bytes()
    profile['requirements_sha256'] = digest(requirements)
    runtime['environment_profile'] = profile
    inp = tmp_path / 'profile-input'
    req = json.loads((original / 'request.json').read_text())
    manifest = create_input(inp, packet, [{'role': 'system', 'content': SYSTEM}, req['messages'][-1]], runtime)
    code_archive(inp, manifest, {'kaggle/bootstrap.py': Path('kaggle/bootstrap.py').read_bytes(),
                               profile['requirements_file']: requirements})
    notebook = render(inp)
    code = [c for c in notebook['cells'] if c['cell_type'] == 'code']
    assert len(code) == 6
    for cell in code:
        assert cell['outputs'] == [] and cell['execution_count'] is None
        compile(''.join(cell['source']), 'notebook', 'exec')
    assert Path('kaggle/bootstrap.py').read_text() in ''.join(code[1]['source'])
    setup = ''.join(code[2]['source'])
    assert "rgpt_python = Path(sys.executable)" in setup
    assert "'--target'" in setup and "'--no-deps'" in setup and "'venv'" not in setup
    assert "'--upgrade'" not in setup and 'kaggle.environment' in setup
    assert notebook['metadata']['researchgpt']['attempt'] == '03'
    procedure = instructions(notebook)
    assert 'REPLACE entire cell' in procedure and notebook['metadata']['researchgpt']['input_manifest_sha256'] in procedure
    # Matching source-ID proposals still require matching runtime metadata and gate.
    _, _, request, _ = validate_input(inp)
    data = {f: [] for f in FIELDS}
    data['metrics'] = [{'evidence_id': packet['bundles'][0]['bundle_id']}]
    execution = {'status': 'COMPLETED', 'requested_model': runtime['requested_model'],
                 'generation': runtime['generation'], 'quantization': runtime['quantization'],
                 'response_contract': request['response_contract'], 'finish_reason': 'eos',
                 'prompt_tokens': 1, 'generated_tokens': 1, 'runtime_seconds': 1.0,
                 'execution_kind': 'controlled_metadata_fixture', 'metrics_are_measured': False}
    remote = tmp_path / 'missing-environment-profile'
    create_result(remote, inp, json.dumps(data), data, execution)
    assert import_result(inp, remote).errors[0]['code'] == 'remote_environment_profile_mismatch'
    execution['environment_profile'] = profile
    remote = tmp_path / 'matching-environment-profile'
    create_result(remote, inp, json.dumps(data), data, execution)
    accepted = import_result(inp, remote).fields['metrics'][0]
    assert accepted.verification_state == 'VERIFIED' and accepted.review_status == 'needs_human_review'
