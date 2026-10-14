# TickTick Nexus pack

53 tools cover all 46 Open API operations in the official reference fetched on 4 October 2026, plus authorization checks, token revocation, project pagination, native task hierarchy and planner ownership helpers. All HTTP and credential handling lives in `client.py`. Importing the package makes no network requests.

## Credential setup

The current [official TickTick reference](https://developer.ticktick.com/docs/openapi.md) offers a personal API token. In the [TickTick web app](https://ticktick.com/webapp/), open the avatar menu, Settings, Account, API Token. Create a token and install it directly into a private file on the Nexus host. Do not send it through chat or commit it.

Set `TICKTICK_TOKEN_FILE=/etc/nexus-http/secrets/ticktick-token`. The file must have mode `0600` and be readable by the Nexus service account. It may contain the token as plain text or a JSON object with an `access_token` string. Alternatively set `TICKTICK_ACCESS_TOKEN` in the service's protected environment. An environment token takes precedence. `TICKTICK_TIMEOUT_SECONDS` defaults to 30 and accepts values above zero through 120. Token-file rotation takes effect on the next tool call.

Enable the `nexus_tools_ticktick` package through the existing Nexus package configuration. The parent tools lane owns installation and service reload. Then run `ticktick.get_auth_status` and `ticktick.get_health`. Auth status reports local configuration only. Health makes the documented read-only preferences request and reports authorization success and account time zone. Neither returns credentials.

### Optional OAuth

For an application serving multiple users, register at the [TickTick Developer Center](https://developer.ticktick.com/manage). Register the exact redirect URI `http://127.0.0.1:8765/callback`. Set `TICKTICK_CLIENT_ID`, `TICKTICK_CLIENT_SECRET`, `TICKTICK_REDIRECT_URI` and `TICKTICK_TOKEN_FILE` in a protected local environment. On the machine where the browser runs, execute `python -m nexus_tools_ticktick.oauth_setup`.

The helper binds only to loopback, opens provider consent, verifies a random state, exchanges the code using documented Basic authentication, and writes a private token file. It suppresses callback HTTP logging and prints no code, token or secret. It waits five minutes. Securely install the resulting file on the Nexus host if OAuth runs elsewhere. Public Nexus tools never accept or return access tokens. The API documents authorization-code grants only. The pack does not invent a refresh-token grant or automatic refresh.

The user-only steps are generating a personal token, or signing into TickTick and granting OAuth consent. App registration is needed only for OAuth. A registered local redirect must match the configured redirect exactly.

## Tool contracts

All tool names use `ticktick.`. Endpoint tools take the named path IDs, optional `params` for query values and, for POST, optional `body`. Requests and responses retain TickTick's JSON field names. Literal decorator descriptions and per-tool docstrings contain the official request contract, so Nexus discovery exposes required body and query fields. `spec/contracts.json` lists every endpoint and path argument.

| Area | Tools |
| --- | --- |
| Tasks | `create_task`, `update_task`, `get_task`, `delete_task`, `complete_task`, `complete_tasks`, `batch_tasks`, `move_tasks`, `assign_task`, `unassign_task`, `list_completed_tasks`, `list_undone_tasks`, `filter_tasks`, `search_tasks` |
| Projects | `list_projects`, `get_project`, `get_project_data`, `create_project`, `update_project`, `delete_project`, `list_project_members`, `list_all_projects` |
| Hierarchy and ownership | `set_task_parent`, `find_tasks_by_marker`, `cancel_task` |
| Comments | `list_task_comments`, `add_task_comment`, `delete_task_comment` |
| Groups and board columns | `list_project_groups`, `create_project_group`, `update_project_group`, `delete_project_group`, `list_columns`, `create_column`, `update_column` |
| Tags | `list_tags`, `create_tag` |
| Habits | `list_habits`, `get_habit`, `create_habit`, `update_habit`, `list_habit_sections`, `upsert_habit_checkin`, `list_habit_checkins` |
| Focus and countdowns | `list_focus`, `get_focus`, `create_focus`, `delete_focus`, `list_countdowns` |
| Account | `get_preferences`, `get_auth_status`, `get_health`, `revoke_authorization` |

Examples use the actual Nexus invocation contract.

```python
load_tool('ticktick.list_projects')(params={'offset': 0, 'limit': 100})
load_tool('ticktick.list_all_projects')(page_size=100, max_projects=1000)
load_tool('ticktick.get_project_data')(project_id='project-id')
load_tool('ticktick.create_task')(body={
    'title': 'Planner test',
    'projectId': 'agent-owned-test-project',
    'content': 'Task details\n[personal-agent:12345678-1234-1234-1234-123456789abc]',
    'timeZone': 'Europe/London',
    'dueDate': '2026-10-06T09:00:00+0100',
    'reminders': ['TRIGGER:PT0S'],
    'repeatFlag': 'RRULE:FREQ=WEEKLY;INTERVAL=1',
    'repeatFrom': '2',
    'items': [{'title': 'Checklist step', 'status': 0}]
})
load_tool('ticktick.update_task')('task-id', body={
    'id': 'task-id', 'projectId': 'project-id', 'title': 'Updated title'
})
load_tool('ticktick.set_task_parent')('project-id', 'child-id', 'parent-id')
```

`update_task` requires an `id` that matches the path ID and a `projectId`. The pack rejects larger-than-supported batches before a request. `complete_tasks` supports 1 to 50 task IDs. `batch_tasks` supports at most 50 additions and 50 updates per call. Batch results include per-task errors, so callers must inspect `id2error` rather than treating HTTP success as all tasks succeeding.

### Planner ownership

Store the exact marker `[personal-agent:<UUID>]` verbatim in `content`, while preserving the human task text. The helpers also recognize a marker in checklist `desc`. Empty, arbitrary or malformed markers fail before any API call.

`find_tasks_by_marker(marker, project_ids=None, max_projects=100, max_tasks=5000, include_completed=False)` returns `tasks`, `truncated`, `complete`, `reasons`, `scanned_tasks`, `scanned_project_ids` and `includes_completed`. It scans open tasks from project data. Default project enumeration covers only projects returned by the API. If the inbox is absent from that listing, account-wide absence has not been established. Supply known project IDs when necessary. Completed queries are optional and capped by the provider at 200 per project. Saturated completed responses set `truncated`. A bounded or capped scan never reports authoritative absence through `complete=True`.

`cancel_task(project_id, task_id, marker)` fetches the task again. It requires matching IDs and the exact marker in current `content` or `desc` before deleting. It returns `deleted`, `project_id` and `task_id`. The API has no documented conditional-delete revision parameter, so a concurrent edit between this read and delete cannot be excluded. Existing user tasks without the marker fail the ownership check.

## Documented limits

- Live verification found that TickTick truncates project names above 64 characters. Keep test project names within that limit and retain the returned project ID for cleanup. Store planner ownership markers in task content rather than a project name.
- Checklist `items` are embedded checklist entries with status `0` or `1`. They are distinct from native tasks linked by `parentId`. The Task schema documents setting `parentId` to an empty string to remove hierarchy. `set_task_parent` uses the batch Task schema and verifies both tasks belong to the same project before sending the update.
- Recurrence uses `repeatFlag` and optional `repeatFrom`. The reference defines `0` for the original schedule, `1` for completion-relative calculation, and `2` for calendar recurrence that advances beyond expired occurrences. Reminder triggers are strings. Phone delivery and recurrence release must be tested independently after authorization.
- In the live fixture, updating `reminders` to an empty array did not clear the reminder in the completed-task readback. Clearing reminders through that payload remains unverified. Updating `repeatFlag` to an empty string did clear recurrence in the same fixture. Generic update tools preserve the provider's response semantics.
- Dependencies such as blocks, blocked by, predecessor, successor and arbitrary typed relations are absent from the documented API. A parent relationship is not a dependency. No dependency endpoint is invented.
- Projects support offset/limit pagination. `list_all_projects` returns `projects`, `complete` and `next_offset`, with an extra one-record read at an exact boundary. Completed and filtered task queries cap at 200 with no documented continuation. Undone date ranges may span at most 14 days. Focus ranges above 30 days are adjusted by the server. The pack retains these limits in tool contracts rather than adding unsupported pagination parameters.
- There is no documented incremental change cursor, webhook or account-wide task deletion feed. Reconciliation must combine bounded project snapshots and saved task IDs. Missing items in a truncated scan cannot establish deletion.
- The reference offers tag list/create, column list/create/update, countdown read, habit section read and habit read/create/update/check-in operations. It does not document tag update/delete, column delete, countdown mutation, habit delete or section mutation. Those operations are not exposed.
- Assignment is a real write that can affect another project member. Comments, assignment, completion, cancellation and OAuth revocation must remain subject to the caller's authorization policy. The pack itself does not activate proactive writes.

## Generation and verification

The provider publishes Markdown, not a downloadable OpenAPI specification. `scripts/build_spec.py` derives a 46-operation OpenAPI endpoint inventory from that official source. `spec/openapi.json` records the source and request contract text. It is explicitly a derived inventory rather than a provider-issued machine specification.

The required guarded generator preflight reported 46 canonical operations, zero collisions, zero skipped operations and zero guardrail failures. The write phase generated the same inventory. `scripts/customize_generated.py` applies semantic names, encoded path IDs and request docstrings, including correction of the generator's repeated path-parameter substitution behavior. The shared generic generated client is replaced by the TickTick client. The staged generated package is temporary and is not installed.

```bash
PYTHONPATH=tool_packs/nexus_tools_ticktick .venv/bin/python -m pytest -q tool_packs/nexus_tools_ticktick/tests
python -m compileall -q tool_packs/nexus_tools_ticktick/nexus_tools_ticktick
python /path/to/nexus-tool-builder/scripts/validate_nexus_toolset.py --service-dir tool_packs/nexus_tools_ticktick/nexus_tools_ticktick --namespace ticktick
```

Verified locally: all 46 endpoint paths dispatch to the expected method with encoded IDs, 21 pack tests pass, compilation succeeds, and the strict tool validator finds 53 canonical names with no aliases, placeholders, duplicates or metadata issues. The configured Nexus catalog discovers all 53 tools with no warnings, every tool lazy-loads, and the Nexus selftest passes. Write and destructive operations carry explicit safety classes, including completion, assignment, batch changes, cancellation and revocation.

Live authorization, writes, cleanup, reminder delivery, recurrence release and hierarchy behavior remain untested until credentials are configured. No real user task was mutated during implementation. Live verification must use tagged agent-owned records and clean them up afterward.
