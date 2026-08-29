from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .brand_manager import BrandManager, BrandState

__all__ = [
    "BrandManager",
    "BrandState",
]


def __getattr__(name: str) -> Any:
    if name in __all__:
        from .brand_manager import BrandManager, BrandState

        exports = {
            "BrandManager": BrandManager,
            "BrandState": BrandState,
        }
        globals().update(exports)
        return exports[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted((*globals(), *__all__))
