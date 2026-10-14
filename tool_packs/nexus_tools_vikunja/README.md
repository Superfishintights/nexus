# Vikunja tools for Nexus

This Python pack exposes 141 `vikunja.*` tools for Vikunja API v2. It covers 133 of the 197 operations in the deployed specification, plus eight helpers. It is a practical API toolkit with explicit authentication and feature limits. It targets the fresh Vikunja 2.7 service. A URL ending in `/api/v1` is rejected so this pack cannot accidentally write to the legacy API instance.

## Configuration

Install the pack into the same Python environment as Nexus, then add `nexus_tools_vikunja` to the existing `NEXUS_TOOL_PACKAGES` list. Keep the other package names. Reload the Nexus process after changing its package list.

```bash
python -m pip install ./tool_packs/nexus_tools_vikunja
```

| Setting | Meaning |
| --- | --- |
| `VIKUNJA_URL` | Explicit `http://` or `https://` root URL, or a full URL ending in `/api/v2`. A subdirectory deployment is supported. |
| `VIKUNJA_TOKEN` | Bearer API token or a human session JWT used for initial provisioning. Takes precedence over the token file. |
| `VIKUNJA_TOKEN_FILE` | Private file holding one token. Use mode `0600`; group or world permissions are rejected. |
| `VIKUNJA_TIMEOUT_S` | Positive HTTP timeout in seconds. Default `30`. |
| `VIKUNJA_TOKEN_OUTPUT_DIR` | Existing directory with mode `0700` for the `create_token` provisioning tool. Optional for normal operation. |
| `VIKUNJA_ATTACHMENT_DIR` | Existing runtime-local directory with mode `0700` for attachment uploads and downloads. Uploaded files must be inside it. |
| `VIKUNJA_MAX_ATTACHMENT_BYTES` | Positive byte limit for total file data in one upload or one download. Default `20971520`, which is 20 MiB. |

Configuration and the token file are read on each tool call, so rotating a token file does not require a Python restart. The client sends bearer credentials only to the configured endpoint and refuses HTTP redirects. Error messages omit transport details and redact the configured bearer token.

Create API tokens in Vikunja Settings > API Tokens, or bootstrap with a human session credential. `get_routes` returns the instance's exact supported permission groups. Select operation scopes for the required tasks and projects, rather than account settings or password changes. A token's scopes limit operations; its owner's project access determines which projects it can see. Use an account-owner scoped service token when the planner must also see that account's future projects. Use a bot-owned token when isolation into explicitly shared projects is desired.

Bot and token management, and the current-user endpoint, are human-session bootstrap operations. They do not become available merely by granting normal task scopes to an API token. `create_token(fields, output_name)` requires the private output directory and a new filename. It stores the returned token with mode `0600`, returns only metadata and the saved path, and tries to revoke the new token if saving fails. It never returns the secret to the MCP transcript. Keep bootstrap credentials out of the proactive runtime.

## Tools and contracts

The complete tool list, signatures, metadata and API methods are in [specs/tool-contracts.json](specs/tool-contracts.json). The live API operation audit is in [specs/source-coverage.json](specs/source-coverage.json). Tool examples are API shapes, not authorization to act on those example IDs.

| Area | Tools |
| --- | --- |
| Service and identity | `get_info`, `get_health`, `get_server_health`, `get_current_user`, `get_routes`, `search_users` |
| Projects | `list_projects`, `get_project`, `create_project`, `update_project`, `replace_project`, `delete_project`, `duplicate_project` |
| Project collaboration | List/search users, share with a user or team, update their permission, remove direct access. |
| Tasks | List globally, by project or view; read by ID or project index; create, PATCH, full replacement, delete, duplicate, bulk create/update, complete/reopen. |
| Planning | `set_task_recurrence`, `set_task_reminders`, `create_subtask`, `list_all_tasks`, `find_tasks_by_marker`, `cancel_task` |
| Relationships | Add/remove supported directional relations. Vikunja creates/removes the inverse relation. |
| Labels and assignees | Label CRUD; add/remove/replace task labels; list/add/remove/replace task assignees. |
| Comments | Paginated list, read, create, PATCH, full replacement, delete. |
| Views and kanban | View CRUD/PATCH, bucket list/create/replace/delete, grouped bucket tasks, move task to bucket, set task position. |
| Attachments | Paginated metadata, upload one or more runtime-local files, download to a new private file, delete. |
| Reactions | List, add and remove the authenticated user's reaction on a task or comment. |
| Saved filters | Create, read, PATCH, full replacement and delete. The checked API has no saved-filter list endpoint. |
| Webhooks | Project and user webhook list/create/update/delete, plus supported event catalogs. Response credentials are omitted. |
| Teams | Team list/create/read/PATCH/replace/delete, member add/remove, explicit member-admin toggle. |
| Time entries | Global/task/project pagination, read/create/PATCH/replace/delete and stop timer. Requires the server feature and appropriate authentication. |
| Notifications | List, mark one or all read, delete all. Requires notification scopes. |
| Preferences | General settings and avatar provider read/PATCH/replace, available time zones. Requires a human session. |
| Sessions and subscriptions | Session list/revoke and task/project subscribe/unsubscribe. Requires a human session. |
| Task activity | Explicit `mark_task_read` for Vikunja activity. No WhatsApp operation is involved. |
| Provisioning | Bot list/read/create/PATCH/replace/delete, token list/create-to-file/delete. |

