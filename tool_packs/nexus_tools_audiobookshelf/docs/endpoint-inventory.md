# Audiobookshelf endpoint inventory

Inventory frozen before implementation on 2026-08-09.

## Sources and compatibility baseline

- Published API reference: <https://api.audiobookshelf.org/>
- Published API docs source: <https://github.com/audiobookshelf/audiobookshelf-api-docs>
  at commit `a62c7f9d2800d80a16030c3d45f58fe4d09feeee` (2025-07-08).
- Audiobookshelf server source tag `v2.36.0`, commit
  `96d4021a3cd45f67bf374b65abafbe5d73e926b5`, especially
  `server/routers/ApiRouter.js`.
- Live read-only `POST /api/authorize` reports Audiobookshelf `2.36.0`, Docker,
  with an authenticated admin user. `GET /status`, `GET /ping`, and `GET /api/me`
  also succeeded through the TLS-safe direct route.

The published API reference warns that it is out of date. The v2.36.0 server
router is therefore the endpoint-presence authority, while the published docs
remain the request/response semantics source where they agree.

## Included surface

Exactly 60 canonical tools are included: 19 read, 11 write, 21 admin, and 9
destructive. Fifty-nine tools map to live routes and one (`find_duplicate_items`)
is a read-only client-side analysis over the documented library-items route.

| Wave | Tool | Method and route | Class | Rationale |
|---:|---|---|---|---|
| 1 | `get_status` | `GET /status` | read | Server readiness and initialization state |
| 1 | `get_server_info` | `POST /api/authorize` | admin | Version, source, settings, and authorized-user context |
| 1 | `get_me` | `GET /api/me` | read | Current user and permissions |
| 1 | `list_libraries` | `GET /api/libraries` | read | Library/folder discovery |
| 1 | `get_library` | `GET /api/libraries/{library_id}` | read | Library detail and optional filter data |
| 1 | `list_library_items` | `GET /api/libraries/{library_id}/items` | read | Paginated/sorted/filtered book and item inventory |
| 1 | `search_library` | `GET /api/libraries/{library_id}/search` | read | Local title/author/series search |
| 1 | `get_library_stats` | `GET /api/libraries/{library_id}/stats` | read | Library health and size statistics |
| 1 | `get_library_filter_data` | `GET /api/libraries/{library_id}/filterdata` | read | Missing-metadata and issue maintenance inputs |
| 1 | `get_library_item` | `GET /api/items/{item_id}` | read | Full item/media/metadata detail |
| 2 | `find_duplicate_items` | derived from `GET /api/libraries/{library_id}/items` | read | Duplicate candidates by path, ASIN, ISBN, or normalized title+author |
| 2 | `search_books` | `GET /api/search/books` | read | Metadata-provider book search |
| 2 | `search_covers` | `GET /api/search/covers` | read | Cover-provider search |
| 2 | `list_library_series` | `GET /api/libraries/{library_id}/series` | read | Series inventory |
| 2 | `get_series` | `GET /api/series/{series_id}` | read | Series detail |
| 2 | `list_library_authors` | `GET /api/libraries/{library_id}/authors` | read | Author inventory |
| 2 | `get_author` | `GET /api/authors/{author_id}` | read | Author detail |
| 2 | `search_authors` | `GET /api/search/authors` | read | Metadata-provider author search |
| 2 | `list_filesystem_paths` | `GET /api/filesystem` | admin | Server-side folder discovery for library setup |
| 2 | `list_tasks` | `GET /api/tasks` | admin | Background maintenance/task visibility |
| 3 | `upload_media` | `POST /api/upload` multipart | write | Import new media from allowlisted local paths |
| 3 | `update_library_item_media` | `PATCH /api/items/{item_id}/media` | write | Amend book/media metadata |
| 3 | `upload_library_item_cover` | `POST /api/items/{item_id}/cover` multipart | write | Upload a local cover safely |
| 3 | `update_library_item_cover` | `PATCH /api/items/{item_id}/cover` | write | Select an existing server-side cover path |
| 3 | `remove_library_item_cover` | `DELETE /api/items/{item_id}/cover` | destructive | Remove a custom cover |
| 3 | `match_library_item` | `POST /api/items/{item_id}/match` | write | Match/rematch one item |
| 3 | `scan_library` | `POST /api/libraries/{library_id}/scan` | admin | Scan library folders |
| 3 | `scan_library_item` | `POST /api/items/{item_id}/scan` | admin | Rescan one item |
| 3 | `batch_scan_items` | `POST /api/items/batch/scan` | admin | Rescan selected items |
| 3 | `batch_quick_match_items` | `POST /api/items/batch/quickmatch` | admin | Quick-match selected items (admin-only in v2.36.0) |
| 4 | `batch_get_items` | `POST /api/items/batch/get` | read | Retrieve exact item sets efficiently |
| 4 | `batch_update_items` | `POST /api/items/batch/update` | write | Apply documented batch metadata updates |
| 4 | `batch_delete_items` | `POST /api/items/batch/delete` | destructive | Delete an exact item set |
| 4 | `remove_library_items_with_issues` | `DELETE /api/libraries/{library_id}/issues` | destructive | Remove missing/invalid entries |
| 4 | `delete_library_item` | `DELETE /api/items/{item_id}` | destructive | Delete one exact item |
| 4 | `match_all_library_items` | `GET /api/libraries/{library_id}/matchall` | admin | Match all items despite upstream mutating GET semantics |
| 4 | `update_series` | `PATCH /api/series/{series_id}` | write | Amend series metadata |
| 4 | `update_author` | `PATCH /api/authors/{author_id}` | write | Amend author metadata |
| 4 | `match_author` | `POST /api/authors/{author_id}/match` | write | Match/rematch an author |
| 4 | `create_library` | `POST /api/libraries` | admin | Create a library with folders/settings |
| 5 | `update_library` | `PATCH /api/libraries/{library_id}` | admin | Update folders/settings as a full-array operation |
| 5 | `delete_library` | `DELETE /api/libraries/{library_id}` | destructive | Delete one exact library |
| 5 | `list_users` | `GET /api/users` | admin | User and permission administration |
| 5 | `create_user` | `POST /api/users` | admin | Create a user with explicit permissions |
| 5 | `update_user` | `PATCH /api/users/{user_id}` | admin | Update user permissions/access |
| 5 | `delete_user` | `DELETE /api/users/{user_id}` | destructive | Delete one exact user |
| 5 | `list_backups` | `GET /api/backups` | admin | Backup inventory |
| 5 | `create_backup` | `POST /api/backups` | admin | Create an on-server backup |
| 5 | `upload_backup` | `POST /api/backups/upload` multipart | admin | Upload a backup from an allowlisted local path |
| 5 | `apply_backup` | `GET /api/backups/{backup_id}/apply` | destructive | Restore an exact backup despite upstream mutating GET semantics |
| 6 | `delete_backup` | `DELETE /api/backups/{backup_id}` | destructive | Delete one exact backup |
| 6 | `list_sessions` | `GET /api/sessions` | admin | Playback-session administration |
| 6 | `start_playback_session` | `POST /api/items/{item_id}/play` | write | Start a basic playback session |
| 6 | `get_media_progress` | `GET /api/me/progress/{item_id}[/{episode_id}]` | read | Inspect current-user progress |
| 6 | `update_media_progress` | `PATCH /api/me/progress/{item_id}[/{episode_id}]` | write | Create/update progress |
| 6 | `delete_media_progress` | `DELETE /api/me/progress/{progress_id}` | destructive | Remove exact progress state |
| 6 | `get_logger_data` | `GET /api/logger-data` | admin | Server and scanner log access |
| 6 | `get_notification_settings` | `GET /api/notifications` | admin | Notification configuration visibility |
| 6 | `update_notification_settings` | `PATCH /api/notifications` | admin | Update notification settings |
| 6 | `create_notification` | `POST /api/notifications` | admin | Add a documented notification target/rule |

