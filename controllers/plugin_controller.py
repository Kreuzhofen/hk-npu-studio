from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from uuid import uuid4

from engine.plugin_info import PluginInfo

class PluginMetadata:
    def __init__(
        self,
        plugin_id: str,
        name: str,
        version: str,
        author: str,
        description: str,
        enabled: bool = True,
        path: Path | None = None,
    ) -> None:
        self.id = plugin_id
        self.name = name
        self.version = version
        self.author = author
        self.description = description
        self.enabled = enabled
        self.path = path


class PluginController:
    """Controller for discovering, enabling/disabling, and installing plugins."""

    def __init__(self, plugins_dir: str | Path = r"C:\SnapdragonAI\plugins") -> None:
        self.plugins_dir = Path(plugins_dir)
        self.config_path = self.plugins_dir / "plugins_config.json"
        self.enabled_states: dict[str, bool] = {}
        self.load_config()

    def load_config(self) -> None:
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.enabled_states = json.load(f)
            except Exception:
                self.enabled_states = {}

    def save_config(self) -> None:
        staging: Path | None = None
        try:
            self.plugins_dir.mkdir(parents=True, exist_ok=True)
            staging = self.config_path.with_name(
                f".{self.config_path.name}.{uuid4().hex}.tmp"
            )
            with staging.open("w", encoding="utf-8", newline="\n") as f:
                json.dump(self.enabled_states, f, indent=4)
                f.flush()
                os.fsync(f.fileno())
            os.replace(staging, self.config_path)
        except Exception:
            pass
        finally:
            if staging is not None:
                staging.unlink(missing_ok=True)

    def get_plugins(self, filter_type: str = "Alle", search_query: str = "") -> list[PluginMetadata]:
        """Discover and return plugins under the plugins folder, filtered by state and query."""
        plugins = []
        if not self.plugins_dir.exists():
            return plugins

        for item in self.plugins_dir.iterdir():
            if item.is_dir() and not item.name.startswith("__"):
                plugin_py = item / "plugin.py"
                if plugin_py.exists():
                    plugin_id = item.name
                    # Read metadata from plugin.json if it exists
                    plugin_json = item / "plugin.json"
                    name = plugin_id.capitalize()
                    version = "1.0.0"
                    from app.i18n import tr
                    author = tr("plugin_fallback_author", "System")
                    description = tr("plugin_fallback_description", "Zusatzmodul für Snapdragon AI Studio.")

                    if plugin_json.exists():
                        try:
                            with open(plugin_json, "r", encoding="utf-8") as f:
                                data = json.load(f)
                                name = data.get("name", name)
                                version = data.get("version", version)
                                author = data.get("author", author)
                                description = data.get("description", description)
                        except Exception:
                            pass

                    # Default to enabled if not specified in config
                    enabled = self.enabled_states.get(plugin_id, True)

                    # Filter matching search query
                    if search_query:
                        q = search_query.lower()
                        if q not in name.lower() and q not in description.lower() and q not in author.lower():
                            continue

                    # Filter by tab selection: Alle, Aktiv, Verfügbar
                    if filter_type == "Aktiv" and not enabled:
                        continue
                    if filter_type == "Verfügbar" and enabled:
                        continue

                    plugins.append(
                        PluginMetadata(
                            plugin_id=plugin_id,
                            name=name,
                            version=version,
                            author=author,
                            description=description,
                            enabled=enabled,
                            path=item,
                        )
                    )
        return sorted(plugins, key=lambda p: p.name.lower())

    def toggle_plugin(self, plugin_id: str, enabled: bool) -> None:
        self.enabled_states[plugin_id] = enabled
        self.save_config()

    def install_plugin(self, source_path: str | Path) -> str:
        """Install a plugin from a source directory or zip by copying it to plugins_dir."""
        src = Path(source_path)
        if not src.exists():
            raise FileNotFoundError(f"Installationsquelle nicht gefunden: {src}")

        if src.is_dir():
            manifest_path = src / "plugin.json"
            entrypoint = src / "plugin.py"
            if not manifest_path.is_file() or not entrypoint.is_file():
                raise ValueError("Plugin benötigt plugin.json und plugin.py.")
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                plugin_id = PluginInfo.from_json(manifest).id
            except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
                raise ValueError(f"Ungültiges Plugin-Manifest: {error}") from error
            dest = self.plugins_dir / plugin_id
            if dest.exists():
                raise FileExistsError(f"Ein Plugin mit der ID '{plugin_id}' ist bereits installiert.")
            self.plugins_dir.mkdir(parents=True, exist_ok=True)
            staging = self.plugins_dir / f".{plugin_id}.{uuid4().hex}.tmp"
            try:
                shutil.copytree(src, staging)
                os.replace(staging, dest)
            finally:
                if staging.exists():
                    shutil.rmtree(staging)
            self.enabled_states[plugin_id] = True
            self.save_config()
            return plugin_id
        else:
            raise ValueError("Ungültige Installationsquelle. Bitte wähle einen Plugin-Ordner.")

    def uninstall_plugin(self, plugin_id: str) -> None:
        dest = self.plugins_dir / plugin_id
        if dest.exists():
            shutil.rmtree(dest)
        if plugin_id in self.enabled_states:
            del self.enabled_states[plugin_id]
            self.save_config()
