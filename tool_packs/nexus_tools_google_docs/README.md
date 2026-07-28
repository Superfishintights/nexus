# nexus_tools_google_docs

Google Docs tools for Nexus, using the shared `nexus-tools-google-common` OAuth/API client.

Enable with:

```bash
export NEXUS_TOOL_PACKAGES="nexus_tools_google_common,nexus_tools_google_docs"
```

Namespace: `google_docs`

Main tools:

- `create_document`
- `get_document`
- `batch_update_document`
- `append_text`
- `insert_text`
- `replace_all_text`
- `delete_content_range`
- `insert_table`
- `insert_page_break`
- `create_named_range`
- `update_text_style`
- `update_paragraph_style`
- `insert_inline_image`
- `pin_table_header_rows`
- `merge_table_cells`
- `unmerge_table_cells`

Configure Google credentials through the shared common pack environment variables such as `GOOGLE_ACCESS_TOKEN`, `GOOGLE_REFRESH_TOKEN`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, or `GOOGLE_TOKEN_FILE`.
