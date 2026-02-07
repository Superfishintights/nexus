"""Lazy Mapping wrapper for tool metadata used inside run_code.

This avoids eagerly converting every ToolSpec into a JSON-ish dict when building
the runner execution globals. Tool dicts are generated on demand and cached.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Dict, List, Tuple

from .tool_catalog import ToolSpec, spec_to_dict
from .tool_registry import ToolInfo, get_tool as get_loaded_tool, is_tool_loaded


def _score_spec(spec: ToolSpec, query: str) -> int:
    """Same scoring semantics as nexus.tool_catalog.score_spec (duplicated here).

    We keep this local so LazyTools can search a provided catalog snapshot
    without calling search_catalog(), which forces a catalog refresh.
    """

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


def _tool_info_to_dict(info: ToolInfo, *, detail_level: str) -> Dict[str, Any]:
    base: Dict[str, Any] = {"name": info.name, "module": info.module}
    if detail_level == "name":
        return base
    base.update(
        {
            "description": info.description.splitlines()[0] if info.description else "",
            "signature": info.signature,
            "loaded": True,
        }
    )
    if detail_level == "full":
        base["description"] = info.description
        base["examples"] = list(info.examples)
    return base


class LazyTools(Mapping[str, Dict[str, Any]]):
    """Mapping-like, cache-backed view of the tool catalog.

    - `TOOLS[name]` returns summary metadata dict (default behavior in runner).
    - `TOOLS.search(...)` returns a list of metadata dicts for matches.
    - `TOOLS.get_tool(...)` returns a metadata dict at the requested detail level.

    Tool dicts are not built until accessed.
    """

    def __init__(self, catalog: Mapping[str, ToolSpec]):
        self._catalog = catalog
        self._cache: Dict[Tuple[str, str], Dict[str, Any]] = {}

    def __iter__(self):
        return iter(self._catalog)

    def __len__(self) -> int:
        return len(self._catalog)

    def __getitem__(self, name: str) -> Dict[str, Any]:
        spec = self._catalog[name]
        return self._spec_to_tool_dict(spec, detail_level="summary")

    def _spec_to_tool_dict(self, spec: ToolSpec, *, detail_level: str) -> Dict[str, Any]:
        cache_key = (spec.name, detail_level)
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        loaded = is_tool_loaded(spec.name)
        tool_dict: Dict[str, Any] = spec_to_dict(
            spec, detail_level=detail_level, loaded=loaded
        )

        # If already loaded, prefer runtime info (doc/signature/examples) without
        # forcing an import for unloaded tools.
        if loaded and detail_level != "name":
            info = get_loaded_tool(spec.name)
            tool_dict["module"] = info.module
            tool_dict["signature"] = info.signature
            if detail_level == "summary":
                tool_dict["description"] = (
                    info.description.splitlines()[0] if info.description else ""
                )
            else:
                tool_dict["description"] = info.description
                tool_dict["examples"] = list(info.examples)

        self._cache[cache_key] = tool_dict
        return tool_dict

    def search(
        self,
        query: str,
        limit: int = 20,
        detail_level: str = "summary",
    ) -> List[Dict[str, Any]]:
        """Search within this catalog snapshot."""

        if limit <= 0:
            return []

        q = (query or "").strip().lower()
        if not q:
            specs = sorted(self._catalog.values(), key=lambda spec: spec.name)[:limit]
            return [self._spec_to_tool_dict(spec, detail_level=detail_level) for spec in specs]

        scored: List[Tuple[int, ToolSpec]] = []
        for spec in self._catalog.values():
            score = _score_spec(spec, q)
            if score > 0:
                scored.append((score, spec))

        scored.sort(key=lambda item: (-item[0], item[1].name))
        return [
            self._spec_to_tool_dict(spec, detail_level=detail_level)
            for _, spec in scored[:limit]
        ]

    def get_tool(self, name: str, detail_level: str = "full") -> Dict[str, Any]:
        """Return metadata for a single tool, falling back to loaded-only tools."""

        spec = self._catalog.get(name)
        if spec is not None:
            return self._spec_to_tool_dict(spec, detail_level=detail_level)

        if is_tool_loaded(name):
            return _tool_info_to_dict(get_loaded_tool(name), detail_level=detail_level)

        raise KeyError(f"Unknown tool: {name}")


__all__ = ["LazyTools"]

