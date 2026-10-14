"""Shared TickTick HTTP/configuration. Never expose credential or error bodies."""
from __future__ import annotations

import json
import os
import stat
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from nexus.config import get_setting

API_URL = 'https://api.ticktick.com/open/v1'


class TickTickError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)


def path_id(value: str) -> str:
    if not isinstance(value, str) or not value or value in {'.', '..'}:
        raise ValueError('TickTick identifier must be a nonempty string')
    return urllib.parse.quote(value, safe='')


def token_file() -> Path | None:
    value = get_setting('TICKTICK_TOKEN_FILE')
    return Path(value).expanduser() if value else None


def read_token() -> str:
    configured = get_setting('TICKTICK_ACCESS_TOKEN')
    if configured:
        return str(configured).strip()
    path = token_file()
    if path is None:
        raise TickTickError('Set TICKTICK_ACCESS_TOKEN or TICKTICK_TOKEN_FILE')
    try:
        info = path.stat()
        if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077:
            raise TickTickError('TickTick token file must be a regular private file with mode 0600')
        raw = path.read_text().strip()
        if raw.startswith('{'):
            raw = json.loads(raw).get('access_token', '')
        if not isinstance(raw, str) or not raw:
            raise ValueError('empty token')
        return raw
    except TickTickError:
        raise
    except (OSError, ValueError, TypeError):
        raise TickTickError('Cannot read a valid TickTick access token from the configured file') from None


def save_token(token: str) -> None:
    """Write from the local OAuth helper only. Public tools never accept tokens."""
    path = token_file()
    if path is None:
        raise TickTickError('Set TICKTICK_TOKEN_FILE before OAuth setup')
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temp = path.with_name(path.name + '.new-' + str(os.getpid()))
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(json.dumps({'access_token': token})+'\n')
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch(req: urllib.request.Request, timeout: float) -> Any:
    try:
        with urllib.request.build_opener(_NoRedirect).open(req, timeout=timeout) as response:
            raw = response.read()
        return json.loads(raw) if raw.strip() else None
    except urllib.error.HTTPError as exc:
        status = exc.code
        exc.close()
        raise TickTickError(f'TickTick HTTP {status}', status) from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise TickTickError('TickTick network request failed') from None
    except (ValueError, UnicodeError):
        raise TickTickError('TickTick returned an invalid JSON response') from None


class TickTickClient:
    def __init__(self, token: str | None = None):
        self._token = token or read_token()
        self.timeout = float(get_setting('TICKTICK_TIMEOUT_SECONDS') or 30)
        if not 0 < self.timeout <= 120:
            raise ValueError('TICKTICK_TIMEOUT_SECONDS must be in (0, 120]')

    def request(self, method: str, endpoint: str, params: dict[str, Any] | None = None, body: Any = None) -> Any:
        if endpoint.startswith('/') or '://' in endpoint or '?' in endpoint or '#' in endpoint:
            raise ValueError('Expected a relative TickTick endpoint')
        self._validate(method, endpoint, body)
        url = API_URL + '/' + endpoint
        if params:
            url += '?' + urllib.parse.urlencode(params, doseq=True)
        headers = {'Authorization': 'Bearer '+self._token, 'Accept': 'application/json'}
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers['Content-Type'] = 'application/json'
        return fetch(urllib.request.Request(url, data=data, headers=headers, method=method), self.timeout)

    @staticmethod
    def _validate(method: str, endpoint: str, body: Any) -> None:
        if method != 'POST':
            return
        if endpoint == 'task/completeTasks':
            if not isinstance(body, dict) or not isinstance(body.get('taskIds'), list) or not 1 <= len(body['taskIds']) <= 50:
                raise ValueError('complete_tasks requires taskIds with 1 to 50 IDs; split larger batches')
        if endpoint == 'task/batch':
            if not isinstance(body, dict) or not any(body.get(key) for key in ('add', 'update')):
                raise ValueError('batch_tasks requires nonempty add or update arrays')
            if any(not isinstance(body.get(key, []), list) or len(body.get(key, [])) > 50 for key in ('add', 'update')):
                raise ValueError('Each batch add/update array supports at most 50 tasks')
        if endpoint.startswith('task/') and endpoint.count('/') == 1 and endpoint not in {'task/assign','task/unassign','task/move','task/batch','task/search','task/filter','task/completed','task/undone','task/completeTasks'}:
            if not isinstance(body, dict) or body.get('id') != urllib.parse.unquote(endpoint.split('/')[1]) or not body.get('projectId'):
                raise ValueError('update_task body must contain matching id and projectId')
        if endpoint in {'task', 'project'}:
            required = ('title','projectId') if endpoint == 'task' else ('name',)
            if not isinstance(body, dict) or any(not body.get(key) for key in required):
                raise ValueError('Request body requires '+', '.join(required))

    def get(self, endpoint: str, params=None):
        return self.request('GET', endpoint, params=params)

    def post(self, endpoint: str, body=None, params=None):
        return self.request('POST', endpoint, params=params, body=body)

    def delete(self, endpoint: str, params=None):
        return self.request('DELETE', endpoint, params=params)

    def revoke(self):
        boundary = 'nexus-ticktick-revoke'
        data = ('--'+boundary+'\r\nContent-Disposition: form-data; name="token"\r\n\r\n'+self._token+'\r\n--'+boundary+'--\r\n').encode()
        req = urllib.request.Request('https://api.ticktick.com/oauth/revoke', data=data, headers={'Content-Type':'multipart/form-data; boundary='+boundary}, method='POST')
        return fetch(req, self.timeout)


def get_client() -> TickTickClient:
    # Resolve each call so token-file rotation takes effect without a process restart.
    return TickTickClient()
