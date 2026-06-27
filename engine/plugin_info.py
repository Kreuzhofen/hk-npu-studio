"""
SnapdragonAI Studio

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
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            version=data.get("version", ""),
            author=data.get("author", ""),
            backend=data.get("backend", ""),
            skills=data.get("skills", []),
        )