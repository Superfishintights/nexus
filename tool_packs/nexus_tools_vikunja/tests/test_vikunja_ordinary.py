from __future__ import annotations

import ast
import importlib
import inspect
import io
import json
from pathlib import Path
import sys
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from nexus_tools_vikunja import miscellaneous, notifications, sessions, settings, subscriptions, time_entries
from nexus_tools_vikunja.client import VikunjaClient, VikunjaError

CONTRACTS = json.loads((ROOT / 'specs/ordinary-tool-contracts.json').read_text())
UUID = '00000000-0000-4000-8000-000000000001'
TIME_FIELDS = {'task_id': 7, 'start_time': '2026-10-04T09:00:00Z', 'end_time': None}


class Reply:
    def __init__(self, value):
        self.value = value
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self): return json.dumps(self.value).encode()


class Opener:
    def __init__(self, value):
        self.value = value
        self.requests = []
    def open(self, request, timeout):
        self.requests.append(request)
        if isinstance(self.value, Exception):
            raise self.value
        return Reply(self.value)


def fake_client(monkeypatch, module, response=None):
    client = VikunjaClient('https://example.test/api/v2', 'test-bearer')
    client._opener = Opener(response if response is not None else {})
    monkeypatch.setattr(module, 'get_client', lambda: client)
    return client


def call_arguments(name):
    cases = {
        'create_time_entry': {'fields': TIME_FIELDS},
        'get_time_entry': {'time_entry_id': 7},
        'update_time_entry': {'time_entry_id': 7, 'fields': {'comment': None}},
        'replace_time_entry': {'time_entry_id': 7, 'fields': TIME_FIELDS},
        'delete_time_entry': {'time_entry_id': 7},
        'list_task_time_entries': {'task_id': 7},
        'list_project_time_entries': {'project_id': 7},
        'set_notification_read': {'notification_id': 7, 'read': False},
        'update_general_settings': {'fields': {'name': None}},
        'replace_general_settings': {'fields': {'language': 'en'}},
        'update_avatar_provider': {'fields': {'avatar_provider': 'default'}},
        'replace_avatar_provider': {'fields': {'avatar_provider': 'default'}},
        'delete_session': {'session_id': UUID},
        'subscribe': {'entity': 'project', 'entity_id': 7},
        'unsubscribe': {'entity': 'task', 'entity_id': 7},
        'duplicate_project': {'project_id': 7, 'fields': {'parent_project_id': 0, 'duplicate_shares': False}},
        'mark_task_read': {'task_id': 7},
    }
    return cases.get(name, {})


@pytest.mark.parametrize('contract', CONTRACTS, ids=lambda c: c['tool'])
def test_all_routes_bodies_and_authentication(contract, monkeypatch):
    module = importlib.import_module(contract['module'])
    name = contract['tool'].split('.')[1]
    function = getattr(module, name)
    arguments = call_arguments(name)
    paged = 'page' in inspect.signature(function).parameters
    response = {'items': [{'id': 9}], 'page': 1, 'per_page': 50, 'total': 1, 'total_pages': 1} if paged else {'id': 9}
    client = fake_client(monkeypatch, module, response)
    function(**arguments, params={'filter_timezone': 'Europe/London'})
    assert len(client._opener.requests) == 1
    request = client._opener.requests[0]
    expected_path = contract['path']
    for placeholder in ('{id}', '{task_id}', '{project_id}', '{notificationid}', '{entityID}', '{projectid}', '{task}'):
        expected_path = expected_path.replace(placeholder, '7')
    expected_path = expected_path.replace('{session}', UUID).replace('{entity}', arguments.get('entity', ''))
    assert urlsplit(request.full_url).path == expected_path
    assert request.method == contract['method']
    assert parse_qs(urlsplit(request.full_url).query)['filter_timezone'] == ['Europe/London']
    assert request.get_header('Authorization') == (None if name == 'get_server_health' else 'Bearer test-bearer')
    expected_body = arguments.get('fields')
    if name == 'set_notification_read': expected_body = {'read': False}
    assert (json.loads(request.data) if request.data is not None else None) == expected_body
    if contract['method'] == 'PATCH':
        assert request.get_header('Content-type') == 'application/merge-patch+json'


@pytest.mark.parametrize('module,name,extra', [
    (time_entries, 'list_time_entries', {}),
    (time_entries, 'list_task_time_entries', {'task_id': 2}),
    (time_entries, 'list_project_time_entries', {'project_id': 3}),
    (notifications, 'list_notifications', {}),
    (sessions, 'list_sessions', {}),
])
def test_pagination_preserves_server_cap_filters_and_redacts(monkeypatch, module, name, extra):
    response = {'items': [{'id': 8, 'refresh_token': 'private', 'read': False}], 'page': 2, 'per_page': 20, 'total': 45, 'total_pages': 3}
    client = fake_client(monkeypatch, module, response)
    params = {'filter': 'task_id = 2', 'page': 999, 'q': 'old', 'expand': ['user', 'task']}
    result = getattr(module, name)(**extra, page=2, per_page=50, query='current', params=params)
    assert result == {'items': [{'id': 8, 'refresh_token': '[redacted]', 'read': False}], 'pagination': {'page': 2, 'per_page': 20, 'total': 45, 'total_pages': 3, 'next_page': 3}}
    query = parse_qs(urlsplit(client._opener.requests[0].full_url).query)
    assert query == {'page': ['2'], 'per_page': ['50'], 'q': ['current'], 'filter': ['task_id = 2'], 'expand': ['user', 'task']}
    assert params['page'] == 999 and params['q'] == 'old'