Use the PATCH `update_*` tools for ordinary edits. `replace_*` tools use full PUT replacement. Omitted writable fields may reset. Write tools declare `write`, `destructive` or `admin` metadata; reads have `read` metadata.

The main sync contract is:

```python
projects = load_tool("vikunja.list_projects")(page=1, per_page=50)
tasks = load_tool("vikunja.list_tasks")(
    page=1, per_page=50,
    params={"filter": "done = false", "filter_timezone": "Europe/London"},
)
task = load_tool("vikunja.create_task")(
    project_id=123,
    title="Prepare meeting notes",
    fields={
        "description": "[personal-agent:00000000-0000-0000-0000-000000000001]\nSource reference and context.",
        "due_date": "2026-10-10T09:00:00Z",
    },
    params={"format": "markdown"},
)
updated = load_tool("vikunja.update_task")(
    task_id=task["id"], fields={"due_date": "2026-10-11T09:00:00Z"},
)
```

Create tools take a title and optional `fields`. Other resource mutation tools accept the API body as `fields`, unless a planning helper provides explicit arguments. Additional documented query fields go in `params`. Arrays use repeated query parameters, and booleans serialize as lowercase `true` and `false`. Use `format=markdown` for description/comment Markdown exchange when needed.

Paginated list tools return:

```json
{
  "items": [],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 0,
    "total_pages": 0,
    "next_page": null
  }
}
```

The server can cap `per_page`; use its returned pagination values. `list_all_tasks` follows those pages up to `max_pages`, then returns `truncated` and `next_page` explicitly. `find_tasks_by_marker` scans descriptions across the same bounded pages. It does not rely on title search finding description text. A truncated empty result cannot prove that a task does not exist. The exact `[personal-agent:<UUID>]` marker must remain in the task description. `cancel_task(task_id, marker)` fetches that task's current description and refuses deletion on a marker mismatch.

There is no native idempotency-key parameter in the checked API. The caller should search the ownership marker after an uncertain create response before retrying. Marker cancellation verifies ownership immediately before deletion, but is not a transactional compare-and-delete operation.

## Supported behavior and limits

