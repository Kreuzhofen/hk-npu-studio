from __future__ import annotations

import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]
RUNNER = ROOT / "engine" / "backends" / "fidesr_strong_runner_template.py"
BACKEND = ROOT / "engine" / "backends" / "fidesr_photo_restore_backend.py"


class FiDeSRSerializedContextRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner_text = RUNNER.read_text(encoding="utf-8")
        cls.backend_text = BACKEND.read_text(encoding="utf-8")
        cls.runner_tree = ast.parse(cls.runner_text)

    def test_all_four_stage_context_paths_are_exact(self) -> None:
        expected = (
            '"fidesr_vae_encoder.serialized.bin.bin"',
            '"fidesr_unet_merged.serialized.bin.bin"',
            '"fidesr_lrrb.serialized.bin.bin"',
            '"fidesr_vae_decoder.serialized.bin.bin"',
        )
        for filename in expected:
            with self.subTest(filename=filename):
                self.assertIn(filename, self.runner_text)
                self.assertIn(filename, self.backend_text)

        for stage in ("VAE_ENCODER", "UNET", "LRRB", "VAE_DECODER"):
            self.assertIn(f'"{stage}": CONTEXT_', self.runner_text)

    def test_active_stage_command_retrieves_context_without_dlc_loader(self) -> None:
        function = next(
            node for node in self.runner_tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "run_qnn_stage"
        )
        function_text = ast.get_source_segment(self.runner_text, function) or ""
        self.assertIn('"--retrieve_context", str(context)', function_text)
        self.assertNotIn("--dlc_path", function_text)
        self.assertNotIn("QnnModelDlc.dll", function_text)
        self.assertNotIn("--model", function_text)
        self.assertNotIn("perf_profile", function_text)

    def test_missing_context_and_retrieval_failure_are_explicit(self) -> None:
        self.assertIn("Serialisierter HTP-Kontext fehlt oder ist leer", self.runner_text)
        self.assertIn("Abruf/Ausführung des serialisierten", self.runner_text)
        self.assertIn("if not context.is_file() or context.stat().st_size <= 0", self.runner_text)

    def test_no_dlc_fallback_or_cpu_gpu_ai_fallback(self) -> None:
        self.assertNotIn("QNN_MODEL_DLC", self.runner_text)
        self.assertNotIn("DLC_ENCODER", self.runner_text)
        self.assertNotIn("DLC_UNET", self.runner_text)
        self.assertNotIn("DLC_LRRB", self.runner_text)
        self.assertNotIn("DLC_DECODER", self.runner_text)
        self.assertIn("CPU_AI_FALLBACK=NO", self.runner_text)
        self.assertNotIn("cuda", self.runner_text.lower())


if __name__ == "__main__":
    unittest.main()
