# Nexus Google People Tools

Nexus tool pack for Google People API contacts, contact groups, other contacts,
directory search, contact photos, and batch contact operations.

The pack uses the shared `nexus-tools-google-common` auth/client package and the
`google_people` namespace.

## Environment

Credentials and refresh behaviour are provided by `nexus-tools-google-common`.
The expected shared settings are:

- `GOOGLE_ACCESS_TOKEN`
- `GOOGLE_REFRESH_TOKEN`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_TOKEN_URL`
- `GOOGLE_TIMEOUT_SECONDS`

## Scopes

Read-only usage generally needs one or more of:

- `https://www.googleapis.com/auth/contacts.readonly`
- `https://www.googleapis.com/auth/contacts.other.readonly`
- `https://www.googleapis.com/auth/directory.readonly`

Write operations need:

- `https://www.googleapis.com/auth/contacts`

Full practical coverage uses all four scopes above.
