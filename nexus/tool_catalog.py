"""Lazy tool catalog for progressive disclosure.

This module scans configured tool packages on disk using AST to build a catalog
of available tools without importing them. Tools are identified by the
`@register_tool` decorator.

The catalog supports text search and detail levels for context-efficient
tool discovery.
"""

from __future__ import annotations

import ast
import importlib.util
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple, Union

from .config import get_setting
from .tool_policy import (
    ToolPolicy,
    classify_tool_name,
    namespace_for_tool,
)


TOOL_PACKAGES_ENV = "NEXUS_TOOL_PACKAGES"
DEFAULT_TOOL_PACKAGES: Tuple[str, ...] = ()
REPO_ROOT = Path(__file__).resolve().parents[1]
LOCAL_TOOL_PACKS_ROOT = REPO_ROOT / "tool_packs"
LEGACY_ALL_PACKAGES_ALIASES = frozenset({"tools"})
FIRST_PARTY_TOOL_PACK_ORDER: Tuple[str, ...] = (
    "nexus_tools_jira",
    "nexus_tools_n8n",
    "nexus_tools_radarr",
    "nexus_tools_sonarr",
    "nexus_tools_tautulli",
    "nexus_tools_starling",
)


@dataclass(frozen=True)
class ToolSpec:
    """Metadata for a tool discovered on disk but not yet imported."""

    name: str
    module: str
    description: str
    signature: str
    examples: Tuple[str, ...] = ()
    tool_class: str = "read"
    # If set, this ToolSpec name is an alias for the canonical tool name.
    alias_of: Optional[str] = None


@dataclass(frozen=True)
class CatalogProblem:
    """Non-fatal problem encountered while building the tool catalog."""

    code: str
    message: str
    package: Optional[str] = None
    path: Optional[str] = None


_CATALOG: Optional[Dict[str, ToolSpec]] = None
_CATALOG_PROBLEMS: Tuple[CatalogProblem, ...] = ()
_DISCOVERY_VERBS = ("get", "create", "update", "delete", "set", "head")
_STOPWORDS = {
    "a",
    "all",
    "an",
    "for",
    "from",
    "i",
    "in",
    "is",
    "items",
    "me",
    "most",
    "of",
    "on",
    "please",
    "show",
    "the",
    "to",
    "what",
}
_TOKEN_NORMALIZATIONS = {
    "display": "get",
    "fetch": "get",
    "films": "movie",
    "issues": "issue",
    "latest": "recent",
    "list": "get",
    "members": "user",
    "movies": "movie",
    "plays": "play",
    "played": "play",
    "playing": "play",
    "recently": "recent",
    "rerun": "retry",
    "reruns": "retry",
    "shows": "series",
    "statuses": "status",
    "tickets": "issue",
    "transitions": "transition",
    "users": "user",
    "watched": "watch",
    "watching": "watch",
    "workflows": "workflow",
}
_TOKEN_EXPANSIONS = {
    "activity": {"stream", "session", "watch"},
    "episode": {"episodes", "series"},
    "execution": {"retry", "run"},
    "get": {"list", "show", "fetch"},
    "history": {"play", "playback", "watch", "recent"},
    "item": {"media", "movie", "episode", "series"},
    "issue": {"status", "transition", "ticket"},
    "lookup": {"search", "find"},
    "missing": {"wanted"},
    "movie": {"media", "lookup"},
    "play": {"history", "playback", "watch"},
    "queue": {"status", "download"},
    "recent": {"history", "latest", "last"},
    "retry": {"execution", "run"},
    "series": {"show", "episode"},
    "status": {"state", "transition"},
    "stream": {"activity", "session", "watch"},
    "user": {"users", "member", "account"},
    "watch": {"history", "play", "playback", "activity", "stream", "session"},
    "workflow": {"automation", "node"},
}
_SERVICE_ALIASES = {
    "jira": {"jira", "issue", "ticket"},
    "n8n": {"n8n", "workflow", "execution", "credential", "project"},
    "radarr": {"radarr", "movie", "movies"},
    "sonarr": {"sonarr", "series", "episode", "episodes", "show", "shows"},
    "tautulli": {"tautulli", "plex", "stream", "streams"},
}
_QUERY_INTENTS = (
    ({"current", "watch"}, {"activity", "stream", "session"}, {"recently", "added"}),
    ({"who", "watch"}, {"activity", "stream", "session", "user"}, set()),
    ({"recent", "watch"}, {"history", "play", "playback"}, {"recently", "added"}),
    ({"recent", "play"}, {"history", "play", "playback"}, {"recently", "added"}),
    ({"missing", "episode"}, {"wanted", "missing", "series", "episode"}, set()),
    ({"missing", "movie"}, {"wanted", "missing", "movie"}, set()),
    ({"queue", "status"}, {"queue", "status"}, set()),
    ({"add", "node"}, {"add", "node", "workflow"}, set()),
    ({"create", "workflow"}, {"create", "workflow"}, set()),
    ({"retry", "execution"}, {"retry", "execution"}, set()),
    ({"issue", "status"}, {"issue", "status", "transition"}, set()),
    ({"user", "get"}, {"user", "users", "get"}, set()),
)
_VERB_TOKENS = {"get", "create", "update", "delete", "set", "add", "retry", "lookup"}
_READ_INTENT_TOKENS = {"get", "history", "status", "watch", "play", "activity", "queue"}
_WRITE_VERBS = {"create", "update", "delete", "set", "add"}
_SPECIFICITY_PENALTIES = {
    "action": 10,
    "all": 8,
    "bulk": 10,
    "by": 6,
    "detail": 8,
    "details": 8,
    "editor": 10,
    "folder": 8,
    "history": 9,
    "id": 10,
    "imdb": 12,
    "schema": 10,
    "test": 10,
    "testall": 12,
    "tmdb": 12,
    "upload": 10,
}


