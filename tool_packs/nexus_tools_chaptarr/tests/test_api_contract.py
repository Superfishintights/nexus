"""Independent, mocked wire checks against the pinned official API contracts.

The fixture was extracted from Chaptarr's OpenAPI at source revision
 e67374f4b3fed01bbf08f18672add944062fcb49 and the reviewed generation report.
Requests never leave the process. This exercises every generated operation,
including root routes, multipart routes, multi-argument paths and DELETE bodies.
"""
from __future__ import annotations

import ast
from email.message import Message
import importlib
import inspect
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import parse_qs, quote, urlsplit

import pytest

from nexus_tools_chaptarr import client

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'nexus_tools_chaptarr'
CONTRACT = json.loads((Path(__file__).parent / 'fixtures/pinned-api-contract.json').read_text())
OPERATIONS = CONTRACT['operations']
MANIFEST = json.loads((PACKAGE / 'coverage-manifest.json').read_text())
MODULES = {entry['tool']: entry['module'] for entry in MANIFEST['operations']}
DELETE_BODIES = [op for op in OPERATIONS if op['method'] == 'DELETE' and op['request_content_types']]


class Response:
    status = 200

    def __init__(self, data=b'{"contract": "ok"}', content_type='application/json', headers=None):
        self.data = data
        self.headers = Message()
        self.headers['Content-Type'] = content_type
        for key, value in (headers or {}).items():
            self.headers[key] = value

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.data


@pytest.fixture
def transport(monkeypatch):
    requests = []

    def open_request(request, timeout):
        requests.append((request, timeout))
        return Response()

    from types import SimpleNamespace
    monkeypatch.setattr(client.urllib.request, 'build_opener', lambda *args: SimpleNamespace(open=open_request))
    return requests


def argument_name(name):
    import re
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()


def parameter_value(schema):
    if schema.get('enum'):
        return schema['enum'][0]
    if schema.get('type') == 'integer':
        return 73
    if schema.get('type') == 'number':
        return 2.5
    if schema.get('type') == 'boolean':
        return False
    if schema.get('type') == 'array':
        return [parameter_value(schema.get('items', {})), parameter_value(schema.get('items', {}))]
    return 'contract / space? & unicode café'


def wrapper(op):
    module = importlib.import_module('nexus_tools_chaptarr.' + Path(MODULES['chaptarr.' + op['name']]).stem)
    return module, getattr(module, op['name'])


def invoke(op, monkeypatch, **extra):
    module, function = wrapper(op)
    monkeypatch.setattr(module, 'get_client', lambda: client.ChaptarrClient('https://chaptarr.test', 'contract-secret'))
    arguments = {}
    path = op['path']
    for parameter in op['parameters']:
        name = parameter['name']
        if parameter.get('in') != 'path' or '{' + name + '}' not in path:
            continue
        value = 17 if parameter.get('schema', {}).get('type') == 'integer' else 'dir name/cover?#é.png'
        arguments[argument_name(name)] = value
        encoded = quote(str(value), safe='/' if name == 'path' and op['path'] in ('/{path}', '/content/{path}') else '')
        path = path.replace('{' + name + '}', encoded)
    arguments.update(extra)
    return function(**arguments), path


@pytest.mark.parametrize('op', OPERATIONS, ids=lambda op: op['name'])
def test_every_generated_operation_reaches_its_pinned_route(op, monkeypatch, transport):
    params = {p['name']: parameter_value(p.get('schema', {})) for p in op['parameters'] if p.get('in') == 'query'}
    params['contractProbe'] = ['first & value', 'second?value']
    params['contractDisabled'] = False
    params['contractOmitted'] = None
    arguments = {'params': params}
    body = {'ids': [17, 23], 'contract': 'body stays intact'}
    if op['request_content_types'] and 'multipart/form-data' not in op['request_content_types']:
        arguments['body'] = body
    if 'multipart/form-data' in op['request_content_types']:
        arguments['files'] = []
        arguments['form_data'] = {'username': 'contract-user', 'password': 'contract-pass', 'rememberMe': 'on'}
    _, expected_path = invoke(op, monkeypatch, **arguments)
    assert len(transport) == 1
    request, timeout = transport[0]
    assert request.get_method() == op['method']
    assert (urlsplit(request.full_url).path or '/') == expected_path
    # Compare query values on the wire, not merely wrapper forwarding.
    expected_query = {}
    for key, value in params.items():
        items = value if isinstance(value, list) else [value]
        values = ['true' if v is True else 'false' if v is False else str(v) for v in items if v is not None]
        if values:
            expected_query[key] = values
    assert parse_qs(urlsplit(request.full_url).query) == expected_query
    assert request.get_header('X-api-key') == 'contract-secret'
    assert timeout == 30.0
    if 'body' in arguments:
        assert json.loads(request.data) == body
    elif 'form_data' in arguments:
        assert request.get_header('Content-type').startswith('multipart/form-data; boundary=')
        assert b'name="username"' in request.data and b'contract-user' in request.data
    else:
        assert request.data is None


