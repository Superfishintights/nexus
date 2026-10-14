"""Materialize the approved 27-operation modules from the deployed API reference.

The guarded generator preflight/write scaffolds are recorded separately. This
step gives routes semantic names and the shared client's pagination/PATCH rules.
It must not overwrite any existing target module.
"""
from __future__ import annotations
import json
from pathlib import Path

root = Path(__file__).parents[1]
spec = json.loads((root/'specs/live-v2-2.7.0.json').read_text())
# module, canonical function, method, API path, signature, endpoint, dispatch
operations = [
('time_entries','list_time_entries','GET','/time-entries','page: int = 1, per_page: int = 50, query: str | None = None, params: dict[str, Any] | None = None',"'time-entries'",'page'),
('time_entries','create_time_entry','POST','/time-entries','fields: dict[str, Any], params: dict[str, Any] | None = None',"'time-entries'",'time_fields'),
('time_entries','get_time_entry','GET','/time-entries/{id}','time_entry_id: int, params: dict[str, Any] | None = None',"f'time-entries/{positive_id(time_entry_id)}'",'request'),
('time_entries','update_time_entry','PATCH','/time-entries/{id}','time_entry_id: int, fields: dict[str, Any], params: dict[str, Any] | None = None',"f'time-entries/{positive_id(time_entry_id)}'",'patch'),
('time_entries','replace_time_entry','PUT','/time-entries/{id}','time_entry_id: int, fields: dict[str, Any], params: dict[str, Any] | None = None',"f'time-entries/{positive_id(time_entry_id)}'",'time_fields'),
('time_entries','delete_time_entry','DELETE','/time-entries/{id}','time_entry_id: int, params: dict[str, Any] | None = None',"f'time-entries/{positive_id(time_entry_id)}'",'request'),
('time_entries','stop_timer','POST','/time-entries/timer/stop','params: dict[str, Any] | None = None',"'time-entries/timer/stop'",'request'),
('time_entries','list_task_time_entries','GET','/tasks/{task_id}/time-entries','task_id: int, page: int = 1, per_page: int = 50, query: str | None = None, params: dict[str, Any] | None = None',"f'tasks/{positive_id(task_id)}/time-entries'",'page'),
('time_entries','list_project_time_entries','GET','/projects/{project_id}/time-entries','project_id: int, page: int = 1, per_page: int = 50, query: str | None = None, params: dict[str, Any] | None = None',"f'projects/{positive_id(project_id)}/time-entries'",'page'),
('notifications','list_notifications','GET','/notifications','page: int = 1, per_page: int = 50, query: str | None = None, params: dict[str, Any] | None = None',"'notifications'",'page'),
('notifications','mark_all_notifications_read','POST','/notifications','params: dict[str, Any] | None = None',"'notifications'",'request'),
('notifications','delete_all_notifications','DELETE','/notifications','params: dict[str, Any] | None = None',"'notifications'",'request'),
('notifications','set_notification_read','PUT','/notifications/{notificationid}','notification_id: int, read: bool = True, params: dict[str, Any] | None = None',"f'notifications/{positive_id(notification_id)}'",'read_flag'),
('settings','get_general_settings','GET','/user/settings/general','params: dict[str, Any] | None = None',"'user/settings/general'",'request'),
('settings','update_general_settings','PATCH','/user/settings/general','fields: dict[str, Any], params: dict[str, Any] | None = None',"'user/settings/general'",'patch'),
('settings','replace_general_settings','PUT','/user/settings/general','fields: dict[str, Any], params: dict[str, Any] | None = None',"'user/settings/general'",'fields'),
('settings','get_avatar_provider','GET','/user/settings/avatar/provider','params: dict[str, Any] | None = None',"'user/settings/avatar/provider'",'request'),
('settings','update_avatar_provider','PATCH','/user/settings/avatar/provider','fields: dict[str, Any], params: dict[str, Any] | None = None',"'user/settings/avatar/provider'",'patch'),
('settings','replace_avatar_provider','PUT','/user/settings/avatar/provider','fields: dict[str, Any], params: dict[str, Any] | None = None',"'user/settings/avatar/provider'",'fields'),
('settings','list_timezones','GET','/user/timezones','params: dict[str, Any] | None = None',"'user/timezones'",'request'),
('sessions','list_sessions','GET','/user/sessions','page: int = 1, per_page: int = 50, query: str | None = None, params: dict[str, Any] | None = None',"'user/sessions'",'page'),
('sessions','delete_session','DELETE','/user/sessions/{session}','session_id: str, params: dict[str, Any] | None = None',"f'user/sessions/{path_text(session_uuid(session_id))}'",'request'),
('subscriptions','subscribe','POST','/subscriptions/{entity}/{entityID}','entity: str, entity_id: int, params: dict[str, Any] | None = None',"f'subscriptions/{subscription_entity(entity)}/{positive_id(entity_id)}'",'request'),
('subscriptions','unsubscribe','DELETE','/subscriptions/{entity}/{entityID}','entity: str, entity_id: int, params: dict[str, Any] | None = None',"f'subscriptions/{subscription_entity(entity)}/{positive_id(entity_id)}'",'request'),
('miscellaneous','duplicate_project','POST','/projects/{projectid}/duplicate','project_id: int, fields: dict[str, Any] | None = None, params: dict[str, Any] | None = None',"f'projects/{positive_id(project_id)}/duplicate'",'optional_fields'),
('miscellaneous','mark_task_read','PUT','/tasks/{task}/read','task_id: int, params: dict[str, Any] | None = None',"f'tasks/{positive_id(task_id)}/read'",'request'),
('miscellaneous','get_server_health','GET','/health','params: dict[str, Any] | None = None',"'health'",'public'),
]
assert len(operations) == 27
modules={};contracts=[]
for module,name,method,path,signature,endpoint,dispatch in operations:
    op=spec['paths'][path][method.lower()]
    description=op.get('summary','')+'. '+op.get('description','')
    if method=='PUT' and 'fields:' in signature:
        description+=' Full replacement can reset omitted fields. Prefer the partial update tool for sparse changes.'
    if method=='PATCH':
        description+=' Uses JSON Merge Patch: send only changed fields, including explicit null when needed.'
    if module=='sessions':
        description+=' The server requires suitable user authentication; the configured API token may be refused. Credential fields are redacted from responses.'
    if module=='settings':
        description+=' Credential fields in nested settings are redacted from responses; do not replace settings from a redacted readback.'
    if name=='duplicate_project':
        description+=' fields accepts parent_project_id and duplicate_shares. Sharing is not copied unless explicitly requested.'
    if name=='set_notification_read':
        description+=' read=True marks it read; read=False marks it unread.'
    if name=='create_time_entry':
        description+=' fields requires exactly one positive task_id or project_id. Set start_time and end_time; end_time=null starts a running timer.'
    query_contract=[{'name':q['name'],'description':q.get('description',''),'schema':q.get('schema',{})} for q in op.get('parameters',[]) if q.get('in')=='query']
    if query_contract:
        description+=' Query parameters: '+json.dumps(query_contract,separators=(',',':'))
    body_contract=op.get('requestBody',{})
    if body_contract:
        description+=' Request body schema: '+json.dumps(body_contract,separators=(',',':'))
    cls='read' if method=='GET' else 'destructive' if method=='DELETE' else 'write'
    if name=='delete_session':cls='admin'
    example_args={'create_time_entry': 'fields={"task_id":1,"start_time":"2026-10-04T09:00:00Z","end_time":None}', 'get_time_entry': 'time_entry_id=1', 'update_time_entry': 'time_entry_id=1, fields={"comment":"Planning"}', 'replace_time_entry': 'time_entry_id=1, fields={"task_id":1,"start_time":"2026-10-04T09:00:00Z","end_time":"2026-10-04T09:30:00Z"}', 'delete_time_entry': 'time_entry_id=1', 'list_task_time_entries': 'task_id=1', 'list_project_time_entries': 'project_id=1', 'set_notification_read': 'notification_id=1, read=True', 'update_general_settings': 'fields={"language":"en"}', 'replace_general_settings': 'fields={"language":"en","timezone":"Europe/London"}', 'update_avatar_provider': 'fields={"avatar_provider":"default"}', 'replace_avatar_provider': 'fields={"avatar_provider":"default"}', 'delete_session': 'session_id="00000000-0000-4000-8000-000000000001"', 'subscribe': 'entity="task", entity_id=1', 'unsubscribe': 'entity="task", entity_id=1', 'duplicate_project': 'project_id=1, fields={"parent_project_id":0,"duplicate_shares":False}', 'mark_task_read': 'task_id=1'}
    example='load_tool("vikunja.'+name+'")('+example_args.get(name,'')+')'
    lines=['@register_tool(', '    namespace="vikunja",', '    description='+json.dumps(description)+',','    examples=['+repr(example)+'],','    tool_class='+repr(cls)+',','    aliases=[],',')','def '+name+'('+signature+') -> Any:','    '+repr(method+' /api/v2'+path+'. '+op.get('description',''))]
    if dispatch=='read_flag':
        lines+=['    if not isinstance(read, bool):','        raise ValueError("read must be a boolean")']
    lines+=['    client = get_client()']
    if dispatch=='page':
        call="client.page("+endpoint+", page=page, per_page=per_page, params={**(params or {}), **({'q': query} if query is not None else {})})"
    else:
        call='safe_request(client, '+repr(method)+', '+endpoint+', params=params'
        if dispatch in {'fields','patch'}:call+=', body=fields_object(fields)'
        elif dispatch=='time_fields':call+=', body=time_entry_fields(fields)'
        elif dispatch=='optional_fields':call+=', body=fields_object(fields) if fields is not None else {}'
        elif dispatch=='read_flag':call+=", body={'read':read}"
        elif dispatch=='public':call+=', authenticated=False'
        if dispatch=='patch':call+=", headers={'Content-Type':'application/merge-patch+json'}"
        call+=')'
    lines+=['    return safe_response('+call+')','','']
    modules.setdefault(module,[]).extend(lines)
    contracts.append({'tool':'vikunja.'+name,'method':method,'path':'/api/v2'+path,'signature':'('+signature+')','class':cls,'module':'nexus_tools_vikunja.'+module,'description':description})
for module,lines in modules.items():
    path=root/'nexus_tools_vikunja'/(module+'.py')
    if path.exists():raise SystemExit('Refusing to overwrite existing module: '+str(path))
    header=['"""Approved Vikunja API v2 ordinary operations, derived from deployed v2.7.0."""','from __future__ import annotations','from typing import Any','from nexus.tool_registry import register_tool','from .client import get_client, positive_id, path_text','from ._ordinary import safe_response, safe_request, fields_object, time_entry_fields, subscription_entity, session_uuid','','']
    path.write_text('\n'.join(header+lines))
(root/'specs/ordinary-tool-contracts.json').write_text(json.dumps(contracts,indent=2)+'\n')
print('Materialized27 semantic wrappers in6 new modules')
