from __future__ import annotations

import ast
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
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
        cls.backend_tree = ast.parse(cls.backend_text)

    @staticmethod
    def _extract_function(tree, source_text, source_path, name):
        function = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == name
        )
        namespace = {"subprocess": subprocess, "sys": __import__("sys")}
        exec(
            compile(
                ast.Module(body=[function], type_ignores=[]),
                str(source_path),
                "exec",
            ),
            namespace,
        )
        return namespace[name]

    @classmethod
    def _staging_function(cls):
        function = next(
            node for node in cls.runner_tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "prepare_qnn_input_staging"
        )
        namespace = {
            "Path": Path,
            "os": os,
            "shutil": shutil,
            "hard_stop": lambda message: (_ for _ in ()).throw(RuntimeError(message)),
        }
        exec(
            compile(
                ast.Module(body=[function], type_ignores=[]),
                str(RUNNER),
                "exec",
            ),
            namespace,
        )
        return namespace["prepare_qnn_input_staging"]

    def _assert_portable_stage(self, stage, tensor_names):
        prepare = self._staging_function()
        with tempfile.TemporaryDirectory(prefix="HK NPU STUDIO ") as temp_text:
            root = Path(temp_text)
            source_dir = root / "Source Files With Spaces"
            source_dir.mkdir()
            input_set = {}
            for index, tensor_name in enumerate(tensor_names):
                source = source_dir / f"input {index}.raw"
                source.write_bytes(bytes([index + 1]))
                input_set[tensor_name] = source

            stage_dir = root / "QNN Stage With Spaces"
            input_list = prepare(stage, [input_set], stage_dir)
            line = input_list.read_text(encoding="ascii").strip()

            self.assertEqual(len(line.split()), len(tensor_names))
            self.assertNotIn(str(root), line)
            self.assertEqual(
                [token.split(":=", 1)[0] for token in line.split()],
                list(tensor_names),
            )
            for token in line.split():
                relative = token.split(":=", 1)[1]
                self.assertFalse(Path(relative).is_absolute())
                self.assertTrue((stage_dir / relative).is_file())
            self.assertEqual(
                [(stage_dir / token.split(":=", 1)[1]).read_bytes() for token in line.split()],
                [path.read_bytes() for path in input_set.values()],
            )

    def test_space_path_encoder_inputs_are_portable_and_exact(self) -> None:
        self._assert_portable_stage("VAE_ENCODER", ("image", "epsilon"))

    def test_space_path_unet_inputs_are_portable_and_exact(self) -> None:
        self._assert_portable_stage(
            "UNET",
            ("sample", "timestep", "encoder_hidden_states"),
        )

    def test_space_path_lrrb_input_is_portable_and_exact(self) -> None:
        self._assert_portable_stage("LRRB", ("latent_cat",))

    def test_space_path_decoder_input_is_portable_and_exact(self) -> None:
        self._assert_portable_stage("VAE_DECODER", ("latent",))

    def test_path_without_spaces_remains_portable(self) -> None:
        prepare = self._staging_function()
        with tempfile.TemporaryDirectory(prefix="qnn_stage_") as temp_text:
            root = Path(temp_text)
            source = root / "sample.raw"
            source.write_bytes(b"sample")
            input_list = prepare("LRRB", [{"latent_cat": source}], root / "stage")
            self.assertEqual(
                input_list.read_text(encoding="ascii").strip().split(":=", 1)[0],
                "latent_cat",
            )

    def test_fidesr_runner_process_is_hidden_on_windows(self) -> None:
        kwargs = self._extract_function(
            self.backend_tree,
            self.backend_text,
            BACKEND,
            "_subprocess_creation_kwargs",
        )
        self.assertEqual(
            kwargs("win32"),
            {"creationflags": subprocess.CREATE_NO_WINDOW},
        )
        self.assertIn("**_subprocess_creation_kwargs()", self.backend_text)

    def test_qnn_runner_process_is_hidden_on_windows(self) -> None:
        kwargs = self._extract_function(
            self.runner_tree,
            self.runner_text,
            RUNNER,
            "_subprocess_creation_kwargs",
        )
        self.assertEqual(
            kwargs("win32"),
            {"creationflags": subprocess.CREATE_NO_WINDOW},
        )
        function = next(
            node for node in self.runner_tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "run_qnn_stage"
        )
        function_text = ast.get_source_segment(self.runner_text, function) or ""
        self.assertIn("**_subprocess_creation_kwargs()", function_text)

    def test_non_windows_subprocesses_have_no_creation_flags(self) -> None:
        for tree, source_text, source_path in (
            (self.backend_tree, self.backend_text, BACKEND),
            (self.runner_tree, self.runner_text, RUNNER),
        ):
            with self.subTest(source=source_path.name):
                kwargs = self._extract_function(
                    tree,
                    source_text,
                    source_path,
                    "_subprocess_creation_kwargs",
                )
                self.assertEqual(kwargs("linux"), {})

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
        self.assertIn('"--input_list", input_list.name', function_text)
        self.assertIn("cwd=str(input_stage)", function_text)
        self.assertIn("shutil.rmtree(input_stage, ignore_errors=True)", function_text)

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

    def test_runner_has_no_machine_specific_release_paths(self) -> None:
        self.assertNotIn(r"C:\SnapdragonAI", self.runner_text)
        self.assertNotIn(r"C:\Qualcomm\AIStack", self.runner_text)
        self.assertIn('os.environ["HK_NPU_FIDESR_ROOT"]', self.runner_text)
        self.assertIn('os.environ["HK_NPU_FIDESR_QNN_RUNNER"]', self.runner_text)
        self.assertIn(
            'os.environ["HK_NPU_FIDESR_QNN_SKELETON_DIR"]',
            self.runner_text,
        )


if __name__ == "__main__":
    unittest.main()
