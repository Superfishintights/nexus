"""Derive an endpoint inventory from the official TickTick Markdown reference.

Usage: python build_spec.py /path/to/openapi.md
The official reference is Markdown, not an OpenAPI JSON specification.
"""
import json
import re
import sys
from pathlib import Path

source = Path(sys.argv[1]).read_text()
paths = {}
for block in re.split(r'(?m)^#### ', source)[1:]:
    title = block.splitlines()[0].strip()
    match = re.search(r'(?m)^(GET|POST|PUT|DELETE) (/open/v1/[^\s]+)', block)
    if not match:
        continue
    method, path = match.groups()
    path_params = [{'name': p, 'in': 'path', 'required': True, 'schema': {'type': 'string'}} for p in re.findall(r'{([^}]+)}', path)]
    contract = block[match.end():].split('##### Responses')[0].strip().strip('`').strip()
    paths.setdefault(path, {})[method.lower()] = {
        'summary': title,
        'description': contract,
        'parameters': path_params,
        'responses': {'200': {'description': 'Official API response; see the live Markdown reference.'}},
    }
spec = {'openapi':'3.0.3','info':{'title':'TickTick documented Open API endpoint inventory','version':'2026-10-04','description':'Derived from https://developer.ticktick.com/docs/openapi.md. Request contract text retained; not a provider-issued OpenAPI specification.'},'servers':[{'url':'https://api.ticktick.com'}],'paths':paths}
Path(__file__).parents[1].joinpath('spec/openapi.json').write_text(json.dumps(spec, indent=2)+'\n')
print(f'{sum(map(len, paths.values()))} operations')
