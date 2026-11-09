"""CPU-only contract tests: real schema/decoder/gate, no Qwen model or gold claim."""
import copy
import json
from pathlib import Path
import string
import sys
from types import SimpleNamespace

import jsonschema
import pytest
import torch
from transformers import PreTrainedTokenizerBase

from pipeline.extraction.clients import parse_object
from pipeline.extraction.prompt import FIELDS
from pipeline.extraction.selection import schema
from pipeline.inference.packages import create_result, import_result, validate_input
from pipeline.inference.structured import contract_prompt, prompt_schema, response_contract, schema_prefix, selection_pattern, validate_contract
from tests.test_inference_packages import package, result


class CharacterTokenizer(PreTrainedTokenizerBase):
    """Explicit test double; the real LMFE Transformers adapter supplies filtering."""
    alphabet = string.printable
    eos_token_id = len(alphabet)
    all_special_ids = [eos_token_id]

    def __len__(self):
        return len(self.alphabet) + 1

    def encode(self, text):
        return [self.alphabet.index(c) for c in text]

    def decode(self, ids, skip_special_tokens=False):
        return ''.join(('' if skip_special_tokens else '<eos>') if i == self.eos_token_id
                       else self.alphabet[i] for i in ids)


def decoder_accepts(output_schema, raw):
    tokenizer = CharacterTokenizer()
    allowed = schema_prefix(tokenizer, output_schema)
    prefix = tokenizer.encode('PROMPT')
    for token in tokenizer.encode(raw):
        if token not in allowed(0, torch.tensor(prefix)):
            return False
        prefix.append(token)
    return tokenizer.eos_token_id in allowed(0, torch.tensor(prefix))


def reported_response():
    saved = json.loads(Path('tests/fixtures/qwen3_metrics_contract_failure.json').read_text(encoding='utf-8'))
    response = {f: [] for f in FIELDS}
    response['metrics'] = saved['metrics']
    return response


def test_reported_eos_response_is_not_a_valid_selection_or_repaired(tmp_path):
    inp, _, _, runtime, _ = package(tmp_path)
    _, _, request, _ = validate_input(inp)
    response = reported_response()
    raw = json.dumps(response)
    assert parse_object(raw) == response  # Parser preserves labels; it did not cause them.
    errors = list(jsonschema.Draft202012Validator(request['output_schema']).iter_errors(response))
    assert {e.validator for e in errors} == {'maxItems', 'type'}
    assert not decoder_accepts(request['output_schema'], raw)
    # Deliberately claim completion/verification: neither EOS nor the remote
    # assertion can turn schema-invalid data into verified source evidence.
    execution = {'status': 'COMPLETED', 'execution_kind': 'reported_excerpt_test_fixture',
                 'requested_model': runtime['requested_model'], 'generation': runtime['generation'],
                 'quantization': runtime['quantization'], 'response_contract': request['response_contract'],
                 'finish_reason': 'eos', 'prompt_tokens': 1, 'generated_tokens': 349,
                 'runtime_seconds': 1.0, 'metrics_are_measured': False, 'claimed_verdict': 'VERIFIED'}
    remote = tmp_path / 'reported-excerpt'
    create_result(remote, inp, raw, response, execution)
    out = import_result(inp, remote, output_root=tmp_path / 'preserved')
    assert out.status == 'EXTRACTION_FAILED'
    assert out.errors[0]['code'] == 'remote_output_schema_invalid'
    assert all(v.verification_state == 'FAILED' for values in out.fields.values() for v in values)
    assert (remote / 'raw_response.txt').read_text(encoding='utf-8') == raw
    assert json.loads((remote / 'candidates.json').read_text())['metrics'] == ['BLEU score', 'training cost']


