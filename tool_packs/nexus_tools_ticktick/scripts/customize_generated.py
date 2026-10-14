"""Convert the guarded generated inventory to the installed package contracts."""
import json
from pathlib import Path
import re

root = Path(__file__).parents[1]
report = json.loads((root/'spec/generation-report.json').read_text())
spec = json.loads((root/'spec/openapi.json').read_text())
pkg = root/'nexus_tools_ticktick'
pkg.mkdir(exist_ok=True)
names = {
'Get Countdowns':'list_countdowns','Get Focuses By Time Range':'list_focus','Get Focus By Focus ID':'get_focus','Delete Focus':'delete_focus',
'Get All Habits':'list_habits','Get Habit Check-Ins':'list_habit_checkins','Get Habit Sections':'list_habit_sections','Get Habit By Habit ID':'get_habit','Update Habit':'update_habit','Create Or Update Habit Check-In':'upsert_habit_checkin',
'Get User Preferences':'get_preferences','Get User Project':'list_projects','Get Project Groups':'list_project_groups','Update Project Group':'update_project_group','Delete Project Group':'delete_project_group',
'Get Project By ID':'get_project','Update Project':'update_project','Delete Project':'delete_project','Get Columns':'list_columns','Create Column':'create_column','Update Column':'update_column','Get Project With Data':'get_project_data','Get Project Members':'list_project_members',
'Get Task By Project ID And Task ID':'get_task','Delete Task':'delete_task','Add Task Comment':'add_task_comment','Delete Task Comment':'delete_task_comment','Get Task Comments':'list_task_comments','Complete Task':'complete_task',
'Get Tags':'list_tags','Assign Task':'assign_task','Batch Create or Update Tasks':'batch_tasks','Complete Multiple Tasks':'complete_tasks','List Completed Tasks':'list_completed_tasks','Filter Tasks':'filter_tasks','Move Task':'move_tasks','Search Tasks':'search_tasks','Unassign Task':'unassign_task','List Undone Tasks':'list_undone_tasks','Update Task':'update_task'}
contracts=[]
for op in report['canonical']:
    name=names.get(op['summary'],op['name'])
    text=(root/'_generation/ticktick'/op['filename']).read_text()
    text=text.replace(op['name'], name)
    read_posts = {'get_preferences','list_completed_tasks','filter_tasks','list_undone_tasks','search_tasks'}
    tool_class = 'read' if op['method']=='GET' or name in read_posts else 'destructive' if op['method']=='DELETE' else 'write'
    text = text.replace('    namespace="ticktick",', '    namespace="ticktick",\n    tool_class='+repr(tool_class)+',')
    text=text.replace('from .client import get_client','from .client import get_client, path_id')
    for param,_ in op['path_params']:
        text=text.replace('{'+param+'}', '{path_id('+param+')}')
    desc=spec['paths'][op['path']][op['method'].lower()]['description']
    description = op['summary']+'. '+op['method']+' '+op['path']+'.\n\n'+desc
    text = re.sub(r'    description=.*?,\n', lambda _: '    description='+json.dumps(description)+',\n', text)
    doc=op['method']+' '+op['path']+'.\n\n'+desc
    text=re.sub(r'    """'+re.escape(op['method'])+r' .*?"""', lambda _: '    '+repr(doc), text)
    endpoint = op['path'].removeprefix('/open/v1/')
    for original, (param, _) in zip(re.findall(r'{([^}]+)}', endpoint), op['path_params']):
        endpoint = endpoint.replace('{'+original+'}', '{path_id('+param+')}')
    expression = 'f'+repr(endpoint) if op['path_params'] else repr(endpoint)
    text = re.sub(r'(return client\.\w+\()(?:f)?[\"\'][^\n]*?[\"\'](?=,)', lambda m: m[1]+expression, text)
    (pkg/(name+'.py')).write_text(text)
    contracts.append({'tool':'ticktick.'+name,'method':op['method'],'path':op['path'],'path_arguments':[p[0] for p in op['path_params']],'request_contract':desc})
(pkg/'__init__.py').write_text('"""TickTick Open API tools. No import-time network or credential loading."""\n')
(root/'spec/contracts.json').write_text(json.dumps(contracts,indent=2)+'\n')
print(f'{len(contracts)} endpoint tools copied with semantic names')