@dataclass(frozen=True)
class _FileCacheEntry:
    fingerprint: Tuple[int, int]  # (mtime_ns, size)
    specs: Tuple[ToolSpec, ...]


_FILE_CACHE: Dict[str, _FileCacheEntry] = {}


def get_tool_package_names() -> Sequence[str]:
    """Return configured tool package names.

    Reads comma-separated names from NEXUS_TOOL_PACKAGES. Defaults to no tool packs.
    """

    raw = (get_setting(TOOL_PACKAGES_ENV) or "").strip()
    if not raw:
        return DEFAULT_TOOL_PACKAGES
    names = [name.strip() for name in raw.split(",") if name.strip()]
    expanded = _expand_tool_package_names(names)
    return tuple(expanded) or DEFAULT_TOOL_PACKAGES


def get_catalog(*, refresh: bool = False) -> Dict[str, ToolSpec]:
    """Return the cached tool catalog, rebuilding if needed."""

    global _CATALOG
    if refresh or _CATALOG is None:
        _CATALOG = build_catalog()
    return _CATALOG


def get_catalog_problems(*, refresh: bool = False) -> Tuple[CatalogProblem, ...]:
    """Return non-fatal problems seen during the most recent catalog build."""

    if refresh or _CATALOG is None:
        get_catalog(refresh=True)
    return _CATALOG_PROBLEMS


def get_catalog_diagnostics(*, refresh: bool = False) -> Dict[str, List[str]]:
    """Return a simplified warning view for client-facing responses."""

    problems = get_catalog_problems(refresh=refresh)
    return {"warnings": [problem.message for problem in problems]}


