# Nexus WAHA tools

Curated tools for a private [WAHA](https://waha.devlike.pro/) deployment.

Configuration:

- `WAHA_URL` is WAHA base URL, for example `http://localhost:3000`.
- `WAHA_API_KEY` or `WAHA_API_KEY_FILE` is session-scoped read/send key.
- `WAHA_CONTROL_API_KEY` or `WAHA_CONTROL_API_KEY_FILE` is optional session-scoped control key.
- `WAHA_TIMEOUT_S` is HTTP timeout in seconds; defaults to `30`.
- `WAHA_LOCAL_FILE_MAX_BYTES` is maximum local upload size; defaults to 64 MiB
  and cannot exceed the built-in 128 MiB safety ceiling.

The read/send key should be scoped to one session with only `read` and `send`
permissions. The optional control key should have only the `control` permission.
Neither key needs admin or delete permission.

Local uploads are available through `send_file_local`, `send_image_local`,
`send_video_local`, and `send_voice_local`. They require an absolute path to a
non-empty regular file, reject final-component symlinks and unsafe filenames,
detect MIME type from the filename unless explicitly overridden, and upload
bounded base64 data directly to the private WAHA API using WAHA's documented
`file.data` contract. Inline images must be preconverted JPEGs; disabling media
conversion assumes WhatsApp-compatible MP4 or OGG/Opus input. Existing URL tools
remain public-HTTP(S)-only and retain their private-network protections.


The 30 canonical tools include live group metadata and participant v2 reads.
`get_group_participants` preserves both `id` and `pn` so a LID does not hide the
person's phone identity. `reply_text` sends a quoted reply through `sendText`,
`set_reaction` uses native WAHA `PUT /api/reaction`, and presence operations use
native WAHA APIs. `send_poll_vote` casts a vote as the linked account.

`send_poll` and `get_poll_votes` retain the application compatibility API for
stable cursors and original action/option IDs. Configure `WAHA_BRIDGE_URL` and
`WAHA_BRIDGE_TOKEN` or `WAHA_BRIDGE_TOKEN_FILE` to the WAHA-only adapter. These
names are retained for configuration compatibility. Before every operation,
the client requires that the authenticated adapter `/health` reports
`transport: "waha"`. It refuses legacy transport and has no transport fallback.
The adapter sends native GOWS polls, persists context, and normalizes durable
votes. Consumers still validate voter identity, expiry and action ownership.

Session status and configured webhook subscriptions are visible through
`get_session`. The migration adapter receives native `message.any`, `poll.vote`,
`poll.vote.failed` and `session.status` events. WAHA signs their raw JSON bodies
with HMAC SHA-512 in `X-Webhook-Hmac` and identifies the algorithm in
`X-Webhook-Hmac-Algorithm`. Session configuration belongs to the deployment,
not an unguarded tool that might replace existing subscriptions.
