from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import numpy as np
from PIL import Image

from controllers.generation_job import GenerationJob
from controllers.generation_pipeline import ImageGenerationPipeline
from controllers.generation_result import GenerationResult
from controllers.generation_session import GenerationSessionModel
from engine.phoenix_boost_quality import PhoenixBoostQualityPass


def _fixture_image(width: int = 96, height: int = 80) -> Image.Image:
    y, x = np.mgrid[0:height, 0:width]
    base = 48.0 + x * 1.45 + y * 0.55
    texture = 10.0 * np.sin(x / 2.7) * np.cos(y / 3.1)
    rgb = np.stack((base + texture, base * 0.94 + texture, base * 0.88 + texture), axis=2)
    return Image.fromarray(np.clip(np.rint(rgb), 0, 255).astype(np.uint8), "RGB")


def _detail_energy(image: Image.Image) -> float:
    luminance = np.asarray(image.convert("L"), dtype=np.float32)
    laplacian = -4.0 * luminance[1:-1, 1:-1]
    laplacian += (
        luminance[:-2, 1:-1]
        + luminance[2:, 1:-1]
        + luminance[1:-1, :-2]
        + luminance[1:-1, 2:]
    )
    return float(np.mean(np.abs(laplacian)))


class PhoenixBoostQualityTests(unittest.TestCase):
    def test_profiles_are_limited_and_medium_aware(self) -> None:
        cases = {
            "A landscape photo": "PHOTO",
            "A woman in a photo studio, realistic photo": "PORTRAIT_PHOTO",
            "Mona Lisa, Renaissance painting": "ART_PAINTING",
            "A red abstract form": "GENERAL",
        }
        self.assertEqual(
            {PhoenixBoostQualityPass.classify(prompt) for prompt in cases},
            {"PHOTO", "PORTRAIT_PHOTO", "ART_PAINTING", "GENERAL"},
        )
        for prompt, expected in cases.items():
            self.assertEqual(PhoenixBoostQualityPass.classify(prompt), expected)

    def test_quality_pass_preserves_geometry_color_and_increases_detail(self) -> None:
        raw = _fixture_image()
        result = PhoenixBoostQualityPass.apply(raw.copy(), "A portrait photo of a woman")
        self.assertEqual(result.image.size, raw.size)
        self.assertEqual(result.image.mode, raw.mode)
        self.assertNotEqual(result.boosted_sha256, result.raw_sha256)
        self.assertGreater(_detail_energy(result.image), _detail_energy(raw) * 1.01)
        raw_array = np.asarray(raw, dtype=np.float32)
        output_array = np.asarray(result.image, dtype=np.float32)
        channel_drift = np.abs(
            output_array.mean(axis=(0, 1)) - raw_array.mean(axis=(0, 1))
        )
        self.assertLess(float(channel_drift.max()), 0.75)

    def test_alpha_is_preserved_exactly(self) -> None:
        raw = _fixture_image().convert("RGBA")
        alpha = Image.fromarray(
            np.arange(raw.width * raw.height, dtype=np.uint8).reshape(raw.height, raw.width)
        )
        raw.putalpha(alpha)
        result = PhoenixBoostQualityPass.apply(raw, "Mona Lisa, Renaissance painting")
        self.assertEqual(result.image.getchannel("A").tobytes(), alpha.tobytes())

    def test_pipeline_uses_identical_worker_conditioning_and_raw_hash(self) -> None:
        common = dict(
            prompt="A woman in a photo studio, realistic photo, sharp focus",
            negative_prompt="blur",
            model_name="stable_diffusion_v3_5_qai",
            width=96,
            height=80,
            steps=8,
            cfg_scale=4.5,
            seed=1234,
            sampler="Euler",
            scheduler="Normal",
        )
        off = GenerationJob(GenerationSessionModel(**common, phoenix_boost_enabled=False))
        on = GenerationJob(GenerationSessionModel(**common, phoenix_boost_enabled=True))
        self.assertEqual(
            off.parameters.to_worker_dict("same"),
            on.parameters.to_worker_dict("same"),
        )

        with tempfile.TemporaryDirectory() as directory:
            raw = _fixture_image()
            raw_hash = PhoenixBoostQualityPass.pixel_sha256(raw)
            off_path = Path(directory) / "off.png"
            on_path = Path(directory) / "on.png"
            raw.save(off_path)
            raw.save(on_path)
            ImageGenerationPipeline(off, object()).finish(
                GenerationResult(True, "FINISHED", "ok", image_path=str(off_path))
            )
            on_result = ImageGenerationPipeline(on, object()).finish(
                GenerationResult(True, "FINISHED", "ok", image_path=str(on_path))
            )
            with Image.open(off_path) as off_image, Image.open(on_path) as on_image:
                self.assertEqual(PhoenixBoostQualityPass.pixel_sha256(off_image), raw_hash)
                self.assertEqual(on_result.metadata["phoenix_boost_raw_sha256"], raw_hash)
                self.assertNotEqual(PhoenixBoostQualityPass.pixel_sha256(on_image), raw_hash)
                self.assertEqual(off_image.size, on_image.size)

    def test_sd_model_matrix_has_no_conditioning_drift(self) -> None:
        for model in (
            "stable_diffusion_v3_5_qai",
            "stable_diffusion_v2_5_qnn",
            "stable_diffusion_v1_5_qnn",
        ):
            with self.subTest(model=model):
                off = GenerationJob(GenerationSessionModel(prompt="unchanged", model_name=model))
                on = GenerationJob(
                    GenerationSessionModel(
                        prompt="unchanged",
                        model_name=model,
                        phoenix_boost_enabled=True,
                    )
                )
                self.assertEqual(
                    off.parameters.to_worker_dict("job"),
                    on.parameters.to_worker_dict("job"),
                )


if __name__ == "__main__":
    unittest.main()
