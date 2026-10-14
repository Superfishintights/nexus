"""Local-only OAuth helper. Never print codes, access tokens or client secrets.

Run on the machine where the browser runs, then securely install the resulting
0600 token file on the Nexus host. Provider supports authorization_code only;
no undocumented refresh flow is attempted.
"""
from __future__ import annotations

import base64
import hmac
import secrets
import time
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

from nexus.config import get_setting
from .client import TickTickError, fetch, save_token, token_file


def main() -> None:
    client_id = get_setting('TICKTICK_CLIENT_ID')
    client_secret = get_setting('TICKTICK_CLIENT_SECRET')
    redirect_uri = get_setting('TICKTICK_REDIRECT_URI')
    if not client_id or not client_secret or not redirect_uri or not token_file():
        raise TickTickError('Set TICKTICK_CLIENT_ID, TICKTICK_CLIENT_SECRET, TICKTICK_REDIRECT_URI and TICKTICK_TOKEN_FILE')
    redirect = urllib.parse.urlsplit(redirect_uri)
    if redirect.scheme != 'http' or redirect.hostname != '127.0.0.1' or not redirect.port or redirect.query or redirect.fragment:
        raise TickTickError('Local helper needs an exact http://127.0.0.1:PORT/callback registered redirect URI')
    expected_state = secrets.token_urlsafe(32)
    captured = {}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            received = urllib.parse.urlsplit(self.path)
            params = urllib.parse.parse_qs(received.query)
            state = params.get('state',[''])[0]
            valid = received.path == (redirect.path or '/') and hmac.compare_digest(state, expected_state)
            if not valid:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Invalid OAuth callback.')
                return
            if params.get('code'):
                captured['code'] = params['code'][0]
            else:
                captured['error'] = True
            self.send_response(200)
            self.send_header('Content-Type','text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(b'Authorization received. You may close this tab.')

    server = HTTPServer(('127.0.0.1',redirect.port),Handler)
    server.timeout = 1
    authorization_url = 'https://ticktick.com/oauth/authorize?'+urllib.parse.urlencode({'client_id':client_id,'scope':'tasks:read tasks:write','state':expected_state,'redirect_uri':redirect_uri,'response_type':'code'})
    print('Opening TickTick consent in your local browser. Waiting up to five minutes.')
    webbrowser.open(authorization_url)
    deadline = time.monotonic()+300
    try:
        while not captured and time.monotonic() < deadline:
            server.handle_request()
    finally:
        server.server_close()
    if 'code' not in captured:
        raise TickTickError('TickTick authorization was declined or timed out')
    basic = base64.b64encode((client_id+':'+client_secret).encode()).decode()
    data = urllib.parse.urlencode({'code':captured['code'],'grant_type':'authorization_code','scope':'tasks:read tasks:write','redirect_uri':redirect_uri}).encode()
    response = fetch(urllib.request.Request('https://ticktick.com/oauth/token',data=data,headers={'Authorization':'Basic '+basic,'Content-Type':'application/x-www-form-urlencoded'},method='POST'),30)
    if not isinstance(response,dict) or not isinstance(response.get('access_token'),str) or not response['access_token']:
        raise TickTickError('OAuth exchange did not return an access token')
    save_token(response['access_token'])
    print('TickTick credential saved to the configured private token file. Run ticktick.get_health to verify access.')


if __name__ == '__main__':
    main()