def build_catalog() -> Dict[str, ToolSpec]:
    """Scan all configured packages and build a name->ToolSpec catalog."""

    global _CATALOG_PROBLEMS

    catalog: Dict[str, ToolSpec] = {}
    duplicates: List[Tuple[str, str, str]] = []
    problems: List[CatalogProblem] = []
    seen_files: Set[str] = set()
    package_names = tuple(get_tool_package_names())

    _ensure_tool_pack_paths(package_names)

    for package_name in package_names:
        spec = importlib.util.find_spec(package_name)
        if spec is None or spec.submodule_search_locations is None:
            problems.append(
                CatalogProblem(
                    code="missing_package",
                    message=f"Configured tool package '{package_name}' could not be found.",
                    package=package_name,
                )
            )
            continue

        for location in spec.submodule_search_locations:
            package_path = Path(location)
            for tool_spec in scan_package(
                package_name,
                package_path,
                seen_files=seen_files,
                problems=problems,
            ):
                existing = catalog.get(tool_spec.name)
                if existing is not None:
                    duplicates.append((tool_spec.name, existing.module, tool_spec.module))
                    continue
                catalog[tool_spec.name] = tool_spec

    if duplicates:
        lines = [
            f"  - {name}: {old_module} vs {new_module}"
            for name, old_module, new_module in duplicates
        ]
        raise ValueError(
            "Duplicate tool names found across packages:\n" + "\n".join(lines)
        )

    # Drop cache entries for deleted/unseen files.
    stale = [path for path in _FILE_CACHE.keys() if path not in seen_files]
    for path in stale:
        _FILE_CACHE.pop(path, None)

    _CATALOG_PROBLEMS = tuple(problems)
    return catalog


def _expand_tool_package_names(names: Sequence[str]) -> List[str]:
    expanded: List[str] = []
    seen: Set[str] = set()

    for name in names:
        if name in LEGACY_ALL_PACKAGES_ALIASES:
            candidates = discover_local_tool_packages()
        else:
            candidates = (name,)

        for candidate in candidates:
            normalized = candidate.strip()
            if not normalized or normalized in seen:
                continue
            expanded.append(normalized)
            seen.add(normalized)

    return expanded


def discover_local_tool_packages(tool_packs_root: Path = LOCAL_TOOL_PACKS_ROOT) -> Tuple[str, ...]:
    """Return first-party tool package roots available in the local monorepo."""

    if not tool_packs_root.exists():
        return ()

    discovered: List[str] = []
    for package_root in tool_packs_root.iterdir():
        if not package_root.is_dir():
            continue
        package_name = package_root.name
        if not package_name.startswith("nexus_tools_"):
            continue
        if not (package_root / "pyproject.toml").exists():
            continue
        if not (package_root / package_name / "__init__.py").exists():
            continue
        discovered.append(package_name)

    preferred_index = {
        package_name: index for index, package_name in enumerate(FIRST_PARTY_TOOL_PACK_ORDER)
    }
    package_names = sorted(
        discovered,
        key=lambda name: (preferred_index.get(name, len(FIRST_PARTY_TOOL_PACK_ORDER)), name),
    )
    return tuple(package_names)


def _ensure_tool_pack_paths(package_names: Sequence[str]) -> None:
    """Expose local monorepo tool packs on sys.path when available."""

    if not package_names or not LOCAL_TOOL_PACKS_ROOT.exists():
        return

    for package_name in package_names:
        package_root = LOCAL_TOOL_PACKS_ROOT / package_name
        if not package_root.is_dir():
            continue
        if not (package_root / package_name / "__init__.py").exists():
            continue
        package_root_s = str(package_root)
        if package_root_s not in sys.path:
            sys.path.insert(0, package_root_s)


def scan_package(
    package_name: str,
    package_path: Path,
    *,
    seen_files: Optional[Set[str]] = None,
    problems: Optional[List[CatalogProblem]] = None,
) -> Iterable[ToolSpec]:
    """Yield ToolSpec objects discovered inside *package_path*."""

    for file_path in package_path.rglob("*.py"):
        if file_path.name == "__init__.py":
            continue
        if file_path.name.startswith("test_") or file_path.name.endswith("_test.py"):
            continue
        if seen_files is not None:
            seen_files.add(str(file_path))
        yield from scan_file(
            package_name,
            package_path,
            file_path,
            problems=problems,
        )


