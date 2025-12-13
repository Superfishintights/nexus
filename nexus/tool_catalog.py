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
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from .config import get_setting


TOOL_PACKAGES_ENV = "NEXUS_TOOL_PACKAGES"
DEFAULT_TOOL_PACKAGES = ("tools",)


@dataclass(frozen=True)
class ToolSpec:
    """Metadata for a tool discovered on disk but not yet imported."""

    name: str
    module: str
    description: str
    signature: str
    examples: Tuple[str, ...] = ()


_CATALOG: Optional[Dict[str, ToolSpec]] = None


def get_tool_package_names() -> Sequence[str]:
    """Return configured tool package names.

    Reads comma-separated names from NEXUS_TOOL_PACKAGES. Defaults to ["tools"].
    """

    raw = (get_setting(TOOL_PACKAGES_ENV) or "").strip()
    if not raw:
        return DEFAULT_TOOL_PACKAGES
    names = [name.strip() for name in raw.split(",") if name.strip()]
    return names or DEFAULT_TOOL_PACKAGES


def get_catalog(*, refresh: bool = False) -> Dict[str, ToolSpec]:
    """Return the cached tool catalog, rebuilding if needed."""

    global _CATALOG
    if refresh or _CATALOG is None:
        _CATALOG = build_catalog()
    return _CATALOG


def build_catalog() -> Dict[str, ToolSpec]:
    """Scan all configured packages and build a name->ToolSpec catalog."""

    catalog: Dict[str, ToolSpec] = {}
    duplicates: List[Tuple[str, str, str]] = []

    for package_name in get_tool_package_names():
        spec = importlib.util.find_spec(package_name)
        if spec is None or spec.submodule_search_locations is None:
            continue

        for location in spec.submodule_search_locations:
            package_path = Path(location)
            for tool_spec in scan_package(package_name, package_path):
                existing = catalog.get(tool_spec.name)
                if existing is not None and existing.module != tool_spec.module:
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

    return catalog


def scan_package(package_name: str, package_path: Path) -> Iterable[ToolSpec]:
    """Yield ToolSpec objects discovered inside *package_path*."""

    for file_path in package_path.rglob("*.py"):
        if file_path.name == "__init__.py":
            continue
        if file_path.name.startswith("test_") or file_path.name.endswith("_test.py"):
            continue
        yield from scan_file(package_name, package_path, file_path)


def scan_file(package_name: str, package_root: Path, file_path: Path) -> Iterable[ToolSpec]:
    """Parse a single file and yield any ToolSpec definitions found."""

    try:
        source = file_path.read_text(encoding="utf-8")
    except OSError:
        return []

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError:
        return []

    module_path = module_name_for_file(package_name, package_root, file_path)

    specs: List[ToolSpec] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and has_register_tool_decorator(node):
            decorator_meta = extract_decorator_metadata(node)
            base_name = decorator_meta.name or node.name
            namespace = (decorator_meta.namespace or "").strip()
            tool_name = f"{namespace}.{base_name}" if namespace else base_name
            docstring = decorator_meta.description or (ast.get_docstring(node) or "")
            signature = signature_from_ast(node, source)
            examples = tuple(decorator_meta.examples or ())
            specs.append(
                ToolSpec(
                    name=tool_name,
                    module=module_path,
                    description=docstring.strip(),
                    signature=signature,
                    examples=examples,
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


def has_register_tool_decorator(node: ast.FunctionDef) -> bool:
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


def extract_decorator_metadata(node: ast.FunctionDef) -> DecoratorMetadata:
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Call) and is_register_tool_decorator(decorator):
            name = None
            namespace = None
            description = None
            examples: Optional[List[str]] = None
            for keyword in decorator.keywords:
                if keyword.arg == "name":
                    name = literal_str(keyword.value)
                elif keyword.arg == "namespace":
                    namespace = literal_str(keyword.value)
                elif keyword.arg == "description":
                    description = literal_str(keyword.value)
                elif keyword.arg == "examples":
                    examples = literal_str_list(keyword.value)
            return DecoratorMetadata(
                name=name,
                namespace=namespace,
                description=description,
                examples=examples,
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


def signature_from_ast(node: ast.FunctionDef, source: str) -> str:
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


def search_catalog(query: str = "", *, limit: int = 20) -> List[ToolSpec]:
    """Search the catalog and return best matches."""

    catalog = get_catalog(refresh=True)
    if not query:
        return sorted(catalog.values(), key=lambda spec: spec.name)[:limit]

    q = query.lower()
    scored: List[Tuple[int, ToolSpec]] = []
    for spec in catalog.values():
        score = score_spec(spec, q)
        if score > 0:
            scored.append((score, spec))

    scored.sort(key=lambda item: (-item[0], item[1].name))
    return [spec for _, spec in scored[:limit]]


def score_spec(spec: ToolSpec, query: str) -> int:
    name = spec.name.lower()
    module = spec.module.lower()
    description = spec.description.lower()

    if name == query:
        return 100
    if name.startswith(query):
        return 80
    if query in name:
        return 60
    if query in module:
        return 50
    if query in description:
        return 40
    return 0


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
            "loaded": loaded,
        }
    )

    if detail_level == "full":
        base["description"] = spec.description
        base["examples"] = list(spec.examples)

    return base


__all__ = [
    "ToolSpec",
    "get_tool_package_names",
    "get_catalog",
    "search_catalog",
    "spec_to_dict",
    "TOOL_PACKAGES_ENV",
]
