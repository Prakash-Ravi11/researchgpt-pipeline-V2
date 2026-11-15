"""One selection schema for the prompt, constrained decoding and validation.

The decoder restricts syntax/IDs, never decides which evidence is scientifically
appropriate. Raw candidates still require independent validation and the host gate.
"""
from copy import deepcopy
import hashlib
from importlib.metadata import version
import json
import re

import jsonschema

CONTRACT_VERSION = 'selection-json-schema-v1'
DECODER_VERSION = '0.11.3'


def response_contract(output_schema):
    encoded = json.dumps(output_schema, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return {'version': CONTRACT_VERSION, 'decoder': 'lm-format-enforcer',
            'decoder_version': DECODER_VERSION, 'grammar': 'selection-schema-regex-v1',
            'schema_sha256': hashlib.sha256(encoded).hexdigest()}


def prompt_schema(output_schema):
    """Losslessly deduplicate repeated ID enums to preserve the context budget."""
    compact = deepcopy(output_schema)
    definitions, names = {}, {}
    for prop in compact['properties'].values():
        ids = prop['items']['properties']['evidence_id']
        key = json.dumps(ids, sort_keys=True)
        if key not in names:
            name = 'evidence_ids_' + str(len(names))
            names[key] = name
            definitions[name] = ids
        prop['items']['properties']['evidence_id'] = {'$ref': '#/$defs/' + names[key]}
    compact['$defs'] = definitions
    return compact


def contract_prompt(output_schema):
    empty = {field: [] for field in output_schema['required']}
    return ('\n\nSelection response contract:\n'
            'Return one JSON object with every required field in the schema order. Each field is [] or an array '
            'containing at most one object. That object has exactly one property: evidence_id. '
            'Copy the complete ID from that field\'s schema enum. Never return metric names, '
            'plain strings, quotations, numbers, additional properties or invented IDs. '
            'If no appropriate evidence is supported, return [] for that field. '
            'Schema compliance is only a proposal, not scientific verification.\n'
            'JSON Schema (references in $defs retain the exact allowed IDs):\n' +
            json.dumps(prompt_schema(output_schema), separators=(',', ':')) +
            '\nEmpty response shape (valid abstention):\n' + json.dumps(empty, separators=(',', ':')))


def contract_messages(messages, output_schema):
    if not messages or messages[0]['role'] != 'system':
        raise ValueError('selection contract requires a system message')
    messages = deepcopy(messages)
    messages[0]['content'] += contract_prompt(output_schema)
    return messages


def validate_contract(request):
    # Legacy immutable packages remain readable; newly exported packages bind
    # the exact schema used in all three places and name the decoder explicitly.
    if 'response_contract' not in request:
        return
    output_schema = request['output_schema']
    if (request['response_contract'] != response_contract(output_schema)
            or request['messages'][0]['role'] != 'system'
            or not request['messages'][0]['content'].endswith(contract_prompt(output_schema))):
        raise ValueError('selection response contract mismatch')


def selection_pattern(output_schema):
    """Compile only our finite ID-selection schema; unsupported shapes fail closed.

    Fixed JSON member order is a valid subset of the schema, never a fact/ID
    choice. Explicit empty-array grammar also avoids LMFE 0.11.3's reproduced
    JsonSchemaParser maxItems=0 first-item loophole. Post-validation is retained.
    """
    fields = output_schema['required']
    if (output_schema.get('type') != 'object' or output_schema.get('additionalProperties') is not False
            or len(fields) != len(set(fields)) or set(fields) != set(output_schema['properties'])):
        raise ValueError('unsupported selection schema')
    ws = r'[ \t\r\n]{0,4}'
    members = []
    for field in fields:
        prop = output_schema['properties'][field]
        ids = prop['items']['properties']['evidence_id']['enum']
        cap = prop.get('maxItems')
        expected = {'type': 'array', 'maxItems': cap, 'items': {'type': 'object',
                    'properties': {'evidence_id': {'type': 'string', 'enum': ids}},
                    'required': ['evidence_id'], 'additionalProperties': False}}
        if prop != expected or cap not in (0, 1) or not ids or any(not isinstance(i, str) for i in ids):
            raise ValueError('unsupported selection field schema')
        item = ''
        if cap == 1:
            choices = '(?:' + '|'.join(re.escape(json.dumps(i, ensure_ascii=True)) for i in ids) + ')'
            item = '(?:' + r'\{' + ws + '"evidence_id"' + ws + ':' + ws + choices + ws + r'\}' + ws + ')?'
        array = r'\[' + ws + item + r'\]'
        members.append(re.escape(json.dumps(field)) + ws + ':' + ws + array)
    return ws + r'\{' + ws + (ws + ',' + ws).join(members) + ws + r'\}' + ws


def schema_prefix(tokenizer, output_schema):
    """Fail closed when the pinned decoder is absent; never use JSON-mode fallback."""
    if version('lm-format-enforcer') != DECODER_VERSION:
        raise RuntimeError('unsupported lm-format-enforcer version')
    from lmformatenforcer import RegexParser
    from lmformatenforcer.integrations.transformers import build_transformers_prefix_allowed_tokens_fn
    jsonschema.Draft202012Validator.check_schema(output_schema)
    return build_transformers_prefix_allowed_tokens_fn(tokenizer, RegexParser(selection_pattern(output_schema)))