def scan_file(
    package_name: str,
    package_root: Path,
    file_path: Path,
    *,
    problems: Optional[List[CatalogProblem]] = None,
) -> Iterable[ToolSpec]:
    """Parse a single file and yield any ToolSpec definitions found."""

    try:
        st = file_path.stat()
    except OSError:
        return []

    fingerprint = (getattr(st, "st_mtime_ns", int(st.st_mtime * 1e9)), st.st_size)
    cache_key = str(file_path)
    cached = _FILE_CACHE.get(cache_key)
    if cached is not None and cached.fingerprint == fingerprint:
        return list(cached.specs)

    specs = list(
        _scan_file_uncached(
            package_name,
            package_root,
            file_path,
            problems=problems,
        )
    )
    _FILE_CACHE[cache_key] = _FileCacheEntry(fingerprint=fingerprint, specs=tuple(specs))
    return specs


def _scan_file_uncached(
    package_name: str,
    package_root: Path,
    file_path: Path,
    *,
    problems: Optional[List[CatalogProblem]] = None,
) -> Iterable[ToolSpec]:
    """Uncached scan of a single file (used by scan_file cache wrapper)."""

    try:
        source = file_path.read_text(encoding="utf-8")
    except OSError:
        if problems is not None:
            problems.append(
                CatalogProblem(
                    code="read_error",
                    message=f"Failed to read tool file: {file_path}",
                    package=package_name,
                    path=str(file_path),
                )
            )
        return []

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError as exc:
        if problems is not None:
            line = f"{exc.lineno}:{exc.offset}" if exc.lineno is not None else "?"
            problems.append(
                CatalogProblem(
                    code="syntax_error",
                    message=f"Syntax error at {line}: {exc.msg}",
                    package=package_name,
                    path=str(file_path),
                )
            )
        return []

    module_path = module_name_for_file(package_name, package_root, file_path)

    specs: List[ToolSpec] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and has_register_tool_decorator(node):
            decorator_meta = extract_decorator_metadata(node)
            base_name = decorator_meta.name or node.name
            namespace = (decorator_meta.namespace or "").strip()
            tool_name = f"{namespace}.{base_name}" if namespace else base_name
            docstring = decorator_meta.description or (ast.get_docstring(node) or "")
            signature = signature_from_ast(node, source)
            examples = tuple(decorator_meta.examples or ())
            canonical = ToolSpec(
                name=tool_name,
                module=module_path,
                description=docstring.strip(),
                signature=signature,
                examples=examples,
                tool_class=decorator_meta.tool_class or classify_tool_name(tool_name),
                alias_of=None,
            )
            specs.append(canonical)

            for alias in list(decorator_meta.aliases or ()):
                alias_name = (alias or "").strip()
                if not alias_name or alias_name == tool_name:
                    continue
                specs.append(
                    ToolSpec(
                        name=alias_name,
                        module=module_path,
                        description=canonical.description,
                        signature=canonical.signature,
                        examples=canonical.examples,
                        tool_class=canonical.tool_class,
                        alias_of=tool_name,
                    )
                )

    return specs


def module_name_for_file(package_name: str, package_root: Path, file_path: Path) -> str:
    rel = file_path.relative_to(package_root).with_suffix("")
    parts = ".".join(rel.parts)
    return f"{package_name}.{parts}" if parts else package_name


@dataclass(frozen=True)
class DecoratorMetadata:
    name: Optional[str] = None
    namespace: Optional[str] = None
    description: Optional[str] = None
    examples: Optional[List[str]] = None
    tool_class: Optional[str] = None
    aliases: Optional[List[str]] = None


def has_register_tool_decorator(
    node: Union[ast.FunctionDef, ast.AsyncFunctionDef]
) -> bool:
    for decorator in node.decorator_list:
        if is_register_tool_decorator(decorator):
            return True
    return False


def is_register_tool_decorator(decorator: ast.expr) -> bool:
    if isinstance(decorator, ast.Call):
        decorator = decorator.func
    if isinstance(decorator, ast.Name):
        return decorator.id == "register_tool"
    if isinstance(decorator, ast.Attribute):
        return decorator.attr == "register_tool"
    return False