- Recurrence uses `repeat_after` seconds and modes `0`, `1`, `2`. Mode `0` advances prior dates by the interval; mode `1` advances monthly; mode `2` advances from the current date. The v1 prose incorrectly mentions `3`; the enum and v2 schema use `2`. The checked API does not provide RRULE or arbitrary calendar recurrence rules.
- Completing a recurring task may advance its dates and reopen it. Inspect the returned task rather than assuming `done=True` persisted.
- Reminders are task fields. Supply absolute `reminder` timestamps or `relative_to` with `relative_period` seconds. An empty array clears all reminders. API persistence does not prove notification delivery; delivery requires the server's configured notification channels.
- A subtask is a task relation, not a separate child-task resource. `create_subtask` makes two API writes. If relation creation fails, it returns `partial=True` plus `created_task` so the caller can recover without duplicating it.
- Relations support `subtask`, `parenttask`, `related`, `duplicateof`, `duplicates`, `blocking`, `blocked`, `precedes`, `follows`, `copiedfrom`, and `copiedto`. Vikunja enforces relationship cycles and permissions.
- Project sharing uses usernames for users, numeric IDs for teams, and permission values `0` read, `1` read/write, `2` admin. Existing users are required; this pack does not send invitations.
- Buckets belong to a project view. Moving a task into a done bucket can complete it; moving it out can reopen it. Bucket capacity and recurrence can change that outcome.
- `expand=comments` and `comment_count` require comment-read scopes; other expensive expansions can require additional scopes. The scoped token may reject an expansion even when ordinary task reads succeed.
- Exact bucket, task-position, task-duplicate and project-user-search permission keys can depend on the runtime route catalog. Use `get_routes` from the fresh instance; do not invent names from endpoint paths.
- Attachment upload uses multipart form data and accepts 1 to 10 files from `VIKUNJA_ATTACHMENT_DIR`. The byte limit applies to their combined file data. The server can reject individual files while accepting others, so inspect both `success` and `errors` in the returned upload result. The client does not retry.
- Attachment download streams into a new file with mode `0600`. It refuses existing filenames, path traversal and downloads over the byte limit. It removes partial files on failure. The result contains `file_path`, `size_bytes`, `sha256` and `content_type`, with task and attachment IDs. No binary or base64 payload passes through the gateway. An optional image preview size is `sm`, `md`, `lg` or `xl`.
- Attachment paths belong to the Nexus runtime host. A remote Nexus worker cannot read a desktop-local file unless that file is available in its configured attachment directory. Copy the requested input file there before upload. Download metadata names the saved runtime-local file.
- Webhook request fields remain intact, including explicitly supplied signing and basic-auth credentials. Responses omit these fields recursively. Provisioning a webhook is an explicit write and does not prove that delivery works. Project webhook tools use project permissions. User webhook settings may require a human session credential rather than a normal scoped task API token.
- Team member operations use usernames. The member-admin endpoint toggles the current value; it does not set a requested boolean and should not be retried blindly. Team membership appears in `get_team`; the checked API has no separate team-member list endpoint.
- The pack does not implement every API operation or the server CLI. Remaining operations are listed below.
- This pack only implements integrations. It does not start a watcher, enable proactive writes, synchronize calendars or mutate tasks at import time.

## Sources and generation

