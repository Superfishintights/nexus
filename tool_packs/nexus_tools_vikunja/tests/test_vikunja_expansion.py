from __future__ import annotations
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from pathlib import Path
import sys
import threading
from urllib.error import HTTPError
from email.parser import BytesParser
from email.policy import default
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nexus_tools_vikunja import attachments, client, filters, reactions, teams, webhooks
from nexus_tools_vikunja.client import VikunjaClient, VikunjaError


class Reply:
    def __init__(self, payload: bytes, headers=None):
        self.stream=io.BytesIO(payload)
        self.headers=headers or {}
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def read(self,size=-1): return self.stream.read(size)


class Opener:
    def __init__(self,replies):
        self.replies=iter(replies);self.requests=[]
    def open(self,request,timeout):
        self.requests.append(request)
        reply=next(self.replies)
        if isinstance(reply,Exception):raise reply
        return reply


def fake_client(replies):
    c=VikunjaClient('https://example.test','test-bearer')
    c._opener=Opener(replies)
    return c


@pytest.fixture
def attachment_dir(tmp_path,monkeypatch):
    root=tmp_path/'attachments';root.mkdir(mode=0o700)
    values={'VIKUNJA_ATTACHMENT_DIR':str(root)}
    monkeypatch.setattr(client,'get_setting',lambda key:values.get(key))
    return root,values


def test_patch_saved_filter_and_team_send_only_changed_fields(monkeypatch):
    c=fake_client([Reply(b'{}'),Reply(b'{}')])
    monkeypatch.setattr(filters,'get_client',lambda:c);monkeypatch.setattr(teams,'get_client',lambda:c)
    filters.update_saved_filter(4,{'is_favorite':True})
    teams.update_team(5,{'name':'Planning'})
    assert [(r.method,r.full_url,json.loads(r.data)) for r in c._opener.requests]==[
        ('PATCH','https://example.test/api/v2/filters/4',{'is_favorite':True}),
        ('PATCH','https://example.test/api/v2/teams/5',{'name':'Planning'}),
    ]


def test_team_members_use_username_and_toggle_admin_is_explicit(monkeypatch):
    c=fake_client([Reply(b'{}'),Reply(b''),Reply(b'{}')]);monkeypatch.setattr(teams,'get_client',lambda:c)
    teams.add_team_member(5,'person/name',False)
    teams.remove_team_member(5,'person/name')
    teams.toggle_team_member_admin(5,'person/name')
    assert json.loads(c._opener.requests[0].data)=={'username':'person/name','admin':False}
    assert c._opener.requests[1].full_url.endswith('/teams/5/members/person%2Fname')
    assert c._opener.requests[2].method=='POST' and c._opener.requests[2].full_url.endswith('/person%2Fname/admin')
    assert c._opener.requests[2].data is None


def test_reaction_removal_uses_post_body_and_validates_entity(monkeypatch):
    c=fake_client([Reply(b'{}')]);monkeypatch.setattr(reactions,'get_client',lambda:c)
    reactions.remove_reaction('comments',6,'acknowledged')
    r=c._opener.requests[0]
    assert r.method=='POST' and r.full_url.endswith('/comments/6/reactions/delete')
    assert json.loads(r.data)=={'value':'acknowledged'}
    with pytest.raises(ValueError):reactions.add_reaction('projects',6,'acknowledged')
    with pytest.raises(ValueError):reactions.add_reaction('tasks',6,'a'*21)
    assert len(c._opener.requests)==1


def test_webhook_response_redaction_preserves_request_configuration(monkeypatch):
    fields={'target_url':'https://receiver.test/hook','events':['task.created'],'secret':'signing-secret','basic_auth_user':'hook-user','basic_auth_password':'hook-password'}
    response={**fields,'nested':{'secret':'nested-secret'},'entries':[{'token':'nested-token','id':2}]}
    c=fake_client([Reply(json.dumps(response).encode())]);monkeypatch.setattr(webhooks,'get_client',lambda:c)
    result=webhooks.create_project_webhook(3,fields)
    assert json.loads(c._opener.requests[0].data)==fields
    assert result=={'target_url':fields['target_url'],'events':['task.created'],'nested':{},'entries':[{'id':2}]}
    assert fields['secret']=='signing-secret'


def test_webhook_list_also_redacts_nested_credentials(monkeypatch):
    c=fake_client([Reply(b'{"items":[{"id":1,"secret":"not-for-output","basic_auth_password":"hidden"}],"page":1,"per_page":50,"total":1,"total_pages":1}')])
    monkeypatch.setattr(webhooks,'get_client',lambda:c)
    assert webhooks.list_project_webhooks(1)['items']==[{'id':1}]


def test_error_redacts_echoed_webhook_credentials():
    error=HTTPError('https://example.test',400,'Bad request',{},io.BytesIO(b'{"detail":"signing-secret hook-user hook-password test-bearer"}'))
    c=fake_client([error])
    with pytest.raises(VikunjaError) as raised:c.request('POST','projects/1/webhooks',body={'secret':'signing-secret','basic_auth_user':'hook-user','basic_auth_password':'hook-password'})
    assert not any(s in str(raised.value) for s in ['signing-secret','hook-user','hook-password','test-bearer'])


