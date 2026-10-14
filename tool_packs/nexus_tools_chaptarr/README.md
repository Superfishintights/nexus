# Chaptarr tools for Nexus

This pack exposes all 316 operations in the official Chaptarr OpenAPI contract. It also provides two local tools to inspect that contract and its resource schemas. Tools use the `chaptarr` namespace and load through Nexus on demand.

The contract comes from Chaptarr source commit `e67374f4b3fed01bbf08f18672add944062fcb49`. This matches the source revision of the Chaptarr `0.9.965.0` instance used for discovery. The package includes `openapi.json` and `coverage-manifest.json`. The manifest maps each documented HTTP method and path to its generated tool name, arguments and policy class.

## Install and configure

Install the pack alongside Nexus core:

```bash
pip install -e ./tool_packs/nexus_tools_chaptarr
```

Append `nexus_tools_chaptarr` to the existing `NEXUS_TOOL_PACKAGES` value. Preserve the other packages in that list.

Set these values in the Nexus process environment or its configured `.env` file:

```dotenv
CHAPTARR_URL=http://chaptarr:8789
CHAPTARR_API_KEY_FILE=/run/nexus-secrets/chaptarr_api_key
CHAPTARR_TIMEOUT_S=30
```

`CHAPTARR_URL` is the service base URL. A configured URL base path is supported, and a trailing `/api/v1` does not add that API prefix twice. Use an explicit `http://` or `https://` scheme. The client defaults to HTTPS if the scheme is absent.

Set either `CHAPTARR_API_KEY` or `CHAPTARR_API_KEY_FILE`. The direct key takes precedence. The file must contain the key as text and must be readable inside the Nexus process or container. Requests send the key in `X-Api-Key`. No credentials are required for the two local schema tools.

`CHAPTARR_TIMEOUT_S` is a positive, finite number of seconds and defaults to 30. Nexus can enforce a separate execution deadline, so increasing the HTTP timeout alone does not extend a gateway call. A timed-out mutation needs a service readback before another attempt.

## Read the library and service state

Each example below is Nexus runner code. Set `RESULT` to the value you want Nexus to return.

```python
RESULT = load_tool("chaptarr.get_system_status")()
```

```python
RESULT = load_tool("chaptarr.get_author_lookup")(
    params={"term": "Ursula K. Le Guin"}
)
```

```python
RESULT = load_tool("chaptarr.get_book_lookup")(
    params={"term": "A Wizard of Earthsea"}
)
```

```python
RESULT = load_tool("chaptarr.get_book")()
```

```python
RESULT = load_tool("chaptarr.get_queue")(
    params={"offset": 0, "pageSize": 20, "includeUnmonitored": True}
)
```

```python
RESULT = load_tool("chaptarr.get_rootfolder")()
```

List responses retain the upstream response shape. Paged endpoints return one requested page. The pack does not fetch every page automatically. For `get_book_paged`, use `offset` and `pageSize`, then increase `offset` for the next page. Add `includeUnmonitored=True` when you need the entire library rather than only monitored books.

The live library has more than 105,000 book IDs. An unfiltered `get_book` timed out even after 60 seconds during read checks. Prefer a paged request, a selected book ID, or an author filter. The upstream `bookfile` route returned 500 without ID filters. Provide the applicable `bookId`, `bookIds` or `bookFileIds` query fields after checking `get_api_operation`.

## Inspect arguments and resource schemas

The generated tools accept path arguments by name, optional `params` for query fields, and optional `body` when the operation accepts a request body. These dictionaries preserve Chaptarr's flexible resource shapes. The upstream service validates their contents.

Use the packaged contract to find exact fields rather than guessing from the function signature:

```python
RESULT = load_tool("chaptarr.get_api_operation")("chaptarr.create_book")
```

```python
RESULT = load_tool("chaptarr.get_api_schema")("BookResource")
```

```python
RESULT = load_tool("chaptarr.get_api_schema")()
```

`get_api_operation` returns the manifest entry, original OpenAPI operation and referenced resource schemas. It accepts a qualified name such as `chaptarr.create_book` or an unqualified name such as `create_book`. `get_api_schema` lists available schemas when called without a name. With a name, it returns that schema and its referenced schemas. Both tools read package files and make no network request.

Query dictionaries omit `None`, encode booleans as `true` and `false`, and repeat a query key for list values. Bodies preserve nested objects and lists. JSON keys use the upstream camelCase names. Some DELETE operations accept bodies, so the relevant tools expose `body` as well as `params`.

## Ebook and audiobook fields

Chaptarr supports separate ebook and audiobook settings. A generic `monitored` field alone does not describe every format-specific setting.

