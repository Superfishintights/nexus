"""Utility for registering and discovering tools exposed to the runner."""
from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass
from types import ModuleType
from typing import Callable, Dict, Iterable, Optional


@dataclass(frozen=True)
class ToolInfo:
    """Metadata describing a single callable tool."""

    name: str
    module: str
    description: str
    function: Callable[..., object]


_REGISTRY: Dict[str, ToolInfo] = {}


def register_tool(
    func: Optional[Callable[..., object]] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> Callable[[Callable[..., object]], Callable[..., object]]:
    """Decorator used by tool modules to register callables."""

    def decorator(target: Callable[..., object]) -> Callable[..., object]:
        tool_name = name or target.__name__
        if tool_name in _REGISTRY:
            raise ValueError(f"A tool named '{tool_name}' has already been registered")
        doc = description if description is not None else (target.__doc__ or "")
        _REGISTRY[tool_name] = ToolInfo(
            name=tool_name,
            module=target.__module__,
            description=doc.strip(),
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


def auto_import(package: ModuleType) -> None:
    """Import every submodule inside *package* to trigger registrations."""

    for module_info in pkgutil.walk_packages(package.__path__, prefix=f"{package.__name__}."):
        importlib.import_module(module_info.name)
