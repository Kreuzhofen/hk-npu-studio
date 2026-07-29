"""
Snapdragon AI Studio

PluginInfo

Created by Holger Kreuzhofen
"""

from dataclasses import dataclass, field


@dataclass(slots=True)
class PluginInfo:
    id: str
    name: str
    version: str
    author: str
    backend: str
    skills: list[str] = field(default_factory=list)

    @classmethod
    def from_json(cls, data: dict):
        if not isinstance(data, dict):
            raise ValueError("Plugin-Manifest muss ein JSON-Objekt sein.")
        required = ("id", "name", "version", "author", "backend", "skills")
        missing = [key for key in required if key not in data]
        if missing:
            raise ValueError(
                "Plugin-Manifest unvollständig: " + ", ".join(missing)
            )
        plugin_id = str(data["id"]).strip()
        if not plugin_id or not plugin_id.replace("_", "").isalnum():
            raise ValueError(f"Ungültige Plugin-ID: {plugin_id!r}")
        skills = data["skills"]
        if not isinstance(skills, list) or not all(
            isinstance(skill, str) and skill.strip() for skill in skills
        ):
            raise ValueError("Plugin-Skills müssen eine Liste nichtleerer Strings sein.")
        text_values = {
            key: str(data[key]).strip()
            for key in ("name", "version", "author", "backend")
        }
        empty = [key for key, value in text_values.items() if not value]
        if empty:
            raise ValueError(
                "Plugin-Manifest enthält leere Pflichtwerte: " + ", ".join(empty)
            )
        return cls(
            id=plugin_id,
            name=text_values["name"],
            version=text_values["version"],
            author=text_values["author"],
            backend=text_values["backend"],
            skills=list(skills),
        )