def test_attachment_actual_multipart_download_and_redirect_boundary(attachment_dir):
    root,values=attachment_dir
    blob=b'\x00\xff\x01attachment-data\r\n'
    (root/'first.bin').write_bytes(blob);(root/'second.txt').write_text('second')
    captured=[]
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            raw=self.rfile.read(int(self.headers['Content-Length']))
            mime=BytesParser(policy=default).parsebytes(('Content-Type: '+self.headers['Content-Type']+'\r\nMIME-Version: 1.0\r\n\r\n').encode()+raw)
            parts=list(mime.iter_parts())
            captured.append(('upload',self.path,self.headers.get('Authorization'),[(p.get_param('name',header='content-disposition'),p.get_filename(),p.get_payload(decode=True)) for p in parts]))
            result=b'{"success":[{"id":7}],"errors":[]}'
            self.send_response(201);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(result)));self.end_headers();self.wfile.write(result)
        def do_GET(self):
            captured.append(('download',self.path,self.headers.get('Authorization')))
            if self.path.endswith('/attachments/8'):
                self.send_response(302);self.send_header('Location','/capture-credentials');self.send_header('Content-Length','0');self.end_headers();return
            self.send_response(200);self.send_header('Content-Type','application/octet-stream');self.send_header('Content-Length',str(len(blob)));self.end_headers();self.wfile.write(blob)
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        c=VikunjaClient(f'http://127.0.0.1:{server.server_port}','test-bearer')
        uploaded=c.upload_attachments(3,['first.bin',str(root/'second.txt')])
        assert uploaded['success'][0]['id']==7
        assert captured[0]==('upload','/api/v2/tasks/3/attachments','Bearer test-bearer',[('files','first.bin',blob),('files','second.txt',b'second')])
        result=c.download_attachment(3,7,'downloaded.bin')
        assert (root/'downloaded.bin').read_bytes()==blob
        assert (root/'downloaded.bin').stat().st_mode&0o077==0
        assert result['size_bytes']==len(blob) and result['sha256']==hashlib.sha256(blob).hexdigest()
        assert result['content_type']=='application/octet-stream'
        assert set(result)=={'task_id','attachment_id','file_path','size_bytes','sha256','content_type'}
        with pytest.raises(VikunjaError) as raised:c.download_attachment(3,8,'redirect.bin')
        assert raised.value.status==302
        assert not (root/'redirect.bin').exists()
        assert not any(entry[1]=='/capture-credentials' for entry in captured)
    finally:
        server.shutdown();server.server_close();thread.join(timeout=2)


def test_upload_total_bound_and_path_boundary_precede_http(attachment_dir,tmp_path):
    root,values=attachment_dir;values['VIKUNJA_MAX_ATTACHMENT_BYTES']='5'
    (root/'first.txt').write_bytes(b'123');(root/'second.txt').write_bytes(b'456')
    outside=tmp_path/'outside';outside.write_bytes(b'secret')
    (root/'escape').symlink_to(outside)
    c=fake_client([])
    with pytest.raises(ValueError,match='exceeds'):c.upload_attachments(1,['first.txt','second.txt'])
    for p in ['../outside',str(outside),'escape']:
        with pytest.raises(ValueError,match='within'):c.upload_attachments(1,[p])
    assert c._opener.requests==[]


def test_download_declared_and_streamed_bounds_remove_partial_file(attachment_dir):
    root,values=attachment_dir;values['VIKUNJA_MAX_ATTACHMENT_BYTES']='5'
    c=fake_client([Reply(b'123456',{'Content-Length':'6'}),Reply(b'123456')])
    for name in ['header.bin','stream.bin']:
        with pytest.raises(ValueError,match='exceeds'):c.download_attachment(1,2,name)
        assert not (root/name).exists()


def test_download_does_not_overwrite_or_accept_path_traversal(attachment_dir):
    root,values=attachment_dir;(root/'existing').write_text('keep')
    c=fake_client([])
    with pytest.raises(ValueError,match='already exists'):c.download_attachment(1,2,'existing')
    for name in ['../outside','/tmp/out','.', 'a/b']:
        with pytest.raises(ValueError,match='simple filename'):c.download_attachment(1,2,name)
    assert (root/'existing').read_text()=='keep' and c._opener.requests==[]


def test_download_incomplete_size_and_transport_failure_remove_partial(attachment_dir):
    root,values=attachment_dir
    class BrokenReply(Reply):
        def read(self,size=-1):
            if self.stream.tell():raise OSError('network failed')
            return super().read(2)
    c=fake_client([Reply(b'123',{'Content-Length':'5'}),BrokenReply(b'1234')])
    with pytest.raises(VikunjaError,match='declared size'):c.download_attachment(1,2,'short.bin')
    with pytest.raises(VikunjaError,match='transport failed'):c.download_attachment(1,2,'broken.bin')
    assert not (root/'short.bin').exists() and not (root/'broken.bin').exists()


def test_attachment_directory_and_limits_are_explicit(attachment_dir):
    root,values=attachment_dir;c=fake_client([])
    root.chmod(0o755)
    with pytest.raises(ValueError,match='private permissions'):c.upload_attachments(1,['file'])
    root.chmod(0o700)
    for value in ['0','-1','bad']:
        values['VIKUNJA_MAX_ATTACHMENT_BYTES']=value
        with pytest.raises(ValueError,match='positive integer'):c.download_attachment(1,2,'new.bin')
    values.clear()
    with pytest.raises(ValueError,match='required'):c.download_attachment(1,2,'new.bin')
    assert c._opener.requests==[]
