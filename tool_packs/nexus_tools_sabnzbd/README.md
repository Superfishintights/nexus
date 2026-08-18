# nexus_tools_sabnzbd

Nexus tool pack for the SABnzbd 5.0 mode/query API.

## Configuration

Set these values in the environment or the Nexus `.env` file:

```bash
SABNZBD_URL=http://localhost:8080
SABNZBD_API_KEY=your-api-key
```

Optional settings:

```bash
SABNZBD_TIMEOUT_S=30
SABNZBD_API_PATH=/api
```

Install with:

```bash
pip install -e .
```

Then add this package root to `NEXUS_TOOL_PACKAGES`.

## Tool Coverage

The pack exposes the documented SABnzbd 5.0 API surface as `sabnzbd.*` tools:

- Queue: queue listing, global pause/resume, speed/pause timers, complete action, sorting, add URL/file/local-file, per-job pause/resume/delete/move/category/script/priority/post-processing/rename, job file listing/move/delete.
- History: listing, retry one/all, delete/archive, mark failed jobs completed.
- Status: status/fullstatus, unblock servers, delete/retry one or all orphaned jobs.
- Config and metadata: categories, scripts, server stats, get/set/delete config, config defaults, warnings, anonymized log, API/NZB key resets, certificate regeneration.
- Maintenance and utilities: version, auth, shutdown, restart, restart with queue repair, pause/resume post-processing, RSS fetch, watched-folder scan, quota reset, translate, and raw `sabnzbd.call`.

Destructive tools describe their impact in metadata and do not run during import.
