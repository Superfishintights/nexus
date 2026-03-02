# Sonarr Full Toolset Plan (With Deprecated Placeholders Only)

## Summary
Implement Sonarr tools from `tools/sonarr/v3.json` with this policy:
1. Register all non-deprecated `/api/v3/*` + `/ping` operations as tools.
2. Create **empty placeholder files** for deprecated operations, but do **not** register them as tools.

Result:
- **221 registered canonical tools** (`sonarr.*`)
- **6 deprecated placeholder files** (non-discoverable, non-runnable)

## Public API / Interface Changes
1. `tools/sonarr/client.py` will be upgraded to support full generated coverage:
- Query arrays with `urlencode(..., doseq=True)`
- `head(...)` support for `/ping`
- Optional API path override for non-`/api/v3` endpoints
- `body: Any` support (dict/list payloads)
- Safe response parsing for JSON/text/empty payloads
2. Sonarr tool modules will move to one-file-per-tool format.
3. Back-compat wrappers/aliases for existing Sonarr names remain available (e.g. `lookup_series`, `add_series`, `run_command`, etc.).

## Tool Definition Format (Canonical)
Each generated tool file uses:
- `@register_tool(namespace="sonarr", description="...", examples=[...])`
- Literal decorator metadata values (for AST discovery)
- Direct call through shared `get_client()`
- Deterministic name from method+path:
- `GET -> get_*`
- `POST -> create_*`
- `PUT -> update_*`
- `DELETE -> delete_*`
- `HEAD -> head_*`
- Path params normalized to `by_<param>`

## Deprecated Placeholder Format
For each deprecated endpoint, generate a file with:
1. Module docstring identifying endpoint and deprecation
2. No `@register_tool` usage
3. No exported callable
4. Optional `TODO` note for future migration/removal decision

This keeps repo traceability without polluting tool discovery.

## Registered Tool Inventory (221)
autotagging (6): create_autotagging, delete_autotagging_by_id, get_autotagging, get_autotagging_by_id, get_autotagging_schema, update_autotagging_by_id  
blocklist (3): delete_blocklist_bulk, delete_blocklist_by_id, get_blocklist  
calendar (2): get_calendar, get_calendar_by_id  
command (4): create_command, delete_command_by_id, get_command, get_command_by_id  
config (22): get_config_downloadclient, get_config_downloadclient_by_id, get_config_host, get_config_host_by_id, get_config_importlist, get_config_importlist_by_id, get_config_indexer, get_config_indexer_by_id, get_config_mediamanagement, get_config_mediamanagement_by_id, get_config_naming, get_config_naming_by_id, get_config_naming_examples, get_config_ui, get_config_ui_by_id, update_config_downloadclient_by_id, update_config_host_by_id, update_config_importlist_by_id, update_config_indexer_by_id, update_config_mediamanagement_by_id, update_config_naming_by_id, update_config_ui_by_id  
customfilter (5): create_customfilter, delete_customfilter_by_id, get_customfilter, get_customfilter_by_id, update_customfilter_by_id  
customformat (8): create_customformat, delete_customformat_bulk, delete_customformat_by_id, get_customformat, get_customformat_by_id, get_customformat_schema, update_customformat_bulk, update_customformat_by_id  
delayprofile (6): create_delayprofile, delete_delayprofile_by_id, get_delayprofile, get_delayprofile_by_id, update_delayprofile_by_id, update_delayprofile_reorder_by_id  
diskspace (1): get_diskspace  
downloadclient (11): create_downloadclient, create_downloadclient_action_by_name, create_downloadclient_test, create_downloadclient_testall, delete_downloadclient_bulk, delete_downloadclient_by_id, get_downloadclient, get_downloadclient_by_id, get_downloadclient_schema, update_downloadclient_bulk, update_downloadclient_by_id  
episode (4): get_episode, get_episode_by_id, update_episode_by_id, update_episode_monitor  
episodefile (7): delete_episodefile_bulk, delete_episodefile_by_id, get_episodefile, get_episodefile_by_id, update_episodefile_bulk, update_episodefile_by_id, update_episodefile_editor  
filesystem (3): get_filesystem, get_filesystem_mediafiles, get_filesystem_type  
health (1): get_health  
history (4): create_history_failed_by_id, get_history, get_history_series, get_history_since  
importlist (11): create_importlist, create_importlist_action_by_name, create_importlist_test, create_importlist_testall, delete_importlist_bulk, delete_importlist_by_id, get_importlist, get_importlist_by_id, get_importlist_schema, update_importlist_bulk, update_importlist_by_id  
importlistexclusion (6): create_importlistexclusion, delete_importlistexclusion_bulk, delete_importlistexclusion_by_id, get_importlistexclusion_by_id, get_importlistexclusion_paged, update_importlistexclusion_by_id  
indexer (11): create_indexer, create_indexer_action_by_name, create_indexer_test, create_indexer_testall, delete_indexer_bulk, delete_indexer_by_id, get_indexer, get_indexer_by_id, get_indexer_schema, update_indexer_bulk, update_indexer_by_id  
indexerflag (1): get_indexerflag  
language (2): get_language, get_language_by_id  
languageprofile (1): get_languageprofile_by_id  
localization (3): get_localization, get_localization_by_id, get_localization_language  
log (5): get_log, get_log_file, get_log_file_by_filename, get_log_file_update, get_log_file_update_by_filename  
manualimport (2): create_manualimport, get_manualimport  
mediacover (1): get_mediacover_by_series_id_by_filename  
metadata (9): create_metadata, create_metadata_action_by_name, create_metadata_test, create_metadata_testall, delete_metadata_by_id, get_metadata, get_metadata_by_id, get_metadata_schema, update_metadata_by_id  
notification (9): create_notification, create_notification_action_by_name, create_notification_test, create_notification_testall, delete_notification_by_id, get_notification, get_notification_by_id, get_notification_schema, update_notification_by_id  
parse (1): get_parse  
ping (2): get_ping, head_ping  
qualitydefinition (5): get_qualitydefinition, get_qualitydefinition_by_id, get_qualitydefinition_limits, update_qualitydefinition_by_id, update_qualitydefinition_update  
qualityprofile (6): create_qualityprofile, delete_qualityprofile_by_id, get_qualityprofile, get_qualityprofile_by_id, get_qualityprofile_schema, update_qualityprofile_by_id  
queue (7): create_queue_grab_bulk, create_queue_grab_by_id, delete_queue_bulk, delete_queue_by_id, get_queue, get_queue_details, get_queue_status  
release (3): create_release, create_release_push, get_release  
releaseprofile (5): create_releaseprofile, delete_releaseprofile_by_id, get_releaseprofile, get_releaseprofile_by_id, update_releaseprofile_by_id  
remotepathmapping (5): create_remotepathmapping, delete_remotepathmapping_by_id, get_remotepathmapping, get_remotepathmapping_by_id, update_remotepathmapping_by_id  
rename (1): get_rename  
rootfolder (4): create_rootfolder, delete_rootfolder_by_id, get_rootfolder, get_rootfolder_by_id  
seasonpass (1): create_seasonpass  
series (10): create_series, create_series_import, delete_series_by_id, delete_series_editor, get_series, get_series_by_id, get_series_by_id_folder, get_series_lookup, update_series_by_id, update_series_editor  
system (11): create_system_backup_restore_by_id, create_system_backup_restore_upload, create_system_restart, create_system_shutdown, delete_system_backup_by_id, get_system_backup, get_system_routes, get_system_routes_duplicate, get_system_status, get_system_task, get_system_task_by_id  
tag (7): create_tag, delete_tag_by_id, get_tag, get_tag_by_id, get_tag_detail, get_tag_detail_by_id, update_tag_by_id  
update (1): get_update  
wanted (4): get_wanted_cutoff, get_wanted_cutoff_by_id, get_wanted_missing, get_wanted_missing_by_id