@pytest.mark.parametrize('op', DELETE_BODIES, ids=lambda op: op['name'])
def test_all_eleven_delete_contracts_accept_body(op, monkeypatch, transport):
    assert len(DELETE_BODIES) == 11
    invoke(op, monkeypatch, body={'ids': [1, 2], 'deleteFiles': False})
    request, _ = transport[0]
    assert request.get_method() == 'DELETE'
    assert json.loads(request.data) == {'ids': [1, 2], 'deleteFiles': False}


def test_backup_restore_upload_supplements_missing_openapi_body(monkeypatch, transport, tmp_path):
    op = next(op for op in OPERATIONS if op['name'] == 'create_system_backup_restore_upload')
    assert op['request_content_types'] == []
    upload = tmp_path / 'backup.zip'
    upload.write_bytes(b'PK\x03\x04contract-backup')
    invoke(op, monkeypatch, files=[{'path': str(upload), 'field_name': 'files', 'filename': 'restore.zip', 'content_type': 'application/zip'}], form_data={'restoreConfiguration': True})
    request, _ = transport[0]
    assert request.get_method() == 'POST'
    assert urlsplit(request.full_url).path == '/api/v1/system/backup/restore/upload'
    assert request.get_header('Content-type').startswith('multipart/form-data; boundary=')
    assert b'name="files"; filename="restore.zip"' in request.data
    assert b'Content-Type: application/zip' in request.data
    assert b'PK\x03\x04contract-backup' in request.data
    assert b'name="restoreConfiguration"\r\n\r\ntrue\r\n' in request.data


def test_generated_catalog_has_316_unique_literal_canonical_names():
    from nexus.tool_registry import iter_tools
    for op in OPERATIONS:
        wrapper(op)
    names = ['chaptarr.' + op['name'] for op in OPERATIONS]
    assert len(names) == len(set(names)) == 316
    registered = {tool.name: tool for tool in iter_tools() if tool.name in names}
    assert set(registered) == set(names)
    for op in OPERATIONS:
        filename = PACKAGE / MODULES['chaptarr.' + op['name']]
        assert not filename.name.endswith('_test.py')
        module, function = wrapper(op)
        tool = registered['chaptarr.' + op['name']]
        assert tool.function is function and tool.alias_of is None
        assert str(inspect.signature(function)) == tool.signature
        tree = ast.parse(filename.read_text())
        decorator = next(n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'register_tool')
        values = {keyword.arg: ast.literal_eval(keyword.value) for keyword in decorator.keywords}
        assert values['namespace'] == 'chaptarr'
        assert values['description'] and values['examples']
        assert values['aliases'] == []


def test_pack_imports_all_tools_without_config_or_network():
    script = '''
import os, socket, urllib.request, importlib, pkgutil
for key in list(os.environ):
    if key.startswith('CHAPTARR_'): del os.environ[key]
def forbidden(*args, **kwargs):
    raise AssertionError('Network or configuration side effect during import')
socket.create_connection = forbidden
urllib.request.urlopen = forbidden
import nexus_tools_chaptarr
for entry in pkgutil.iter_modules(nexus_tools_chaptarr.__path__):
    importlib.import_module('nexus_tools_chaptarr.' + entry.name)
'''
    result = subprocess.run([sys.executable, '-c', script], cwd=ROOT.parents[1], capture_output=True, text=True,
                            env={**__import__('os').environ, 'PYTHONPATH': str(ROOT) + ':' + str(ROOT.parents[1])})
    assert result.returncode == 0, result.stderr


def test_packaged_spec_and_manifest_match_independently_pinned_contract():
    import hashlib
    raw = (PACKAGE / 'openapi.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == CONTRACT['spec_sha256']
    assert MANIFEST['source_commit'] == CONTRACT['source_revision']
    assert MANIFEST['documented_operation_count'] == 316
    expected = {(op['method'], op['path']): 'chaptarr.' + op['name'] for op in OPERATIONS}
    actual = {(op['method'], op['path']): op['tool'] for op in MANIFEST['operations']}
    assert len(MANIFEST['operations']) == len(actual) == 316
    assert actual == expected


def test_schema_helpers_return_complete_contract_and_transitive_resources(monkeypatch):
    from nexus_tools_chaptarr.get_api_schema import get_api_operation, get_api_schema
    monkeypatch.setattr(client, 'get_setting', lambda key: (_ for _ in ()).throw(AssertionError('Schema tools cannot need configuration')))
    document = json.loads((PACKAGE / 'openapi.json').read_text())
    schemas = document['components']['schemas']
    index = get_api_schema()
    assert index['schema_count'] == len(schemas)
    assert index['schemas'] == sorted(schemas)
    assert get_api_schema('BookResource')['schema'] == schemas['BookResource']
    assert get_api_schema('#/components/schemas/BookResource')['schema'] == schemas['BookResource']
    operation = get_api_operation('create_book')
    assert operation['tool'] == 'chaptarr.create_book'
    assert operation['operation'] == document['paths']['/api/v1/book']['post']
    assert operation['referenced_schemas']['BookResource'] == schemas['BookResource']
    assert get_api_operation('chaptarr.create_book') == operation
    assert get_api_operation('create_system_backup_restore_upload')['source_supplements']
    json.dumps(index)
    json.dumps(operation)
    with pytest.raises(ValueError, match='Unknown'):
        get_api_schema('UnknownContractSchema')
    with pytest.raises(ValueError, match='Unknown'):
        get_api_operation('unknown_contract_tool')