The official [API v2 documentation](https://vikunja.io/docs/api-v2/) explains verbs, PATCH and envelopes. The runtime-generated [official demo OpenAPI spec](https://try.vikunja.io/api/v2/openapi.json) was fetched on 4 October 2026 and is retained in `specs/upstream-v2.json`. The scoped version contains the requested task-planning, project, collaboration and provisioning endpoints. [Official token-route code](https://github.com/go-vikunja/vikunja/blob/main/pkg/models/api_routes.go) explains the shared v1/v2 permission names and expansion checks.

The nexus-tool-builder bulk generator ran dry-run first. It reported 69 canonical operations, no collisions, no unsupported operations and no guardrail failures. The accepted write phase generated scaffolds. Those scaffolds were consolidated into semantic resource modules. PATCH is not supported by the generator, so the six PATCH operations were tracked separately and implemented explicitly, with eight service/planner helpers. The initial implementation had 83 canonical tools. A second scoped preflight accepted 27 ordinary JSON operations, with zero collisions, unsupported operations or guardrail failures. Two additional PATCH operations and two attachment operations use explicit implementations. The shared client handles bounded multipart and streamed file data. A third preflight accepted 24 ordinary JSON operations with no collisions or guardrail failures. Three PATCH operations were implemented explicitly. The current pack has 141 canonical tools, zero aliases and zero deprecated placeholders.

## Verification

```bash
python3 -m py_compile tool_packs/nexus_tools_vikunja/nexus_tools_vikunja/*.py
.venv/bin/python -m pytest -q tool_packs/nexus_tools_vikunja/tests --import-mode=importlib
python3 /path/to/nexus-tool-builder/scripts/validate_nexus_toolset.py \
  --service-dir tool_packs/nexus_tools_vikunja/nexus_tools_vikunja --namespace vikunja
NEXUS_TOOL_PACKAGES=nexus_tools_vikunja .venv/bin/python nexus/selftest.py
```

Verified locally on 4 October 2026: 84 Vikunja tests pass; compile passes; validator has 141 canonical tools and zero issues/duplicates; Nexus catalog discovers 141 tools with no warnings; all 141 load successfully and attachment search finds the tools; the scoped Nexus self-test passes. Tests cover request encoding, sparse PATCH, pagination/truncation, secret-file permissions and rotation, secret-safe token creation/revocation, marker cancellation boundaries, recoverable subtask failures and literal namespace metadata. Expansion tests also verify real local HTTP multipart upload and streamed download, redirect rejection, byte limits, no overwrites, input/output path boundaries, partial-file cleanup, PATCH methods and nested webhook credential redaction. The additional ordinary tests cover all 27 HTTP routes, authentication headers, sparse updates, server pagination, valid examples and nested credential redaction in both results and error messages. These tests use local fixtures, not live user records.

The default repository self-test failed because its existing environment named unavailable tool packages, including WAHA, Vaultwarden, Playtomic and other installed-service packs. This is separate from the isolated Vikunja catalog and self-test.

Before the ordinary-operation expansion, the tools lane reported 15 passing checks against the fresh deployed API v2 service on 4 October 2026. These checks verified authenticated access, subtasks, blocking relations, reminders, recurrence date advancement and automatic reopening, completion, paginated marker lookup, comments, buckets and marker-checked cancellation. Cleanup of test project 4 and test label 1 was verified. The checks used agent-owned test records and preserved existing user tasks.

Live writes through the 58 newly added operations remain untested. No attachment, reaction, filter, webhook, general-team, notification, settings, session or subscription record was written to the live service during this expansion. No task activity read-state mutation was performed. Notification and webhook delivery remain untested. The source package now declares literal `NEXUS_NAMESPACES` metadata to address the warning from the newer deployed Nexus core. The tools lane owns the wheel rebuild, service reload and live verification of that warning fix.

## Source coverage and remaining operations

The fresh service's API v2 schema identifies version `v2.7.0` and 197 endpoint-method operations. The pack maps 133 direct operations and adds eight helpers, for 141 tools. All 133 operations in the approved scope are implemented. The two extensions add 58 operations to the initial toolkit. [specs/source-coverage.json](specs/source-coverage.json) lists every remaining operation.

The official demo reports 207 operations. Optional public link-share, Unsplash and Todoist/Trello routes appear there but not in the live schema. The live schema includes five two-factor authentication routes absent from the demo. The toolkit uses the live stable schema and does not invent optional routes.

The remaining 64 live operations are outside this scope.

| Remaining group | Operations | Boundary |
| --- | ---: | --- |
| User and account | 20 | Email/password changes, account deletion, CalDAV credentials, two-factor enrollment, avatar files and account export. |
| Administration | 14 | Instance-wide administration and invitation controls. |
| Authentication | 13 | Login, OAuth and credential lifecycle. |
| Migrations | 12 | File imports, migration integrations and their status routes. |
| Project backgrounds | 3 | Background upload, download and removal. |
| Atom feed | 1 | XML feed with its separate HTTP Basic authentication. |
| Native MCP information | 1 | Native server connection information, requiring a human session. |

The official server CLI handles diagnosis, dump/restore, database migrations and repair, mail, user administration and server startup. This API pack does not run server commands or arbitrary shell commands. See the official [CLI documentation](https://vikunja.io/docs/cli/) and [configuration documentation](https://vikunja.io/docs/config-options/). The separate [veans agent CLI](https://vikunja.io/docs/veans/) is not installed by this pack. [CalDAV](https://vikunja.io/help/caldav/) discovery and VTODO operations under `/dav` are outside the OpenAPI count and are not implemented.

## Current runtime availability

The installed API token covers the first extension's available task, attachment, reaction, filter and team route permissions, plus project duplication and task activity mark-read. Public `get_server_health` works without authentication. No permissions or credentials changed during these extensions.

- Notification tools are implemented, but the installed token has no notification permission group. A read-only live list returned 401.
- General settings, avatar provider settings, sessions, time zones and subscriptions require a human session. The server excludes them from API-token scopes. Audited API-token reads returned 401.
- Time tracking requires the server's Pro feature. This instance reports no enabled Pro features. Its route-permission catalog excludes time entries. The current token returns 401 first; valid session authentication would still encounter the disabled feature.
- User webhook settings and bot/token provisioning can also require a human session.

The tools preserve authentication and feature errors. They do not acquire a session, change scopes, enable a paid feature or fall back to another credential. General settings and session responses redact credential fields recursively. Do not replace settings from a redacted readback. Use sparse PATCH for the fields that should change.