## Deprecated Placeholder Inventory (6, Not Registered)
1. `create_languageprofile` -> `POST /api/v3/languageprofile`
2. `get_languageprofile` -> `GET /api/v3/languageprofile`
3. `delete_languageprofile_by_id` -> `DELETE /api/v3/languageprofile/{id}`
4. `update_languageprofile_by_id` -> `PUT /api/v3/languageprofile/{id}`
5. `get_languageprofile_schema` -> `GET /api/v3/languageprofile/schema`
6. `get_importlistexclusion` -> `GET /api/v3/importlistexclusion`

## Implementation Steps
1. Add deterministic generator script for Sonarr from `v3.json`.
2. Refactor/replace `tools/sonarr/api.py` with generated one-file-per-tool modules.
3. Generate 221 registered tools + 6 placeholder files.
4. Add/keep compatibility wrappers for existing Sonarr public names.
5. Update client for array params, HEAD, mixed response handling.
6. Validate catalog/runtime behavior with tests and selftest.

## Test Cases and Acceptance Criteria
1. Discovery count:
- `search_tools("sonarr")` includes all 221 canonical names
- Deprecated placeholder names do not appear
2. Catalog integrity:
- No duplicate names
- Each canonical tool has literal decorator metadata
3. Client behavior:
- Array query params encoded correctly
- `/ping` GET and HEAD work with path override
- Mixed response types parse without crashing
4. Backward compatibility:
- Existing Sonarr names still load and execute
5. Repo checks:
- `python -m py_compile tools/sonarr/*.py`
- `pytest -q`
- `python nexus/selftest.py`

## Assumptions and Defaults
1. Scope is fixed to `/api/v3` + `/ping`.
2. Deprecated endpoints are represented only as non-registered placeholders.
3. One-file-per-tool layout is required.
4. Generator output is source-of-truth for future Sonarr spec refreshes.