@pytest.mark.parametrize('fields', [{}, {'task_id': 1, 'project_id': 2}, {'task_id': True}, {'project_id': -1}, {'task_id': '1'}])
def test_time_entry_create_and_replace_reject_ambiguous_ownership(monkeypatch, fields):
    client = fake_client(monkeypatch, time_entries)
    for function, args in [(time_entries.create_time_entry, (fields,)), (time_entries.replace_time_entry, (1, fields))]:
        with pytest.raises(ValueError): function(*args)
    assert client._opener.requests == []


def test_time_entry_project_timer_and_sparse_patch_preserve_fields(monkeypatch):
    client = fake_client(monkeypatch, time_entries)
    fields = {'project_id': 4, 'task_id': 0, 'start_time': '2026-10-04T10:00:00Z', 'end_time': None}
    time_entries.create_time_entry(fields)
    time_entries.update_time_entry(5, {'end_time': None})
    assert [json.loads(r.data) for r in client._opener.requests] == [fields, {'end_time': None}]
    assert fields['end_time'] is None


def test_redaction_nested_settings_preserves_input_and_ordinary_data(monkeypatch):
    payload = {'name': 'Jay', 'frontend_settings': {'theme': 'dark', 'password': 'private', 'nested': [{'ACCESS_TOKEN': 'private2', 'id': 7}]}}
    client = fake_client(monkeypatch, settings, payload)
    result = settings.update_general_settings(payload)
    assert json.loads(client._opener.requests[0].data) == payload
    assert result == {'name': 'Jay', 'frontend_settings': {'theme': 'dark', 'password': '[redacted]', 'nested': [{'ACCESS_TOKEN': '[redacted]', 'id': 7}]}}
    assert payload['frontend_settings']['password'] == 'private'


def test_session_subscription_and_read_flag_validation_before_http(monkeypatch):
    clients = [fake_client(monkeypatch, module) for module in (sessions, subscriptions, notifications)]
    for invalid in ('', '../other', 'not-a-uuid', 7):
        with pytest.raises(ValueError): sessions.delete_session(invalid)
    for invalid in ('user', 'projects', '../task'):
        with pytest.raises(ValueError): subscriptions.subscribe(invalid, 1)
    with pytest.raises(ValueError): subscriptions.unsubscribe('task', 0)
    with pytest.raises(ValueError): notifications.set_notification_read(1, read='false')
    assert all(client._opener.requests == [] for client in clients)


def test_duplicate_defaults_does_not_request_copying_shares(monkeypatch):
    client = fake_client(monkeypatch, miscellaneous)
    miscellaneous.duplicate_project(7)
    assert json.loads(client._opener.requests[0].data) == {}


@pytest.mark.parametrize('credential_key', ['secret', 'ACCESS_TOKEN', 'refresh_token', 'api_key', 'authorization'])
def test_scope_failure_preserves_status_and_redacts_credentials(monkeypatch, credential_key):
    error = HTTPError('https://example.test', 401, 'Unauthorized', {}, io.BytesIO(b'{"detail":"test-bearer private-secret"}'))
    fake_client(monkeypatch, settings, error)
    with pytest.raises(VikunjaError) as raised:
        settings.update_general_settings({'frontend_settings': {credential_key: 'private-secret'}})
    assert raised.value.status == 401
    assert 'test-bearer' not in str(raised.value) and 'private-secret' not in str(raised.value)


def test_operation_inventory_matches_deployed_spec_and_valid_examples():
    spec = json.loads((ROOT / 'specs/live-v2-2.7.0.json').read_text())
    pairs = {(c['method'], c['path'].removeprefix('/api/v2')) for c in CONTRACTS}
    assert len(CONTRACTS) == len(pairs) == 27
    for method, path in pairs:
        assert method.lower() in spec['paths'][path]
    prior = set()
    for name in ('scoped-v2.json', 'expansion-scoped-v2.json'):
        for path, methods in json.loads((ROOT / 'specs' / name).read_text())['paths'].items():
            prior.update((method.upper(), path.removeprefix('/api/v2')) for method in methods if method.upper() in {'GET', 'POST', 'PUT', 'PATCH', 'DELETE'})
    assert not pairs & prior
    for c in CONTRACTS:
        module = importlib.import_module(c['module'])
        name = c['tool'].split('.')[1]
        node = next(n for n in ast.parse(inspect.getsource(module)).body if isinstance(n, ast.FunctionDef) and n.name == name)
        example_kw = next(k for k in node.decorator_list[0].keywords if k.arg == 'examples')
        example = ast.literal_eval(example_kw.value)[0]
        call = ast.parse(example, mode='eval').body
        args = [ast.literal_eval(a) for a in call.args]
        kwargs = {k.arg: ast.literal_eval(k.value) for k in call.keywords}
        inspect.signature(getattr(module, name)).bind(*args, **kwargs)
