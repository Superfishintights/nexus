from __future__ import annotations
import io
import ast
import json
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nexus_tools_vikunja import auth, client, planner, tasks, projects
from nexus_tools_vikunja.client import VikunjaClient, VikunjaError


def test_namespace_metadata_is_literal_and_matches_runtime_package():
    import nexus_tools_vikunja
    tree = ast.parse(Path(nexus_tools_vikunja.__file__).read_text())
    declaration = next(node for node in tree.body if isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Name) and target.id == "NEXUS_NAMESPACES" for target in node.targets
    ))
    metadata = ast.literal_eval(declaration.value)
    assert metadata == nexus_tools_vikunja.NEXUS_NAMESPACES
    assert isinstance(metadata, list) and len(metadata) == 1
    assert metadata[0]["name"] == "vikunja"
    assert metadata[0]["display_name"] == "Vikunja"
    assert isinstance(metadata[0]["description"], str) and metadata[0]["description"]


class Response:
    def __init__(self, payload):
        self.payload = payload
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self): return b'' if self.payload is None else json.dumps(self.payload).encode()


class Opener:
    def __init__(self, payloads):
        self.payloads = iter(payloads)
        self.requests = []
    def open(self, request, timeout):
        self.requests.append(request)
        payload = next(self.payloads)
        if isinstance(payload, Exception): raise payload
        return Response(payload)


def fake_client(payloads):
    c = VikunjaClient('https://example.test/api/v2/', 'test-secret')
    c._opener = Opener(payloads)
    return c


@pytest.mark.parametrize('url,expected', [('https://example.test','https://example.test/api/v2'), ('https://example.test/api/v2/','https://example.test/api/v2'), ('http://example.test/service','http://example.test/service/api/v2')])
def test_url_normalizes_once(url, expected):
    assert VikunjaClient(url).api_url == expected


@pytest.mark.parametrize('url', ['https://user:password@example.test', 'https://example.test/api/v1', 'ftp://example.test', 'https://example.test?token=secret'])
def test_invalid_or_legacy_url_rejected(url):
    with pytest.raises(ValueError): VikunjaClient(url)


def test_query_repeat_arrays_and_false_boolean():
    c = fake_client([{}])
    c.request('GET','tasks',params={'expand':['subtasks','comments'],'filter_include_nulls':False,'q':'a & b','ignored':None})
    query=parse_qs(urlsplit(c._opener.requests[0].full_url).query)
    assert query == {'expand':['subtasks','comments'],'filter_include_nulls':['false'],'q':['a & b']}
    assert c._opener.requests[0].get_header('Authorization')=='Bearer test-secret'


def test_public_health_never_sends_bearer():
    c = fake_client([{'version':'v2.7.0'}])
    c.request('GET','info',authenticated=False)
    assert c._opener.requests[0].get_header('Authorization') is None


def test_page_envelope_and_explicit_truncation():
    c = fake_client([{'items':[{'id':1}], 'page':1, 'per_page':1, 'total':2, 'total_pages':2}])
    result=c.all_pages('tasks',max_pages=1,per_page=1)
    assert result == {'items':[{'id':1}], 'pages_fetched':1,'truncated':True,'next_page':2,'total':2}


def test_empty_null_items_are_valid():
    c = fake_client([{'items':None,'page':1,'per_page':50,'total':0,'total_pages':0}])
    assert c.page('projects')['items']==[]


def test_all_pages_stops_using_server_page_count():
    c = fake_client([{'items':[{'id':1}],'page':1,'per_page':1,'total':2,'total_pages':2}, {'items':[{'id':2}],'page':2,'per_page':1,'total':2,'total_pages':2}])
    assert c.all_pages('tasks',per_page=1)['items']==[{'id':1},{'id':2}]
    assert len(c._opener.requests)==2


def test_api_problem_is_sanitized():
    error=HTTPError('https://example.test',403,'Forbidden',{},io.BytesIO(b'{"detail":"test-secret denied","code":123}'))
    c=fake_client([error])
    with pytest.raises(VikunjaError) as raised:c.request('GET','tasks')
    assert raised.value.status==403 and raised.value.code==123
    assert 'test-secret' not in str(raised.value)
    assert '[redacted]' in str(raised.value)


def test_token_file_permissions_and_rotation(tmp_path,monkeypatch):
    token=tmp_path/'token';token.write_text('first');token.chmod(0o600)
    monkeypatch.setattr(client,'get_setting',lambda key: {'VIKUNJA_URL':'https://example.test','VIKUNJA_TOKEN_FILE':str(token)}.get(key))
    assert client.get_client().token=='first'
    token.write_text('second')
    assert client.get_client().token=='second'
    token.chmod(0o644)
    with pytest.raises(ValueError,match='private permissions'):client.get_client()


