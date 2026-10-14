# Nexus NZBGet Tool Pack

Nexus tools for the documented NZBGet JSON-RPC API at
<https://nzbget.com/documentation/api/>.

The source API page observed on 2026-06-13 states that it covers NZBGet version
13.0 and later, with newer stable-release updates added to that documentation.

## Configuration

Set these values in the environment or `.env`:

- `NZBGET_URL`: Base URL for NZBGet, for example `http://localhost:6789`.
  The client appends `/jsonrpc` unless the URL already ends with `/jsonrpc`.
- `NZBGET_USERNAME`: Optional HTTP basic-auth username.
- `NZBGET_PASSWORD`: Optional HTTP basic-auth password.

If authentication is enabled, set both username and password. If NZBGet auth is
disabled, omit both.

## Tools

All tool names use the `nzbget.` namespace and call JSON-RPC with positional
parameters.

- Program control: `version`, `shutdown`, `reload`
- Queue and history: `listgroups`, `listfiles`, `history`, `append`,
  `editqueue`, `scan`
- Status, logging, and statistics: `status`, `sysinfo`, `systemhealth`, `log`,
  `writelog`, `loadlog`, `logscript`, `logupdate`, `servervolumes`,
  `resetservervolume`
- Pause and speed limit: `rate`, `pausedownload`, `resumedownload`, `pausepost`,
  `resumepost`, `pausescan`, `resumescan`, `scheduleresume`
- Configuration: `config`, `loadconfig`, `saveconfig`, `configtemplates`
- Extensions: `loadextensions`, `downloadextension`, `updateextension`,
  `deleteextension`
- Tests and diagnostics: `testextension`, `testserver`, `testserverspeed`,
  `testdiskspeed`, `testnetworkspeed`
- Utility: `call` for raw JSON-RPC methods not yet wrapped by this pack

State-changing tools describe their impact in Nexus metadata. Tests in this
pack do not require a live NZBGet server.