@pytest.mark.parametrize('mutation', ['single_label', 'two_valid_ids', 'unknown_id', 'extra_value', 'wrong_field'])
def test_decoder_and_validator_reject_invalid_selections_without_truncation(tmp_path, mutation):
    inp, _, _, _, bundles = package(tmp_path)
    _, _, request, _ = validate_input(inp)
    eid = bundles[0].bundle_id
    response = {f: [] for f in FIELDS}
    response['metrics'] = [{'evidence_id': eid}]
    if mutation == 'single_label':
        response['metrics'] = ['BLEU score']
    elif mutation == 'two_valid_ids':
        response['metrics'] *= 2
    elif mutation == 'unknown_id':
        response['metrics'][0]['evidence_id'] = 'bundle:not-authorized'
    elif mutation == 'extra_value':
        response['metrics'][0]['value'] = '41.8'
    else:
        response['results'] = [{'evidence_id': next(i for i in request['output_schema']['properties']['metrics']['items']['properties']['evidence_id']['enum'] if i.startswith('span:'))}]
    original = copy.deepcopy(response)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(response, request['output_schema'])
    assert not decoder_accepts(request['output_schema'], json.dumps(response))
    assert response == original


def test_decoder_accepts_real_source_id_then_local_gate_verifies_complete_tuple(tmp_path):
    inp, _, _, runtime, bundles = package(tmp_path)
    _, _, request, _ = validate_input(inp)
    response = {f: [] for f in FIELDS}
    response['results'] = [{'evidence_id': bundles[0].bundle_id}]
    jsonschema.validate(response, request['output_schema'])
    assert decoder_accepts(request['output_schema'], json.dumps(response))
    assert decoder_accepts(request['output_schema'], json.dumps({f: [] for f in FIELDS}))
    assert not decoder_accepts(request['output_schema'], json.dumps(response)[:-1])
    out = import_result(inp, result(tmp_path, inp, runtime, bundles[0].bundle_id))
    value = out.fields['results'][0]
    assert value.verification_state == 'VERIFIED' and value.scientific_tuple['value'] == '41.8'
    assert len(value.source_refs) == 9 and value.review_status == 'needs_human_review'


def test_fields_with_no_authorized_ids_only_allow_empty_arrays():
    output_schema = schema('No authorized source headers')
    response = {f: [] for f in FIELDS}
    assert decoder_accepts(output_schema, json.dumps(response))
    response['metrics'] = [{'evidence_id': 'UNAVAILABLE'}]
    assert not decoder_accepts(output_schema, json.dumps(response))


def test_unsupported_schema_shape_never_falls_back_to_unconstrained_json():
    output_schema = schema('[span:test:1@0:1]\nx')
    output_schema['properties']['metrics']['maxItems'] = 2
    with pytest.raises(ValueError, match='unsupported selection field schema'):
        selection_pattern(output_schema)