| Resource | Fields to inspect |
| --- | --- |
| `BookResource` | `audiobookMonitored`, `ebookMonitored`, `mediaType`, `foreignBookId`, `foreignEditionId`, `editions`, `addOptions` |
| `AuthorResource` | `audiobookRootFolderPath`, `ebookRootFolderPath`, `audiobookQualityProfileId`, `ebookQualityProfileId`, `audiobookMetadataProfileId`, `ebookMetadataProfileId`, format-specific monitor modes and tags |
| `RootFolderResource` | `folderType`, `audiobook`, `ebook`, format-specific profile IDs, monitoring defaults and Audiobookshelf metadata options |
| `EditionResource` | `isEbook`, `format`, `readingFormatId`, `audibleASIN`, `narrator`, `durationSeconds`, `chapters` |
| `BookFileResource` | `mediaType`, `quality`, `path`, `narrator`, `tags` |

Read the selected resource schema before a write. Resolve profile IDs and root folders from the live service. An API schema describes fields, but it does not replace the service's validation rules or required metadata relationships.

For a normal book addition, inspect `chaptarr.create_book` and submit a complete book resource to `/api/v1/book`:

```python
# book_resource is a complete resource built from lookup results and
# the selected live author, root-folder, profile and edition settings.
RESULT = load_tool("chaptarr.create_book")(body=book_resource)
```

To update an existing book, read its current resource first and preserve the fields needed by the service:

```python
RESULT = load_tool("chaptarr.update_book_by_id")(
    id=book_id,
    body=updated_book_resource,
)
```

Earlier Chaptarr validation found an incomplete-resource defect in `/book/import`. That is historical evidence, not a fresh test of this release. Prefer the normal `/book` add route for adding a looked-up title. The pack still exposes the documented import route for cases that require it.

## Binary and text responses

The client returns parsed JSON for JSON responses and a string for text responses. Empty responses return `None`. HEAD requests return a dictionary with `status_code` and `headers`.

Binary responses, such as media-cover images and downloaded archives, return a JSON-compatible dictionary:

```json
{
  "encoding": "base64",
  "data": "...",
  "content_type": "image/jpeg",
  "size_bytes": 12345
}
```

`content_disposition` is included when the service sends it. Decode `data` with Base64 to recover the original bytes. Binary responses can be large, so select the specific file or cover you need.

## Browser authentication routes

Most `/api/v1` operations use the API key. Browser routes, static content and `/initialize.json` can require a UI login cookie instead. `chaptarr.create_login` accepts `form_data` with `username`, `password` and `rememberMe`, plus an optional `params` dictionary with `returnUrl`.

The cached client retains cookies for later calls in the same Nexus process. Text form fields without file uploads use `application/x-www-form-urlencoded`. Requests with files use `multipart/form-data`. Changing the configured URL, key or timeout replaces the cached client and its cookies.

Plex and OIDC routes depend on redirect and cookie state. The client blocks redirects to another origin, so exposing those routes does not establish a complete interactive provider login flow. `/initialize.json` can return an API key. Authentication routes can change sessions or account binding even when their HTTP method is GET.

## Multipart file uploads

Operations that accept file uploads expose `files` and `form_data`. Each `files` entry uses `path` or `local_path` for a file visible to the Nexus server. Optional fields are `field_name`, `filename` and `content_type`. The default file field name is `files`. The client derives the filename and content type when you omit them.

Use `form_data` for accompanying text fields. Do not combine a JSON `body` with `files` or `form_data` in the same request. A file on the desktop is not automatically visible to HTTP Nexus. Upload it through Nexus file staging first or use a path mounted into the server container.

Backup restore accepts an uploaded file in the implementation even though the pinned OpenAPI omits its request body. The tool therefore supports multipart arguments:

```python
# Administrative operation. backup_path must exist on the Nexus server.
RESULT = load_tool("chaptarr.create_system_backup_restore_upload")(
    files=[{
        "path": backup_path,
        "field_name": "files",
        "content_type": "application/zip",
    }],
    form_data={},
)
```

## Coverage and validation limits

The pack covers library lookup and management, editions and files, import and release operations, queues and history, profiles, providers, configuration, tasks, commands, backups, logs, covers, feeds and authentication routes. Production Chaptarr can reject development-only route-inspection endpoints with 404 even though they appear in the source contract.

Each tool declares its Nexus policy class. Reads, writes, destructive operations and administrative operations remain distinct. Discovery coverage does not mean that every operation works in every deployment or that a caller has permission to run it.

Live discovery verified authenticated service status. Live write validation was not part of this build. Backup restore, deletion, download grabs, imports, configuration changes and service-control operations need appropriate authorization and a subsequent readback when used.