## Deferred surface

The v2.36.0 router exposes 202 `/api` method/routes plus `/status`, `/ping`, and
`/healthcheck`. This pack includes 59 direct routes and defers 146 direct routes.
Deferred routes are intentional and grouped as follows:

- Podcast feed ingestion/download/episode management: useful, but not required
  for Jay's initial audiobook-library management surface.
- Collections, playlists, bookmarks, RSS feeds, shares, and e-reader email:
  user-facing curation/sharing rather than core library maintenance.
- Audio-file download, ebook streaming/status, ffprobe, raw file deletion, M4B
  encoding, embedded-tag writing, and chapter editing: specialized binary or
  transcoding workflows that need separate resource and safety design.
- Open-session sync/close, local-session sync, batch session deletion, listening
  history/stat variants, and continue-listening controls: deferred beyond the
  basic session/progress surface.
- Author image upload/delete, narrator maintenance, tags/genres rename/delete,
  sorting prefixes, watcher update, and metadata-file removal: lower-priority
  maintenance operations.
- Notification update/delete/test and notification event-data endpoints: initial
  settings/read/create coverage is sufficient for the first production surface.
- API-key CRUD, auth settings, password/OIDC operations, login/logout/init, and
  OAuth flows: credential/bootstrap operations deliberately excluded from a
  bearer-token management pack.
- Cache purge, custom metadata-provider CRUD, server backup-path changes, backup
  download, server statistics variants, and email settings/tests: useful future
  admin extensions, but not required for the initial coherent surface.
- `/ping` and `/healthcheck` are redundant with `get_status` for catalog use.

## Version drift notes

- The current router adds batch scan, narrator, raw library-file, ebook, online
  session, API-key, auth-settings, email, provider, stats, and other routes not
  fully represented in the published reference.
- The historical docs call `GET /api/items/{id}/tone-object`; v2.36.0 exposes
  `GET /api/items/{id}/metadata-object` instead. Neither is included initially.
- `matchall` and backup `apply` are mutating `GET` routes upstream. Their Nexus
  classes are explicitly `admin` and `destructive`, respectively, rather than
  being inferred from HTTP method.
- `POST /api/authorize`, not `GET`, is the v2.36.0 route used for live version
  reconciliation.
