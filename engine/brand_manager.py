from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict


@dataclass(frozen=True)
class BrandState:
    initialized: bool
    app_name: str
    version: str
    slogan: str
    theme: str
    resource_root: str


class BrandManager:
    """
    Central branding manager for SnapdragonAI Studio.

    The BrandManager is the single source of truth for:
    - application name
    - slogan
    - version
    - branding resource paths
    - future design tokens
    """

    def __init__(
        self,
        project_root: Path | None = None,
        version: str = "2.0.0-dev43",
        theme: str = "dark",
    ) -> None:
        self._initialized = False
        self._app_name = "SnapdragonAI Studio"
        self._slogan = "AI powered by Phoenix Engine"
        self._version = version
        self._theme = theme

        if project_root is None:
            self._project_root = Path(__file__).resolve().parent.parent
        else:
            self._project_root = Path(project_root).resolve()

        self._resource_root = self._project_root / "resources" / "branding"

    def initialize(self) -> None:
        self._initialized = True

    def shutdown(self) -> None:
        self._initialized = False

    def reload(self) -> None:
        self.shutdown()
        self.initialize()

    def set_theme(self, theme: str) -> None:
        normalized = theme.lower().strip()

        if normalized not in {"dark", "light"}:
            raise ValueError(
                f"Unsupported theme '{theme}'. Expected 'dark' or 'light'."
            )

        self._theme = normalized

    def app_name(self) -> str:
        return self._app_name

    def slogan(self) -> str:
        return self._slogan

    def version(self) -> str:
        return self._version

    def theme(self) -> str:
        return self._theme

    def logo(self) -> Path:
        if self._theme == "light":
            return self._resource_root / "logo" / "svg" / "logo_dark.svg"

        return self._resource_root / "logo" / "svg" / "logo_light.svg"

    def icon(self) -> Path:
        return self._resource_root / "logo" / "ico" / "app_icon.ico"

    def splash(self) -> Path:
        return self._resource_root / "splash" / f"splash_{self._theme}.svg"

    def about_logo(self) -> Path:
        return self.logo()

    def resource_root(self) -> Path:
        return self._resource_root

    def state(self) -> BrandState:
        return BrandState(
            initialized=self._initialized,
            app_name=self._app_name,
            version=self._version,
            slogan=self._slogan,
            theme=self._theme,
            resource_root=str(self._resource_root),
        )

    def as_dict(self) -> Dict[str, str | bool]:
        state = self.state()

        return {
            "initialized": state.initialized,
            "app_name": state.app_name,
            "version": state.version,
            "slogan": state.slogan,
            "theme": state.theme,
            "resource_root": state.resource_root,
        }