def test_new_token_saved_without_secret_in_result(tmp_path,monkeypatch):
    tmp_path.chmod(0o700)
    monkeypatch.setattr(client,'get_setting',lambda key: str(tmp_path) if key=='VIKUNJA_TOKEN_OUTPUT_DIR' else None)
    c=fake_client([{'id':8,'title':'Planner','token':'new-secret'}]);monkeypatch.setattr(auth,'get_client',lambda:c)
    result=auth.create_token({'title':'Planner','permissions':{'tasks':['read_all']}},'planner.token')
    assert 'token' not in result and 'new-secret' not in json.dumps(result)
    saved=tmp_path/'planner.token';assert saved.read_text()=='new-secret\n' and saved.stat().st_mode&0o077==0
    with pytest.raises(ValueError,match='already exists'):auth.create_token({'title':'Planner'},'planner.token')
    assert len(c._opener.requests)==1


def test_failed_token_save_revokes_new_token(tmp_path,monkeypatch):
    tmp_path.chmod(0o700)
    monkeypatch.setattr(client,'get_setting',lambda key:str(tmp_path) if key=='VIKUNJA_TOKEN_OUTPUT_DIR' else None)
    monkeypatch.setattr(auth,'save_created_token',lambda *args: (_ for _ in ()).throw(OSError()))
    c=fake_client([{'id':8,'token':'new-secret'},None]);monkeypatch.setattr(auth,'get_client',lambda:c)
    with pytest.raises(VikunjaError,match='revocation succeeded=True'):auth.create_token({'title':'Planner'},'planner.token')
    assert c._opener.requests[-1].method=='DELETE'
    assert c._opener.requests[-1].full_url.endswith('/tokens/8')


def test_partial_task_update_preserves_unmentioned_fields_on_wire(monkeypatch):
    c=fake_client([{'id':1,'title':'Existing task','done':True}]);monkeypatch.setattr(planner,'get_client',lambda:c)
    result=planner.complete_task(1)
    request=c._opener.requests[0]
    assert request.method=='PATCH' and json.loads(request.data)=={'done':True}
    assert result['title']=='Existing task'


def test_recurring_and_reminder_payloads(monkeypatch):
    c=fake_client([{},{}]);monkeypatch.setattr(planner,'get_client',lambda:c)
    planner.set_task_recurrence(1,86400,2)
    planner.set_task_reminders(1,[{'relative_to':'due_date','relative_period':-900}])
    assert json.loads(c._opener.requests[0].data)=={'repeat_after':86400,'repeat_mode':2}
    with pytest.raises(ValueError):planner.set_task_recurrence(1,10,3)
    with pytest.raises(ValueError):planner.set_task_reminders(1,[{}])
    assert len(c._opener.requests)==2


MARKER='[personal-agent:00000000-0000-0000-0000-000000000001]'

def test_marker_lookup_scans_descriptions_and_reports_cap(monkeypatch):
    c=fake_client([{'items':[{'id':1,'description':'hello '+MARKER},{'id':2,'description':'other'}], 'page':1,'total_pages':2,'per_page':50,'total':3}]);monkeypatch.setattr(planner,'get_client',lambda:c)
    result=planner.find_tasks_by_marker(MARKER,max_pages=1)
    assert [t['id'] for t in result['items']]==[1] and result['truncated'] is True
    with pytest.raises(ValueError):planner.find_tasks_by_marker('personal-agent')


def test_cancel_refuses_marker_mismatch_before_delete(monkeypatch):
    c=fake_client([{'id':1,'description':'User task'}]);monkeypatch.setattr(planner,'get_client',lambda:c)
    with pytest.raises(ValueError,match='no cancellation'):planner.cancel_task(1,MARKER)
    assert len(c._opener.requests)==1


def test_cancel_uses_fresh_read_and_exact_id(monkeypatch):
    c=fake_client([{'id':5,'description':MARKER},None]);monkeypatch.setattr(planner,'get_client',lambda:c)
    assert planner.cancel_task(5,MARKER)['cancelled'] is True
    assert [r.method for r in c._opener.requests]==['GET','DELETE']
    assert all('/tasks/5' in r.full_url for r in c._opener.requests)


def test_subtask_relation_failure_returns_recoverable_created_id(monkeypatch):
    error=HTTPError('https://example.test',403,'Forbidden',{},io.BytesIO(b'{"detail":"Denied"}'))
    c=fake_client([{'id':1,'project_id':2},{'id':3,'project_id':2},error]);monkeypatch.setattr(planner,'get_client',lambda:c)
    result=planner.create_subtask(1,'Prepare notes')
    assert result['partial'] is True and result['created_task']['id']==3
    assert json.loads(c._opener.requests[-1].data)=={'other_task_id':3,'relation_kind':'subtask'}


def test_relation_validates_kind_and_numeric_id(monkeypatch):
    c=fake_client([{}]);monkeypatch.setattr(tasks,'get_client',lambda:c)
    tasks.add_task_relation(1,2,'blocking')
    assert json.loads(c._opener.requests[0].data)=={'other_task_id':2,'relation_kind':'blocking'}
    with pytest.raises(ValueError):tasks.add_task_relation(1,2,'unknown')
    with pytest.raises(ValueError):tasks.add_task_relation(1,True,'related')


def test_username_in_sharing_route_is_encoded(monkeypatch):
    c=fake_client([None]);monkeypatch.setattr(projects,'get_client',lambda:c)
    projects.remove_project_user(1,'bot/name')
    assert c._opener.requests[0].full_url.endswith('/projects/1/users/bot%2Fname')
