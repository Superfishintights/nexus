"""Shared HTTP behavior that endpoint contract tests cannot establish alone."""
from __future__ import annotations

import base64
from email.message import Message
import io
import json
from types import SimpleNamespace
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

import pytest

from nexus_tools_chaptarr import client


class Response:
    status = 200

    def __init__(self, data, content_type='application/json', **headers):
        self.data = data
        self.headers = Message()
        self.headers['Content-Type'] = content_type
        for key, value in headers.items():
            self.headers[key.replace('_', '-')] = value

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.data


def fake_client(monkeypatch, result, **kwargs):
    requests = []

    def open_request(request, timeout):
        requests.append((request, timeout))
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(client.urllib.request, 'build_opener', lambda *args: SimpleNamespace(open=open_request))
    instance = client.ChaptarrClient('https://chaptarr.test', 'test-secret', **kwargs)
    return instance, requests


@pytest.mark.parametrize('data,media_type,expected', [
    (b'{"name":"contract"}', 'application/json', {'name': 'contract'}),
    (b'[1,2]', 'application/problem+json', [1, 2]),
    (b'Chaptarr log line\n', 'text/plain; charset=utf-8', 'Chaptarr log line\n'),
    (b'BEGIN:VCALENDAR\r\n', 'text/calendar', 'BEGIN:VCALENDAR\r\n'),
    (b'', 'application/json', None),
])
def test_json_text_calendar_and_empty_responses(monkeypatch, data, media_type, expected):
    instance, _ = fake_client(monkeypatch, Response(data, media_type))
    result = instance.get('system/status')
    assert result == expected
    json.dumps(result)


@pytest.mark.parametrize('media_type', ['image/png', 'image/jpeg', 'application/zip', 'application/octet-stream'])
def test_binary_downloads_are_lossless_json_serializable(monkeypatch, media_type):
    payload = b'\x00\xff\xfe\x89binary\r\n'
    instance, _ = fake_client(monkeypatch, Response(payload, media_type, Content_Disposition='attachment; filename="backup.zip"'))
    result = instance.get('mediacover/17/cover.jpg')
    assert result['encoding'] == 'base64'
    assert base64.b64decode(result['data']) == payload
    assert result['size_bytes'] == len(payload)
    assert result['content_type'] == media_type
    assert result['content_disposition'] == 'attachment; filename="backup.zip"'
    json.dumps(result)


def test_invalid_utf8_declared_as_text_preserves_binary(monkeypatch):
    instance, _ = fake_client(monkeypatch, Response(b'\xff\xfe', 'text/plain'))
    result = instance.get('log/file')
    assert base64.b64decode(result['data']) == b'\xff\xfe'
    json.dumps(result)


def test_head_returns_serializable_status_and_headers(monkeypatch):
    instance, requests = fake_client(monkeypatch, Response(b'', ETag='"contract"'))
    result = instance.head('ping', api_path='')
    assert result['status_code'] == 200 and result['headers']['ETag'] == '"contract"'
    assert requests[0][0].get_method() == 'HEAD'
    json.dumps(result)


@pytest.mark.parametrize('base,endpoint,prefix,expected', [
    ('https://host.test', 'book', None, '/api/v1/book'),
    ('https://host.test/api/v1/', 'book', None, '/api/v1/book'),
    ('https://host.test/chaptarr/', 'book', None, '/chaptarr/api/v1/book'),
    ('https://host.test', '/api/v1/book', None, '/api/v1/book'),
    ('https://host.test/api/v1', 'ping', '', '/ping'),
    ('https://host.test/chaptarr/api/v1', 'ping', '', '/chaptarr/ping'),
])
def test_base_path_and_api_prefix_are_applied_once(base, endpoint, prefix, expected):
    instance = client.ChaptarrClient(base, 'key')
    assert urlsplit(instance._build_url(endpoint, prefix)).path == expected


@pytest.mark.parametrize('endpoint', ['https://other.test/books', '//other.test/books', 'book/../settings', 'book/%2e%2e/settings', 'books#fragment'])
def test_endpoint_cannot_redirect_key_or_traverse_path(endpoint):
    instance = client.ChaptarrClient('https://host.test', 'key')
    with pytest.raises(ValueError):
        instance._build_url(endpoint)