@pytest.mark.parametrize('over_budget', [False, True])
def test_runner_passes_constraint_and_still_preserves_invalid_eos_output(tmp_path, monkeypatch, over_budget):
    """Injected CPU model deliberately ignores the mask; post-validation must fail."""
    import transformers
    from kaggle.run_inference import main
    from pipeline.inference.packages import digest, create_input
    from pipeline.extraction.selection import SYSTEM
    inp, _, packet, runtime, _ = package(tmp_path)
    if over_budget:
        request=json.loads((inp/'request.json').read_text())
        runtime=copy.deepcopy(runtime)
        runtime['generation']['context_window']=1
        inp=tmp_path/'limited-input'
        create_input(inp,packet,[{'role':'system','content':SYSTEM},request['messages'][-1]],runtime)
    raw = json.dumps(reported_response())
    tokenizer = CharacterTokenizer()

    class Inputs(dict):
        def __getattr__(self, key):
            return self[key]

        def to(self, device):
            assert device == 'cuda:0'
            return self  # TEST-ONLY: all tensors remain on CPU.

    prompt = tokenizer.encode('PROMPT')
    inputs = Inputs(input_ids=torch.tensor([prompt]))

    class RunnerTokenizer(CharacterTokenizer):
        def apply_chat_template(self, messages, **kwargs):
            assert kwargs['enable_thinking'] is False
            return 'PROMPT'

        def __call__(self, text, **kwargs):
            assert kwargs['add_special_tokens'] is False
            return inputs

    def generate(**kwargs):
        mask = kwargs['prefix_allowed_tokens_fn']
        assert callable(mask)
        assert tokenizer.encode('{')[0] in mask(0, inputs.input_ids[0])
        assert tokenizer.encode('B')[0] not in mask(0, inputs.input_ids[0])
        return torch.tensor([prompt + tokenizer.encode(raw) + [tokenizer.eos_token_id]])

    model = SimpleNamespace(generate=generate, generation_config=SimpleNamespace(eos_token_id=tokenizer.eos_token_id))
    monkeypatch.setattr(transformers.AutoTokenizer, 'from_pretrained', lambda *a, **k: RunnerTokenizer())
    model_loads=[]
    def load_model(*args, **kwargs):
        model_loads.append(True)
        return model
    monkeypatch.setattr(transformers.AutoModelForCausalLM, 'from_pretrained', load_model)
    monkeypatch.setattr(transformers, 'BitsAndBytesConfig', lambda **kwargs: kwargs)
    monkeypatch.setattr(torch.cuda, 'is_available', lambda: True)
    monkeypatch.setattr(torch.cuda, 'mem_get_info', lambda index: (16_000_000_000, 16_000_000_000))
    monkeypatch.setattr(torch.cuda, 'get_device_name', lambda index: 'TEST-ONLY CPU runner fixture')
    for name in ('synchronize', 'reset_peak_memory_stats'):
        monkeypatch.setattr(torch.cuda, name, lambda: None)
    for name in ('max_memory_allocated', 'max_memory_reserved'):
        monkeypatch.setattr(torch.cuda, name, lambda: 0)
    out = tmp_path / 'runner-failure'
    monkeypatch.setattr(sys, 'argv', ['run_inference', '--input', str(inp), '--expected-input-sha256',
                                    digest((inp / 'input-manifest.json').read_bytes()), '--output', str(out)])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2
    execution = json.loads((out / 'execution.json').read_text())
    assert execution['status'] == 'FAILED'
    if over_budget:
        assert not model_loads and execution['error_type']=='ValueError'
        assert execution['finish_reason'] is None and (out/'raw_response.txt').read_bytes()==b''
        assert json.loads((out/'candidates.json').read_text()) is None
    else:
        assert len(model_loads)==1 and execution['error_type']=='ValidationError'
        assert execution['finish_reason'] == 'eos'
        assert (out / 'raw_response.txt').read_text(encoding='utf-8') == raw
        assert json.loads((out / 'candidates.json').read_text())['metrics'] == reported_response()['metrics']
    assert (out / 'result.zip').is_file()
    assert import_result(inp, out).status == 'EXTRACTION_FAILED'


def test_new_prompt_schema_and_decoder_contract_share_the_exact_schema(tmp_path):
    inp, _, _, runtime, bundles = package(tmp_path)
    _, _, request, _ = validate_input(inp)
    validate_contract(request)
    assert request['response_contract'] == response_contract(request['output_schema'])
    assert request['messages'][0]['content'].endswith(contract_prompt(request['output_schema']))
    assert 'a supplied ID' not in request['messages'][0]['content']
    assert request['output_schema'] == schema(request['messages'][-1]['content'])
    compact = prompt_schema(request['output_schema'])
    expanded = copy.deepcopy(compact)
    definitions = expanded.pop('$defs')
    for prop in expanded['properties'].values():
        name = prop['items']['properties']['evidence_id']['$ref'].split('/')[-1]
        prop['items']['properties']['evidence_id'] = definitions[name]
    assert expanded == request['output_schema']  # Identical constraints; no IDs dropped.
    jsonschema.validate({f: [] for f in FIELDS}, compact)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(reported_response(), compact)
    changed = copy.deepcopy(request)
    changed['messages'][0]['content'] = 'Return metric names as strings'
    with pytest.raises(ValueError, match='contract mismatch'):
        validate_contract(changed)
    remote = result(tmp_path, inp, runtime, bundles[0].bundle_id)
    execution = json.loads((remote / 'execution.json').read_text())
    execution.pop('response_contract')
    # Rebuild only this deliberately malformed test result's manifest.
    from pipeline.inference.packages import write_json, digest
    write_json(remote / 'execution.json', execution)
    manifest = json.loads((remote / 'output-manifest.json').read_text())
    content = (remote / 'execution.json').read_bytes()
    manifest['files']['execution.json'] = {'bytes': len(content), 'sha256': digest(content)}
    write_json(remote / 'output-manifest.json', manifest)
    assert import_result(inp, remote).errors[0]['code'] == 'remote_response_contract_mismatch'
