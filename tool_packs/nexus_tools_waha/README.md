# Nexus WAHA tools

Curated tools for a private [WAHA](https://waha.devlike.pro/) deployment.

Configuration:

- `WAHA_URL` — WAHA base URL, for example `http://127.0.0.1:3000`.
- `WAHA_API_KEY` or `WAHA_API_KEY_FILE` — session-scoped read/send key.
- `WAHA_CONTROL_API_KEY` or `WAHA_CONTROL_API_KEY_FILE` — optional session-scoped control key.
- `WAHA_TIMEOUT_S` — HTTP timeout in seconds; defaults to `30`.
- `WAHA_LOCAL_FILE_MAX_BYTES` — maximum local upload size; defaults to 64 MiB
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