def test_query_repeat_arrays_false_zero_and_embedded_query(monkeypatch):
    instance, requests = fake_client(monkeypatch, Response(b'{}'), timeout_s=7.5)
    instance.get('book?existing=value', params={'ids': [1, 2], 'enabled': False, 'empty': None, 'page': 0, 'q': 'a & b'})
    request, timeout = requests[0]
    assert parse_qs(urlsplit(request.full_url).query) == {'existing': ['value'], 'ids': ['1', '2'], 'enabled': ['false'], 'page': ['0'], 'q': ['a & b']}
    assert timeout == 7.5
    assert request.get_header('X-api-key') == 'test-secret'
    assert 'test-secret' not in request.full_url


@pytest.mark.parametrize('verb', ['post', 'put', 'patch', 'delete', 'get'])
def test_json_bodies_keep_false_empty_arrays_and_null(monkeypatch, verb):
    instance, requests = fake_client(monkeypatch, Response(b'{}'))
    getattr(instance, verb)('book', body={'enabled': False, 'ids': [], 'optional': None})
    request, _ = requests[0]
    assert request.get_method() == verb.upper()
    assert request.get_header('Content-type') == 'application/json'
    assert json.loads(request.data) == {'enabled': False, 'ids': [], 'optional': None}


def test_login_form_urlencoding_preserves_credentials_without_url_exposure(monkeypatch):
    instance, requests = fake_client(monkeypatch, Response(b'{}'))
    instance.post('login', api_path='', form_data={'username': 'a & b', 'password': 'test? pass', 'rememberMe': True})
    request, _ = requests[0]
    assert request.get_header('Content-type') == 'application/x-www-form-urlencoded'
    assert parse_qs(request.data.decode()) == {'username': ['a & b'], 'password': ['test? pass'], 'rememberMe': ['true']}
    assert urlsplit(request.full_url).path == '/login' and not urlsplit(request.full_url).query


def test_multipart_repeated_fields_binary_content_and_local_path(monkeypatch, tmp_path):
    upload = tmp_path / 'archive.zip'
    upload.write_bytes(b'\x00\xffcontract')
    instance, requests = fake_client(monkeypatch, Response(b'{}'))
    instance.post('system/backup/restore/upload', files=[{'local_path': str(upload)}], form_data={'tag': ['first', 'second'], 'disabled': False, 'ignored': None})
    request, _ = requests[0]
    assert request.data.count(b'name="tag"') == 2
    assert b'name="files"; filename="archive.zip"' in request.data
    assert b'\x00\xffcontract' in request.data
    assert b'name="disabled"\r\n\r\nfalse' in request.data
    assert b'ignored' not in request.data


@pytest.mark.parametrize('files', [[{}], [{'path': '/nonexistent/chaptarr-test-upload'}]])
def test_invalid_upload_files_fail_before_network(monkeypatch, files):
    instance, requests = fake_client(monkeypatch, Response(b'{}'))
    with pytest.raises(ValueError):
        instance.post('system/backup/restore/upload', files=files)
    assert requests == []


def test_json_and_multipart_cannot_be_combined(monkeypatch):
    instance, requests = fake_client(monkeypatch, Response(b'{}'))
    with pytest.raises(ValueError):
        instance.post('book', body={'id': 1}, files=[])
    assert requests == []


@pytest.mark.parametrize('field', ['field_name', 'filename', 'content_type'])
def test_multipart_header_newlines_rejected_before_network(monkeypatch, tmp_path, field):
    path = tmp_path / 'file.zip'
    path.write_bytes(b'file')
    instance, requests = fake_client(monkeypatch, Response(b'{}'))
    with pytest.raises(ValueError):
        instance.post('upload', files=[{'path': str(path), field: 'injected\r\nheader'}])
    assert requests == []


@pytest.mark.parametrize('status', [400, 401, 403, 404, 429, 500])
def test_http_error_preserves_status_and_redacts_key(monkeypatch, status):
    error = HTTPError('https://chaptarr.test', status, 'Denied', {}, io.BytesIO(b'{"error":"test-secret denied; api_key=another-secret"}'))
    instance, _ = fake_client(monkeypatch, error)
    with pytest.raises(RuntimeError) as raised:
        instance.get('book')
    message = str(raised.value)
    assert str(status) in message
    assert 'test-secret' not in message and 'another-secret' not in message
    assert '[redacted]' in message


@pytest.mark.parametrize('error', [URLError('test-secret failed'), TimeoutError('test-secret timed out'), OSError('test-secret disconnected')])
def test_connection_failures_redact_key(monkeypatch, error):
    instance, _ = fake_client(monkeypatch, error)
    with pytest.raises(RuntimeError) as raised:
        instance.get('book')
    assert 'test-secret' not in str(raised.value)


