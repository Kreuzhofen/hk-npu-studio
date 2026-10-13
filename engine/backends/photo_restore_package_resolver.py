"""Resolve the complete FiDeSR Photo Restore package without moving files."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import config


FIDESR_ARTIFACT_PATHS = {
    "vae_encoder_context": Path(
        "photo_restore_context/fidesr_vae_encoder/"
        "fidesr_vae_encoder.serialized.bin.bin"
    ),
    "unet_context": Path(
        "photo_restore_context/fidesr_unet/"
        "fidesr_unet_merged.serialized.bin.bin"
    ),
    "lrrb_context": Path(
        "photo_restore_context/fidesr_lrrb/"
        "fidesr_lrrb.serialized.bin.bin"
    ),
    "vae_decoder_context": Path(
        "photo_restore_context/fidesr_vae_decoder/"
        "fidesr_vae_decoder.serialized.bin.bin"
    ),
    "empty_prompt_embeddings": Path(
        "photo_restore/fidesr_empty_prompt_embeds.bin"
    ),
    "epsilon_seed": Path("photo_restore/fidesr_epsilon_seed231.bin"),
}

FIDESR_PACKAGE_ARTIFACT_PATHS = {
    "vae_encoder_context": Path(
        "context/fidesr_vae_encoder/"
        "fidesr_vae_encoder.serialized.bin.bin"
    ),
    "unet_context": Path(
        "context/fidesr_unet/fidesr_unet_merged.serialized.bin.bin"
    ),
    "lrrb_context": Path(
        "context/fidesr_lrrb/fidesr_lrrb.serialized.bin.bin"
    ),
    "vae_decoder_context": Path(
        "context/fidesr_vae_decoder/"
        "fidesr_vae_decoder.serialized.bin.bin"
    ),
    "empty_prompt_embeddings": Path(
        "models/fidesr_empty_prompt_embeds.bin"
    ),
    "epsilon_seed": Path("models/fidesr_epsilon_seed231.bin"),
}


class PhotoRestorePackageError(RuntimeError):
    """Raised when no complete FiDeSR package can be resolved."""


@dataclass(frozen=True)
class PhotoRestoreArtifacts:
    root: Path
    vae_encoder_context: Path
    unet_context: Path
    lrrb_context: Path
    vae_decoder_context: Path
    empty_prompt_embeddings: Path
    epsilon_seed: Path

    def required_files(self) -> tuple[Path, ...]:
        return (
            self.vae_encoder_context,
            self.unet_context,
            self.lrrb_context,
            self.vae_decoder_context,
            self.empty_prompt_embeddings,
            self.epsilon_seed,
        )


@dataclass(frozen=True)
class PhotoRestorePackageResolution:
    status: str
    artifacts: PhotoRestoreArtifacts | None
    searched_roots: tuple[Path, ...]
    missing_files: tuple[Path, ...] = ()
    message: str = ""

    @property
    def ready(self) -> bool:
        return self.status == "READY" and self.artifacts is not None


class PhotoRestorePackageResolver:
    """Resolve one coherent six-file FiDeSR package from approved roots."""

    def __init__(self, roots: Iterable[Path | str] | None = None) -> None:
        self._roots = self._unique_roots(
            self._default_roots() if roots is None else roots
        )

    @staticmethod
    def _default_roots() -> tuple[Path, ...]:
        # Reuse the existing model-root contract instead of introducing a
        # second preference or installation-root mechanism.
        from controllers.model_repository import ModelRepository

        roots = list(
            ModelRepository._build_installation_roots(
                None, include_configured_roots=True
            )
        )
        roots.append(config.BASE / "models")
        return tuple(roots)

    @staticmethod
    def _unique_roots(roots: Iterable[Path | str]) -> tuple[Path, ...]:
        unique: list[Path] = []
        seen: set[str] = set()
        for root in roots:
            candidate = Path(root).expanduser().resolve(strict=False)
            key = os.path.normcase(str(candidate))
            if key not in seen:
                seen.add(key)
                unique.append(candidate)
        return tuple(unique)

    @staticmethod
    def _resolve_within_root(root: Path, relative_path: Path) -> Path:
        root = root.resolve(strict=False)
        candidate = (root / relative_path).resolve(strict=False)
        try:
            candidate.relative_to(root)
        except ValueError as error:
            raise PhotoRestorePackageError(
                f"FiDeSR artifact escapes approved model root: {candidate}"
            ) from error
        return candidate

    @classmethod
    def _artifacts_for_root(cls, root: Path) -> PhotoRestoreArtifacts:
        """Resolve the established development/frozen layout."""
        paths = {
            name: cls._resolve_within_root(root, relative_path)
            for name, relative_path in FIDESR_ARTIFACT_PATHS.items()
        }
        return PhotoRestoreArtifacts(root=root, **paths)

    @classmethod
    def _artifacts_for_package_root(cls, root: Path) -> PhotoRestoreArtifacts:
        """Resolve the managed ``photo_restore`` package layout."""
        paths = {
            name: cls._resolve_within_root(root, relative_path)
            for name, relative_path in FIDESR_PACKAGE_ARTIFACT_PATHS.items()
        }
        return PhotoRestoreArtifacts(root=root, **paths)

    @classmethod
    def _candidate_artifacts_for_root(
        cls, root: Path
    ) -> tuple[PhotoRestoreArtifacts, ...]:
        managed_package = cls._resolve_within_root(root, Path("photo_restore"))
        return (
            cls._artifacts_for_package_root(managed_package),
            cls._artifacts_for_package_root(root),
            cls._artifacts_for_root(root),
        )

    def resolve(self) -> PhotoRestorePackageResolution:
        for root in self._roots:
            for artifacts in self._candidate_artifacts_for_root(root):
                required = artifacts.required_files()
                present = tuple(path for path in required if path.exists())
                if not present:
                    continue

                missing = tuple(path for path in required if not path.is_file())
                if missing:
                    return PhotoRestorePackageResolution(
                        status="NOT_READY",
                        artifacts=None,
                        searched_roots=self._roots,
                        missing_files=missing,
                        message=(
                            f"FiDeSR package is incomplete in {artifacts.root}: "
                            + ", ".join(str(path) for path in missing)
                        ),
                    )

                return PhotoRestorePackageResolution(
                    status="READY",
                    artifacts=artifacts,
                    searched_roots=self._roots,
                    message=f"FiDeSR package ready in {artifacts.root}",
                )

        return PhotoRestorePackageResolution(
            status="NOT_READY",
            artifacts=None,
            searched_roots=self._roots,
            message=(
                "FiDeSR package not found in approved model roots: "
                + ", ".join(str(root) for root in self._roots)
            ),
        )

    def require_ready(self) -> PhotoRestoreArtifacts:
        resolution = self.resolve()
        if not resolution.ready or resolution.artifacts is None:
            raise PhotoRestorePackageError(resolution.message)
        return resolution.artifacts
