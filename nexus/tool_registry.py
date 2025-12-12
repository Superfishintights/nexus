"""Utility for registering and discovering tools exposed to the runner.

Tools are regular Python callables decorated with `@register_tool`. The registry
stores loaded tool metadata and supports lazy loading via the tool catalog.
"""
from __future__ import annotations

import importlib
import inspect
import pkgutil
from dataclasses import dataclass
from types import ModuleType
from typing import Any, Callable, Dict, Iterable, List, Optional


@dataclass(frozen=True)
class ToolInfo:
    """Metadata describing a single callable tool."""

    name: str
    module: str
    description: str
    signature: str
    examples: List[str]
    function: Callable[..., object]


_REGISTRY: Dict[str, ToolInfo] = {}


def register_tool(
    func: Optional[Callable[..., object]] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    examples: Optional[List[str]] = None,
) -> Callable[[Callable[..., object]], Callable[..., object]]:
    """Decorator used by tool modules to register callables."""

    def decorator(target: Callable[..., object]) -> Callable[..., object]:
        tool_name = name or target.__name__
        if tool_name in _REGISTRY:
            raise ValueError(f"A tool named '{tool_name}' has already been registered")
        doc = description if description is not None else (target.__doc__ or "")
        try:
            signature = str(inspect.signature(target))
        except (TypeError, ValueError):
            signature = "(...)"
        _REGISTRY[tool_name] = ToolInfo(
            name=tool_name,
            module=target.__module__,
            description=doc.strip(),
            signature=signature,
            examples=list(examples or []),
            function=target,
        )
        return target

    if func is not None:
        return decorator(func)
    return decorator


def clear_registry() -> None:
    """Clear the tool registry (primarily useful for testing)."""

    _REGISTRY.clear()


def iter_tools() -> Iterable[ToolInfo]:
    """Iterate over registered tools."""

    return _REGISTRY.values()


def get_tool(name: str) -> ToolInfo:
    """Retrieve tool metadata by name."""

    return _REGISTRY[name]


def is_tool_loaded(name: str) -> bool:
    """Return True if a tool is already registered in this process."""

    return name in _REGISTRY


def ensure_tool_loaded(name: str) -> ToolInfo:
    """Ensure the tool named *name* is imported and registered.

    This consults the tool catalog for the module path, imports that module,
    and returns the registered ToolInfo.
    """

    if name in _REGISTRY:
        return _REGISTRY[name]

    # Local import to avoid circular dependency at module load time.
    from .tool_catalog import get_catalog

    spec = get_catalog().get(name)
    if spec is None:
        raise KeyError(f"Unknown tool: {name}")
    importlib.import_module(spec.module)
    if name not in _REGISTRY:
        raise RuntimeError(
            f"Tool '{name}' did not register itself when importing '{spec.module}'"
        )
    return _REGISTRY[name]


def auto_import(package: ModuleType) -> None:
    """Import every submodule inside *package* to trigger registrations."""

    for module_info in pkgutil.walk_packages(package.__path__, prefix=f"{package.__name__}."):
        importlib.import_module(module_info.name)