def extract_decorator_metadata(
    node: Union[ast.FunctionDef, ast.AsyncFunctionDef]
) -> DecoratorMetadata:
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Call) and is_register_tool_decorator(decorator):
            name = None
            namespace = None
            description = None
            examples: Optional[List[str]] = None
            tool_class = None
            aliases: Optional[List[str]] = None
            for keyword in decorator.keywords:
                if keyword.arg == "name":
                    name = literal_str(keyword.value)
                elif keyword.arg == "namespace":
                    namespace = literal_str(keyword.value)
                elif keyword.arg == "description":
                    description = literal_str(keyword.value)
                elif keyword.arg == "examples":
                    examples = literal_str_list(keyword.value)
                elif keyword.arg == "tool_class":
                    tool_class = literal_str(keyword.value)
                elif keyword.arg == "aliases":
                    aliases = literal_str_list(keyword.value)
            return DecoratorMetadata(
                name=name,
                namespace=namespace,
                description=description,
                examples=examples,
                tool_class=tool_class,
                aliases=aliases,
            )
    return DecoratorMetadata()


def literal_str(node: ast.AST) -> Optional[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def literal_str_list(node: ast.AST) -> Optional[List[str]]:
    if isinstance(node, (ast.List, ast.Tuple)):
        items: List[str] = []
        for element in node.elts:
            value = literal_str(element)
            if value is not None:
                items.append(value)
        return items
    return None


def signature_from_ast(
    node: Union[ast.FunctionDef, ast.AsyncFunctionDef], source: str
) -> str:
    args = node.args

    parts: List[str] = []

    posonly = list(getattr(args, "posonlyargs", []))
    normal_pos = list(args.args)
    positional = posonly + normal_pos
    defaults = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)

    for index, (arg, default) in enumerate(zip(positional, defaults)):
        parts.append(format_arg(arg, default, source))
        if posonly and index == len(posonly) - 1:
            parts.append("/")

    if args.vararg is not None:
        parts.append(format_vararg(args.vararg, source))
    elif args.kwonlyargs:
        parts.append("*")

    for arg, default in zip(args.kwonlyargs, args.kw_defaults):
        parts.append(format_arg(arg, default, source, kw_only=True))

    if args.kwarg is not None:
        parts.append(format_kwarg(args.kwarg, source))

    return f"({', '.join(parts)})"


def format_arg(
    arg: ast.arg,
    default: Optional[ast.expr],
    source: str,
    *,
    kw_only: bool = False,
) -> str:
    del kw_only
    text = arg.arg
    annotation = annotation_text(arg.annotation, source)
    if annotation:
        text += f": {annotation}"

    if default is not None:
        default_text = default_source(default, source)
        text += f"={default_text}"

    return text


def format_vararg(arg: ast.arg, source: str) -> str:
    text = f"*{arg.arg}"
    annotation = annotation_text(arg.annotation, source)
    if annotation:
        text += f": {annotation}"
    return text


def format_kwarg(arg: ast.arg, source: str) -> str:
    text = f"**{arg.arg}"
    annotation = annotation_text(arg.annotation, source)
    if annotation:
        text += f": {annotation}"
    return text


def annotation_text(node: Optional[ast.expr], source: str) -> str:
    if node is None:
        return ""
    segment = ast.get_source_segment(source, node)
    return segment.strip() if segment else ""


def default_source(node: ast.expr, source: str) -> str:
    segment = ast.get_source_segment(source, node)
    if segment:
        return segment.strip()
    try:
        value = ast.literal_eval(node)
        return repr(value)
    except Exception:
        return "..."


def canonical_specs(specs: Iterable[ToolSpec]) -> List[ToolSpec]:
    """Return only canonical tool specs, excluding alias entries."""

    return [spec for spec in specs if spec.alias_of is None]


def canonical_name_for_spec(spec: ToolSpec) -> str:
    return spec.alias_of or spec.name


