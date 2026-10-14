"""TickTick contract/security checks. No live account data or network writes."""
from __future__ import annotations
import importlib
import io
import json
import urllib.error
from pathlib import Path
from unittest.mock import Mock

import pytest
from nexus_tools_ticktick import client, planning, auth

MARKER = '[personal-agent:12345678-1234-1234-1234-123456789abc]'


def test_all_documented_routes_are_encoded_and_dispatched(monkeypatch):
    contracts = json.loads((Path(__file__).parents[1]/'spec/contracts.json').read_text())
    for contract in contracts:
        name = contract['tool'].split('.')[1]
        module = importlib.import_module('nexus_tools_ticktick.'+name)
        transport = Mock()
        monkeypatch.setattr(module, 'get_client', lambda: transport)
        values = {arg:'test/'+arg for arg in contract['path_arguments']}
        expected = contract['path'].removeprefix('/open/v1/')
        import re
        original_args = re.findall(r'{([^}]+)}', expected)
        for original, arg in zip(original_args, contract['path_arguments']):
            expected = expected.replace('{'+original+'}',client.path_id(values[arg]))
        kwargs = {'params': {'limit':10}}
        if contract['method'] == 'POST':
            kwargs['body'] = {'sample':'body'}
        getattr(module,name)(**values,**kwargs)
        getattr(transport,contract['method'].lower()).assert_called_once_with(expected,**kwargs)


def test_token_file_private_and_rotation(monkeypatch, tmp_path):
    token = tmp_path/'token'
    settings = {'TICKTICK_TOKEN_FILE':str(token)}
    monkeypatch.setattr(client,'get_setting',settings.get)
    client.save_token('first-private-token')
    assert token.stat().st_mode & 0o777 == 0o600
    assert client.read_token() == 'first-private-token'
    client.save_token('second-private-token')
    assert client.get_client()._token == 'second-private-token'
    token.chmod(0o644)
    with pytest.raises(client.TickTickError,match='private'):
        client.read_token()


def test_bad_token_json_does_not_expose_content(monkeypatch,tmp_path):
    token=tmp_path/'token'
    token.write_text('{access_token: SECRET_DO_NOT_ECHO}')
    token.chmod(0o600)
    monkeypatch.setattr(client,'get_setting',lambda key:str(token) if key=='TICKTICK_TOKEN_FILE' else None)
    with pytest.raises(client.TickTickError) as caught:
        client.read_token()
    assert 'SECRET_DO_NOT_ECHO' not in str(caught.value)


def test_request_body_and_query_encoding(monkeypatch):
    monkeypatch.setattr(client,'get_setting',lambda key: None)
    captured=[]
    monkeypatch.setattr(client,'fetch',lambda req,timeout: captured.append(req) or {})
    transport=client.TickTickClient(token='private-token')
    transport.post('task',body={'title':'Task','projectId':'p'},params={'tags':['a b','c']})
    req=captured[0]
    assert req.full_url == client.API_URL+'/task?tags=a+b&tags=c'
    assert req.get_header('Authorization') == 'Bearer private-token'
    assert json.loads(req.data) == {'title':'Task','projectId':'p'}


@pytest.mark.parametrize('endpoint,body',[
    ('task/completeTasks',{'taskIds':['x']*51}),
    ('task/batch',{'add':[{}]*51}),
    ('task/batch',{}),
    ('task/task-id',{'id':'other-id','projectId':'p'}),
    ('task',{'title':'missing project'}),
])
def test_unsafe_or_truncated_inputs_rejected(endpoint,body):
    with pytest.raises(ValueError):
        client.TickTickClient._validate('POST',endpoint,body)


def test_http_error_body_and_token_not_exposed(monkeypatch):
    opener=Mock()
    opener.open.side_effect=urllib.error.HTTPError('https://api.ticktick.com',401,'Unauthorized',{},io.BytesIO(b'private-token sensitive response'))
    monkeypatch.setattr(client.urllib.request,'build_opener',lambda *args:opener)
    with pytest.raises(client.TickTickError) as caught:
        client.fetch(client.urllib.request.Request('https://api.ticktick.com'),10)
    assert str(caught.value)=='TickTick HTTP 401'
    assert caught.value.status_code==401


def test_redirect_is_not_followed():
    assert client._NoRedirect().redirect_request(None,None,302,None,None,'https://foreign.example') is None


