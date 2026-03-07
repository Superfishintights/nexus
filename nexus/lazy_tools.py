"""Lazy Mapping wrapper for tool metadata used inside run_code.

This avoids eagerly converting every ToolSpec into a JSON-ish dict when building
the runner execution globals. Tool dicts are generated on demand and cached.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Dict, List, Tuple

from .tool_catalog import (
    ToolSpec,
    discoverable_specs,
    get_catalog_diagnostics,
    search_specs,
    spec_to_dict,
)
from .tool_registry import ToolInfo, get_tool as get_loaded_tool, is_tool_loaded


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
        self._discoverable_names = tuple(
            spec.name
            for spec in discoverable_specs(
                self._catalog.values(),
                catalog=dict(self._catalog),
            )
        )
        self._cache: Dict[Tuple[str, str], Dict[str, Any]] = {}

    def __iter__(self):
        return iter(self._discoverable_names)

    def __len__(self) -> int:
        return len(self._discoverable_names)

    def __contains__(self, name: object) -> bool:
        return isinstance(name, str) and name in self._catalog

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

        specs = search_specs(self._catalog.values(), query, limit=limit)
        return [self._spec_to_tool_dict(spec, detail_level=detail_level) for spec in specs]

    def get_tool(self, name: str, detail_level: str = "full") -> Dict[str, Any]:
        """Return metadata for a single tool, falling back to loaded-only tools."""

        spec = self._catalog.get(name)
        if spec is not None:
            return self._spec_to_tool_dict(spec, detail_level=detail_level)

        if is_tool_loaded(name):
            return _tool_info_to_dict(get_loaded_tool(name), detail_level=detail_level)

        raise KeyError(f"Unknown tool: {name}")

    def diagnostics(self) -> Dict[str, Any]:
        """Return catalog diagnostics for the current tool snapshot."""

        return get_catalog_diagnostics()


__all__ = ["LazyTools"]
