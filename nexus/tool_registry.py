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

from .tool_policy import (
    ToolAccessError,
    ToolPolicy,
    classify_tool_name,
    namespace_for_tool,
)


@dataclass(frozen=True)
class ToolInfo:
    """Metadata describing a single callable tool."""

    name: str
    module: str
    description: str
    signature: str
    examples: List[str]
    tool_class: str
    function: Callable[..., object]
    alias_of: Optional[str] = None

    @property
    def canonical_name(self) -> str:
        return self.alias_of or self.name


_REGISTRY: Dict[str, ToolInfo] = {}


def register_tool(
    func: Optional[Callable[..., object]] = None,
    *,
    name: Optional[str] = None,
    namespace: Optional[str] = None,
    description: Optional[str] = None,
    examples: Optional[List[str]] = None,
    tool_class: Optional[str] = None,
    aliases: Optional[List[str]] = None,
) -> Callable[[Callable[..., object]], Callable[..., object]]:
    """Decorator used by tool modules to register callables."""

    def decorator(target: Callable[..., object]) -> Callable[..., object]:
        if name is not None:
            base_name = name.strip()
            if not base_name:
                raise ValueError("Tool name cannot be empty")
        else:
            base_name = target.__name__

        tool_name = base_name
        normalized_namespace = (namespace or "").strip()
        if normalized_namespace:
            tool_name = f"{normalized_namespace}.{tool_name}"
        if tool_name in _REGISTRY:
            raise ValueError(f"A tool named '{tool_name}' has already been registered")
        doc = description if description is not None else (target.__doc__ or "")
        try:
            signature = str(inspect.signature(target))
        except (TypeError, ValueError):
            signature = "(...)"
        canonical = ToolInfo(
            name=tool_name,
            module=target.__module__,
            description=doc.strip(),
            signature=signature,
            examples=list(examples or []),
            tool_class=tool_class or classify_tool_name(tool_name),
            function=target,
        )
        _REGISTRY[tool_name] = canonical

        for alias in list(aliases or []):
            alias_name = alias.strip()
            if not alias_name:
                continue
            if alias_name == tool_name:
                continue
            if alias_name in _REGISTRY:
                raise ValueError(f"A tool named '{alias_name}' has already been registered")
            _REGISTRY[alias_name] = ToolInfo(
                name=alias_name,
                module=canonical.module,
                description=canonical.description,
                signature=canonical.signature,
                examples=list(canonical.examples),
                tool_class=canonical.tool_class,
                function=canonical.function,
                alias_of=canonical.name,
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


def ensure_tool_loaded(name: str, *, policy: Optional[ToolPolicy] = None) -> ToolInfo:
    """Ensure the tool named *name* is imported and registered.

    This consults the tool catalog for the module path, imports that module,
    and returns the registered ToolInfo.
    """

    if name in _REGISTRY:
        info = _REGISTRY[name]
        if policy is not None and policy.is_restricted and info.alias_of is not None:
            raise ToolAccessError(
                f"Tool '{name}' is not available in restricted mode; use canonical name '{info.alias_of}'"
            )
        _assert_tool_allowed(info, policy=policy)
        return info

    # Local import to avoid circular dependency at module load time.
    from .tool_catalog import get_catalog, resolve_tool_request

    catalog = get_catalog()
    spec = resolve_tool_request(
        name,
        catalog=catalog,
        policy=policy,
        allow_aliases=not bool(policy and policy.is_restricted),
    )
    importlib.import_module(spec.module)
    if name not in _REGISTRY:
        raise RuntimeError(
            f"Tool '{name}' did not register itself when importing '{spec.module}'"
        )
    info = _REGISTRY[name]
    _assert_tool_allowed(info, policy=policy)
    return info


def _assert_tool_allowed(info: ToolInfo, *, policy: Optional[ToolPolicy]) -> None:
    if policy is None:
        return
    if policy.is_restricted and info.alias_of is not None:
        raise ToolAccessError(
            f"Tool '{info.name}' is not available in restricted mode; use canonical name '{info.alias_of}'"
        )
    policy.assert_canonical_allowed(
        info.canonical_name,
        namespace=namespace_for_tool(info.canonical_name),
        tool_class=info.tool_class,
    )


def auto_import(package: ModuleType) -> None:
    """Import every submodule inside *package* to trigger registrations."""

    for module_info in pkgutil.walk_packages(package.__path__, prefix=f"{package.__name__}."):
        importlib.import_module(module_info.name)