@pytest.fixture
def configuration(monkeypatch):
    values = {'CHAPTARR_URL': 'https://host.test', 'CHAPTARR_API_KEY': 'first', 'CHAPTARR_TIMEOUT_S': '12'}
    monkeypatch.setattr(client, 'get_setting', values.get)
    monkeypatch.setattr(client, '_default_client', None)
    monkeypatch.setattr(client, '_default_client_key', None)
    return values


def test_configuration_cache_reuses_and_refreshes_url_key_timeout(configuration):
    first = client.get_client()
    assert client.get_client() is first
    assert first.api_key == 'first' and first.timeout_s == 12.0
    for name, value in [('CHAPTARR_URL', 'https://second.test'), ('CHAPTARR_API_KEY', 'second'), ('CHAPTARR_TIMEOUT_S', '3.5')]:
        configuration[name] = value
        second = client.get_client()
        assert second is not first
        first = second
    assert first.base_url == 'https://second.test' and first.api_key == 'second' and first.timeout_s == 3.5


def test_key_file_load_rotation_and_inline_key_precedence(configuration, tmp_path):
    path = tmp_path / 'key'
    path.write_text('  file-first\n')
    configuration.pop('CHAPTARR_API_KEY')
    configuration['CHAPTARR_API_KEY_FILE'] = str(path)
    first = client.get_client()
    assert first.api_key == 'file-first'
    path.write_text('file-second\n')
    assert client.get_client().api_key == 'file-second'
    assert client.get_client() is not first
    configuration['CHAPTARR_API_KEY'] = 'inline-key'
    assert client.get_client().api_key == 'inline-key'


@pytest.mark.parametrize('timeout', ['invalid', '0', '-1', 'nan', 'inf'])
def test_invalid_configured_timeout_fails_before_network(configuration, timeout):
    configuration['CHAPTARR_TIMEOUT_S'] = timeout
    with pytest.raises(ValueError, match='CHAPTARR_TIMEOUT_S'):
        client.get_client()


def test_missing_config_and_unreadable_key_file_do_not_expose_paths(configuration):
    configuration.pop('CHAPTARR_API_KEY')
    with pytest.raises(ValueError, match='CHAPTARR_API_KEY'):
        client.get_client()
    configuration['CHAPTARR_API_KEY_FILE'] = '/nonexistent/private/chaptarr-key'
    with pytest.raises(ValueError) as raised:
        client.get_client()
    assert '/nonexistent/private' not in str(raised.value)


@pytest.mark.parametrize('destination', ['https://other.test/book', 'http://chaptarr.test/book', 'https://chaptarr.test:444/book', 'https://user:pass@chaptarr.test/book'])
def test_redirects_cannot_forward_authentication_to_another_origin(destination):
    request = client.urllib.request.Request('https://chaptarr.test/login', headers={'X-Api-Key': 'test-secret'})
    with pytest.raises(URLError):
        client._SameOriginRedirectHandler().redirect_request(request, None, 302, 'Found', Message(), destination)


def test_real_cookie_handler_retains_login_cookie_and_clears_it_on_logout():
    from urllib.response import addinfourl
    requests = []
    replies = iter([
        (302, {'Location': 'https://chaptarr.test/', 'Set-Cookie': 'session=contract-session; Path=/; HttpOnly; Secure'}),
        (200, {}),
        (200, {}),
        (200, {'Set-Cookie': 'session=; Path=/; Max-Age=0; Secure'}),
        (200, {}),
    ])

    class MockHTTPS(client.urllib.request.HTTPSHandler):
        def https_open(self, request):
            requests.append(request)
            status, headers = next(replies)
            message = Message()
            message['Content-Type'] = 'application/json'
            for key, value in headers.items():
                message[key] = value
            result = addinfourl(io.BytesIO(b'{}'), message, request.full_url, status)
            result.msg = 'Found' if status == 302 else 'OK'
            return result

    instance = client.ChaptarrClient('https://chaptarr.test', 'test-secret')
    instance._opener = client.urllib.request.build_opener(
        client.urllib.request.HTTPCookieProcessor(instance.cookie_jar),
        client._SameOriginRedirectHandler(), MockHTTPS(),
    )
    instance.post('login', api_path='', form_data={'username': 'contract', 'password': 'contract-pass'})
    instance.get('book')
    instance.get('logout', api_path='')
    instance.get('book')
    assert len(requests) == 5
    assert requests[0].get_header('Cookie') is None
    assert requests[1].get_header('Cookie') == 'session=contract-session'
    assert requests[2].get_header('Cookie') == 'session=contract-session'
    assert requests[3].get_header('Cookie') == 'session=contract-session'
    assert requests[4].get_header('Cookie') is None
