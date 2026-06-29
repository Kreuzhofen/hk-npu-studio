from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


@dataclass(frozen=True)
class BrandState:
    initialized: bool
    app_name: str
    version: str
    slogan: str
    theme: str
    resource_root: str
    tokens_loaded: bool


class BrandManager:
    """
    Central branding manager for SnapdragonAI Studio.

    Single source of truth for:
    - application identity
    - author and copyright information
    - slogan and version
    - branding resource paths
    - theme-aware design tokens
    - logo, splash, about and installer assets
    """

    def __init__(
        self,
        project_root: Path | None = None,
        version: str = "2.0.0-dev45",
        theme: str = "dark",
    ) -> None:
        self._initialized = False
        self._version = version
        self._theme = self._normalize_theme(theme)

        if project_root is None:
            self._project_root = Path(__file__).resolve().parent.parent
        else:
            self._project_root = Path(project_root).resolve()

        self._resource_root = self._project_root / "resources" / "branding"
        self._tokens_path = self._resource_root / "tokens.json"
        self._tokens: Dict[str, Any] = {}

        self._app_name = "SnapdragonAI Studio"
        self._slogan = "AI powered by Phoenix Engine"

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        self._load_tokens()
        self._initialized = True

    def shutdown(self) -> None:
        self._initialized = False

    def reload(self) -> None:
        self.shutdown()
        self._load_tokens()
        self._initialized = True

    # ------------------------------------------------------------------
    # Application identity
    # ------------------------------------------------------------------

    def app_name(self) -> str:
        return str(self._tokens.get("app", {}).get("name", self._app_name))

    def slogan(self) -> str:
        return str(self._tokens.get("app", {}).get("slogan", self._slogan))

    def version(self) -> str:
        return self._version

    def version_string(self) -> str:
        return f"Version {self._version}"

    def engine(self) -> str:
        return "Phoenix Engine"

    # ------------------------------------------------------------------
    # Brand identity
    # ------------------------------------------------------------------

    def company(self) -> str:
        return "SnapdragonAI Studio"

    def author(self) -> str:
        return "Holger Kreuzhofen"

    def copyright(self) -> str:
        return "© 2026 Holger Kreuzhofen"

    def website(self) -> str:
        return ""

    def github(self) -> str:
        return ""

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def set_theme(self, theme: str) -> None:
        self._theme = self._normalize_theme(theme)

    def theme(self) -> str:
        return self._theme

    # ------------------------------------------------------------------
    # Branding assets
    # ------------------------------------------------------------------

    def logo(self) -> Path:
        return self.asset_path("LOGO_PRIMARY")

    def logo_icon(self) -> Path:
        return self.asset_path("LOGO_ICON")

    def icon(self) -> Path:
        return self.asset_path("APP_ICON")

    def splash(self) -> Path:
        return self.asset_path("LOGO_SPLASH")

    def about_logo(self) -> Path:
        return self.asset_path("ABOUT_LOGO")

    def installer_logo(self) -> Path:
        return self.asset_path("INSTALLER_LOGO")

    def logo_header(self) -> Path:
        return self.resource_path("logo/png/phoenix_header_dark.png")

    def logo_header_light(self) -> Path:
        return self.resource_path("logo/png/phoenix_header_light.png")

    def logo_header_dark(self) -> Path:
        return self.resource_path("logo/png/phoenix_header_dark.png")

    def logo_about(self) -> Path:
        return self.resource_path("logo/png/phoenix_about.png")

    def logo_splash(self) -> Path:
        return self.resource_path("logo/png/phoenix_splash.png")

    def logo_app_icon(self) -> Path:
        return self.resource_path("logo/ico/snapdragonai.ico")

    # ------------------------------------------------------------------
    # Paths
    # ------------------------------------------------------------------

    def resource_root(self) -> Path:
        return self._resource_root

    def tokens_path(self) -> Path:
        return self._tokens_path

    def resource_path(self, relative_path: str) -> Path:
        return self._resource_root / relative_path

    def asset_path(self, token_name: str) -> Path:
        value = self.token(token_name)

        if not isinstance(value, str):
            raise ValueError(f"Token '{token_name}' is not an asset path.")

        return self.resource_path(value)

    # ------------------------------------------------------------------
    # Design tokens
    # ------------------------------------------------------------------

    def token(self, name: str) -> Any:
        theme_tokens = self._theme_tokens()

        if name in theme_tokens:
            return theme_tokens[name]

        for section in ("assets", "typography", "sizes", "spacing"):
            section_tokens = self._tokens.get(section, {})
            if name in section_tokens:
                return section_tokens[name]

        raise KeyError(f"Unknown design token: {name}")

    def color(self, name: str) -> str:
        value = self.token(name)

        if not isinstance(value, str) or not value.startswith("#"):
            raise ValueError(f"Token '{name}' is not a color value.")

        return value

    def font(self, name: str) -> str:
        value = self.token(name)

        if not isinstance(value, str):
            raise ValueError(f"Token '{name}' is not a font value.")

        return value

    def size(self, name: str) -> int:
        value = self.token(name)

        if not isinstance(value, int):
            raise ValueError(f"Token '{name}' is not an integer size value.")

        return value

    def spacing(self, name: str) -> int:
        value = self.token(name)

        if not isinstance(value, int):
            raise ValueError(f"Token '{name}' is not an integer spacing value.")

        return value

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    def state(self) -> BrandState:
        return BrandState(
            initialized=self._initialized,
            app_name=self.app_name(),
            version=self._version,
            slogan=self.slogan(),
            theme=self._theme,
            resource_root=str(self._resource_root),
            tokens_loaded=bool(self._tokens),
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
            "tokens_loaded": state.tokens_loaded,
        }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _load_tokens(self) -> None:
        if not self._tokens_path.exists():
            self._tokens = {}
            return

        with self._tokens_path.open("r", encoding="utf-8") as file:
            loaded = json.load(file)

        if not isinstance(loaded, dict):
            raise ValueError("Brand tokens file must contain a JSON object.")

        self._tokens = loaded

    def _theme_tokens(self) -> Dict[str, Any]:
        themes = self._tokens.get("themes", {})

        if not isinstance(themes, dict):
            return {}

        theme_tokens = themes.get(self._theme, {})

        if not isinstance(theme_tokens, dict):
            return {}

        return theme_tokens

    @staticmethod
    def _normalize_theme(theme: str) -> str:
        normalized = theme.lower().strip()

        if normalized not in {"dark", "light"}:
            raise ValueError(
                f"Unsupported theme '{theme}'. Expected 'dark' or 'light'."
            )

        return normalized