def get_canonical_spec(spec: ToolSpec, catalog: Dict[str, ToolSpec]) -> ToolSpec:
    if spec.alias_of is None:
        return spec
    return catalog[spec.alias_of]


def is_spec_allowed(
    spec: ToolSpec,
    *,
    policy: Optional[ToolPolicy],
    catalog: Dict[str, ToolSpec],
    allow_aliases: bool,
) -> bool:
    if spec.alias_of is not None and not allow_aliases:
        return False
    if policy is None or not policy.is_restricted:
        return True
    canonical = get_canonical_spec(spec, catalog)
    return policy.check_canonical(
        canonical.name,
        namespace=namespace_for_tool(canonical.name),
        tool_class=canonical.tool_class,
    )


def filter_specs_by_policy(
    specs: Iterable[ToolSpec],
    *,
    policy: Optional[ToolPolicy],
    catalog: Dict[str, ToolSpec],
    allow_aliases: bool,
) -> List[ToolSpec]:
    return [
        spec
        for spec in specs
        if is_spec_allowed(
            spec,
            policy=policy,
            catalog=catalog,
            allow_aliases=allow_aliases,
        )
    ]


def filter_catalog(
    catalog: Dict[str, ToolSpec],
    *,
    policy: Optional[ToolPolicy],
    allow_aliases: bool,
) -> Dict[str, ToolSpec]:
    return {
        spec.name: spec
        for spec in filter_specs_by_policy(
            catalog.values(),
            policy=policy,
            catalog=catalog,
            allow_aliases=allow_aliases,
        )
    }


def resolve_tool_request(
    name: str,
    *,
    catalog: Dict[str, ToolSpec],
    policy: Optional[ToolPolicy],
    allow_aliases: bool,
) -> ToolSpec:
    spec = catalog.get(name)
    if spec is None:
        raise KeyError(f"Unknown tool: {name}")
    if spec.alias_of is not None and not allow_aliases:
        raise KeyError(
            f"Tool '{name}' is not available in restricted mode; use canonical name '{spec.alias_of}'"
        )
    if not is_spec_allowed(
        spec,
        policy=policy,
        catalog=catalog,
        allow_aliases=allow_aliases,
    ):
        raise KeyError(f"Unknown tool: {name}")
    return spec


def discoverable_specs(
    specs: Iterable[ToolSpec],
    *,
    catalog: Optional[Dict[str, ToolSpec]] = None,
    include_aliases: bool = False,
    policy: Optional[ToolPolicy] = None,
) -> List[ToolSpec]:
    """Return the default agent-facing discovery surface."""

    if catalog is None:
        catalog = {spec.name: spec for spec in specs}
        spec_list = list(catalog.values())
    else:
        spec_list = list(specs)

    if not include_aliases:
        spec_list = canonical_specs(spec_list)

    spec_list = filter_specs_by_policy(
        spec_list,
        policy=policy,
        catalog=catalog,
        allow_aliases=include_aliases,
    )

    return [spec for spec in spec_list if _is_discoverable(spec, catalog)]


def _is_discoverable(spec: ToolSpec, catalog: Dict[str, ToolSpec]) -> bool:
    collapsed = _collapse_discovery_duplicate(spec.name)
    return collapsed == spec.name or collapsed not in catalog


def _collapse_discovery_duplicate(name: str) -> str:
    if "." not in name:
        return name
    namespace, base = name.split(".", 1)
    for verb in _DISCOVERY_VERBS:
        doubled = f"{verb}_{verb}_"
        if base.startswith(doubled):
            return f"{namespace}.{base[len(verb) + 1:]}"
    return name