def test_exact_pagination_boundary_checked(monkeypatch):
    transport=Mock()
    transport.get.side_effect=[[{'id':'a'},{'id':'b'}],[]]
    monkeypatch.setattr(planning,'get_client',lambda:transport)
    result=planning.list_all_projects(page_size=2,max_projects=2)
    assert result['complete'] and result['next_offset'] is None
    assert transport.get.call_args_list[-1].kwargs['params']=={'offset':2,'limit':1}


def test_project_cap_reports_continuation(monkeypatch):
    transport=Mock()
    transport.get.side_effect=[[{'id':'a'}],[{'id':'b'}]]
    monkeypatch.setattr(planning,'get_client',lambda:transport)
    result=planning.list_all_projects(page_size=1,max_projects=1)
    assert not result['complete'] and result['next_offset']==1


@pytest.mark.parametrize('marker',['','owned','[personal-agent:bad-id]'])
def test_invalid_marker_never_fetches_or_deletes(monkeypatch,marker):
    transport=Mock()
    monkeypatch.setattr(planning,'get_client',lambda:transport)
    with pytest.raises(ValueError):
        planning.cancel_task('p','t',marker)
    transport.get.assert_not_called()
    transport.delete.assert_not_called()


def test_cancel_requires_fresh_exact_marker_and_ids(monkeypatch):
    transport=Mock()
    monkeypatch.setattr(planning,'get_client',lambda:transport)
    transport.get.return_value={'id':'t','projectId':'p','content':MARKER}
    assert planning.cancel_task('p','t',MARKER)['deleted']
    transport.get.assert_called_once_with('project/p/task/t')
    transport.delete.assert_called_once_with('project/p/task/t')
    transport.reset_mock()
    transport.get.return_value={'id':'t','projectId':'p','content':'unowned'}
    with pytest.raises(ValueError,match='Refusing'):
        planning.cancel_task('p','t',MARKER)
    transport.delete.assert_not_called()


def test_marker_scan_reports_cap_and_preserves_task_content(monkeypatch):
    transport=Mock()
    task={'id':'t','projectId':'p','content':'Keep this content.\n'+MARKER,'desc':'other'}
    transport.get.return_value={'tasks':[task,{'id':'second'}]}
    monkeypatch.setattr(planning,'get_client',lambda:transport)
    result=planning.find_tasks_by_marker(MARKER,project_ids=['p'],max_tasks=1)
    assert result['truncated'] and not result['complete']
    assert result['tasks'][0]['content']==task['content']
    transport.delete.assert_not_called()
    transport.post.assert_not_called()


def test_completed_scan_reports_provider_cap(monkeypatch):
    transport=Mock()
    transport.get.return_value={'tasks':[]}
    transport.post.return_value=[{'id':str(i)} for i in range(200)]
    monkeypatch.setattr(planning,'get_client',lambda:transport)
    result=planning.find_tasks_by_marker(MARKER,project_ids=['p'],include_completed=True)
    assert result['truncated'] and result['reasons']==['completed_response_cap:p']


def test_health_reports_only_safe_auth_error(monkeypatch):
    monkeypatch.setattr(auth,'get_client',lambda: (_ for _ in ()).throw(client.TickTickError('TickTick HTTP 401',401)))
    assert auth.get_health()=={'ok':False,'authenticated':False,'status_code':401,'error':'TickTick HTTP 401'}


def test_catalog_exposes_contracts_and_correct_safety_classes(monkeypatch):
    from nexus import tool_catalog
    from nexus.test_helpers import configure_tool_packages

    # Read literal registration metadata independently of test import order.
    # Core tests clear the runtime registry after this module is collected.
    configure_tool_packages(monkeypatch, ('nexus_tools_ticktick',))
    catalog = tool_catalog.get_catalog(refresh=True)
    focus = catalog['ticktick.list_focus']
    assert 'from' in focus.description and 'type' in focus.description
    assert focus.tool_class == 'read'
    for name in ('complete_task','complete_tasks','batch_tasks','move_tasks','assign_task','unassign_task'):
        assert catalog['ticktick.'+name].tool_class == 'write'
    assert catalog['ticktick.cancel_task'].tool_class == 'destructive'
    assert catalog['ticktick.revoke_authorization'].tool_class == 'admin'
