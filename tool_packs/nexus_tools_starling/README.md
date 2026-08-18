# nexus_tools_starling

Install with:

```bash
pip install -e .
```

Then add this package root to `NEXUS_TOOL_PACKAGES`.

Configuration supports either a single Starling token via `STARLING_ACCESS_TOKEN`
or a split-token setup:

- `STARLING_TOKEN_READ_EDIT`
- `STARLING_TOKEN_PAYEE_SAVINGS_CREATE`
- `STARLING_TOKEN_PAYMENT_INITIATION`

The client will route each API call to the matching token automatically.