def _tokenize_query(value: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", value.lower())


def _tokenize_terms(value: str) -> Set[str]:
    return set(_tokenize_query(value))


def _normalize_query_tokens(tokens: Iterable[str]) -> List[str]:
    normalized: List[str] = []
    for token in tokens:
        mapped = _TOKEN_NORMALIZATIONS.get(token, token)
        if mapped in _STOPWORDS:
            continue
        normalized.append(mapped)
    return normalized


def _expanded_query_weights(query: str) -> Dict[str, float]:
    raw_tokens = _tokenize_query(query)
    normalized = _normalize_query_tokens(raw_tokens)
    weights: Dict[str, float] = {}

    for token in normalized:
        weights[token] = max(weights.get(token, 0.0), 1.0)
        for expanded in _TOKEN_EXPANSIONS.get(token, set()):
            weights[expanded] = max(weights.get(expanded, 0.0), 0.55)

    token_set = set(normalized)
    for required, boosted, _ in _QUERY_INTENTS:
        if required.issubset(token_set):
            for token in boosted:
                weights[token] = max(weights.get(token, 0.0), 0.95)

    return weights


def _query_services(query: str) -> Set[str]:
    raw_tokens = set(_tokenize_query(query))
    normalized_tokens = set(_normalize_query_tokens(raw_tokens))
    services: Set[str] = set()
    for namespace, aliases in _SERVICE_ALIASES.items():
        if raw_tokens & aliases or normalized_tokens & aliases:
            services.add(namespace)
    return services


def _query_verbs(query: str) -> Set[str]:
    return {token for token in _normalize_query_tokens(_tokenize_query(query)) if token in _VERB_TOKENS}


def _matched_intents(query: str) -> List[Tuple[Set[str], Set[str], Set[str]]]:
    token_set = set(_normalize_query_tokens(_tokenize_query(query)))
    return [intent for intent in _QUERY_INTENTS if intent[0].issubset(token_set)]


def search_specs(
    specs: Iterable[ToolSpec],
    query: str = "",
    *,
    limit: int = 20,
    include_aliases: bool = False,
    policy: Optional[ToolPolicy] = None,
    catalog: Optional[Dict[str, ToolSpec]] = None,
) -> List[ToolSpec]:
    """Search an iterable of specs using the catalog's shared scoring rules."""

    if limit <= 0:
        return []

    spec_list = discoverable_specs(
        specs,
        include_aliases=include_aliases,
        catalog=catalog,
        policy=policy,
    )
    if not query:
        return sorted(spec_list, key=lambda spec: spec.name)[:limit]

    q = query.strip().lower()
    scored: List[Tuple[int, ToolSpec]] = []
    for spec in spec_list:
        score = score_spec(spec, q)
        if score > 0:
            scored.append((score, spec))

    scored.sort(key=lambda item: (-item[0], item[1].name))
    return [spec for _, spec in scored[:limit]]


def search_catalog(
    query: str = "",
    *,
    limit: int = 20,
    include_aliases: bool = False,
    policy: Optional[ToolPolicy] = None,
) -> List[ToolSpec]:
    """Search the catalog and return best matches.

    By default, alias entries are excluded from search results to keep tool
    discovery output focused on canonical names. Alias names still exist in the
    catalog so `load_tool("old_name")` can remain backwards-compatible.
    """

    catalog = get_catalog(refresh=True)
    return search_specs(
        catalog.values(),
        query,
        limit=limit,
        include_aliases=include_aliases,
        policy=policy,
        catalog=catalog,
    )


def score_spec(spec: ToolSpec, query: str) -> int:
    name = spec.name.lower()
    module = spec.module.lower()
    description = spec.description.lower()
    examples = " ".join(spec.examples).lower()
    raw_tokens = _tokenize_query(query)
    if not raw_tokens:
        return 0

    name_terms = _tokenize_terms(name)
    description_terms = _tokenize_terms(description)
    example_terms = _tokenize_terms(examples)
    module_terms = _tokenize_terms(module)
    normalized_tokens = set(_normalize_query_tokens(raw_tokens))
    expanded_weights = _expanded_query_weights(query)
    services = _query_services(query)
    verbs = _query_verbs(query)
    intents = _matched_intents(query)
    namespace = spec.name.split(".", 1)[0] if "." in spec.name else ""

    score = 0
    if name == query:
        score += 200
    elif name.startswith(query):
        score += 140
    elif query in name:
        score += 100
    elif query in description:
        score += 80
    elif query in examples:
        score += 70
    elif query in module:
        score += 60

    if services and namespace in services:
        score += 120
    elif services:
        score -= 20

    matched_tokens = 0
    for token, weight in expanded_weights.items():
        token_score = 0.0
        if token in name_terms:
            token_score = 42.0 * weight
        elif token in description_terms:
            token_score = 24.0 * weight
        elif token in example_terms:
            token_score = 16.0 * weight
        elif token in module_terms:
            token_score = 12.0 * weight
        elif token in name:
            token_score = 8.0 * weight
        elif token in description:
            token_score = 6.0 * weight
        if token_score:
            matched_tokens += 1
            score += int(token_score)

    if matched_tokens >= len(normalized_tokens) and len(normalized_tokens) > 1:
        score += 25

    spec_verbs = name_terms & _VERB_TOKENS
    if verbs & spec_verbs:
        score += 22
    elif verbs & {"get"} and spec_verbs & _WRITE_VERBS:
        score -= 28
    elif verbs & _WRITE_VERBS and spec_verbs & {"get"}:
        score -= 14

    if verbs & {"get"} and normalized_tokens & _READ_INTENT_TOKENS and spec_verbs & _WRITE_VERBS:
        score -= 12

    for _, boosted_terms, penalty_terms in intents:
        if name_terms & boosted_terms:
            score += 28
        elif description_terms & boosted_terms:
            score += 18

        if penalty_terms and (name_terms | description_terms) & penalty_terms:
            score -= 36

    for token, penalty in _SPECIFICITY_PENALTIES.items():
        if token in name_terms and token not in expanded_weights:
            score -= penalty

    if _collapse_discovery_duplicate(spec.name) != spec.name:
        score -= 10
    if _is_generated_http_description(spec):
        score -= 8
    if _has_placeholder_examples(spec):
        score -= 5

    # Prefer semantic history tools over "recently added" when the query is about watching/playback.
    if normalized_tokens & {"watch", "play", "history"}:
        if {"recently", "added"} <= name_terms | description_terms:
            score -= 30
        if "history" in name_terms or "history" in description_terms:
            score += 20
        if "activity" in name_terms or "activity" in description_terms:
            score += 14

    return score


def _is_generated_http_description(spec: ToolSpec) -> bool:
    return bool(re.match(r"^(GET|POST|PUT|DELETE|PATCH|HEAD)\s+/", spec.description))


def _has_placeholder_examples(spec: ToolSpec) -> bool:
    return any("(...)" in example for example in spec.examples)


def spec_to_dict(
    spec: ToolSpec,
    *,
    detail_level: str = "summary",
    loaded: bool = False,
) -> Dict[str, object]:
    """Convert a ToolSpec into a JSON-serializable dict."""

    base: Dict[str, object] = {"name": spec.name, "module": spec.module}

    if detail_level == "name":
        return base

    description = spec.description.splitlines()[0] if spec.description else ""
    base.update(
        {
            "description": description,
            "signature": spec.signature,
            "toolClass": spec.tool_class,
            "loaded": loaded,
        }
    )
    if spec.alias_of is not None:
        base["aliasOf"] = spec.alias_of
    else:
        base["canonicalName"] = spec.name

    if detail_level == "full":
        base["description"] = spec.description
        base["examples"] = list(spec.examples)

    return base


__all__ = [
    "ToolSpec",
    "CatalogProblem",
    "canonical_name_for_spec",
    "canonical_specs",
    "discoverable_specs",
    "filter_catalog",
    "get_tool_package_names",
    "get_catalog",
    "get_catalog_diagnostics",
    "get_catalog_problems",
    "get_canonical_spec",
    "is_spec_allowed",
    "resolve_tool_request",
    "search_catalog",
    "search_specs",
    "score_spec",
    "spec_to_dict",
    "TOOL_PACKAGES_ENV",
]
