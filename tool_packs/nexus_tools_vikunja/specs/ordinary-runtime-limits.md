# Ordinary operation availability

These 27 wrappers match the deployed `live-v2-2.7.0.json` API reference. They use
the existing configured bearer token. They do not log in, acquire a session,
change token permissions, or fall back to another credential.

The parent lane's read-only audit of the installed v2.7.0 server found:

- `GET /health` is public and returned 200.
- Project duplication and task mark-read have API-token permissions. No write
  was performed as part of this expansion.
- Notifications support API tokens, but the installed token lacks that group's
  GET permission and returned 401. The token's scopes were left unchanged.
- General settings, avatar provider, sessions, timezones and subscriptions are
  session-only in the server's token-route collector. The installed API token
  returned 401 for the audited reads. Wrappers preserve the API's error rather
  than imply that the installed token can use these routes.
- Time entries require the server's Pro feature. The installed server reports
  `enabled_pro_features=[]`. With valid authentication, the disabled feature's
  routes return a feature-related 404. This pack cannot enable that feature.

General-settings and session responses recursively redact credential fields.
Do not use a redacted settings readback as a full replacement body. Sparse
PATCH operations send JSON Merge Patch and preserve explicit null values.
Full PUT replacements may reset omitted fields. Session deletion revokes the
specified session UUID. It does not delete the account.

This expansion has mocked HTTP contract tests and no live mutations or
temporary fixtures. Permission and feature evidence above comes from the
parent lane's separate read-only audit, not from those mocked tests.
