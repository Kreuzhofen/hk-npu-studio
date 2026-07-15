from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np

from engine.qnn_execution_probe import (
    QnnExecutionProbe,
    check_and_hash_output,
    load_production_contract,
)


class QnnExecutionProbeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_load_production_contract_missing_file_raises_error(self) -> None:
        missing_file = self.root / "nonexistent.json"
        with self.assertRaises(FileNotFoundError):
            load_production_contract(missing_file)

    def test_load_production_contract_incomplete_data_raises_error(self) -> None:
        invalid_meta = {
            "model_files": {
                "text_encoder.bin": {
                    "inputs": {"tokens": {"shape": [1, 77]}}  # missing output / dtype / scale / zero_point
                }
            }
        }
        meta_file = self.root / "metadata.json"
        meta_file.write_text(json.dumps(invalid_meta), encoding="utf-8")
        with self.assertRaises(ValueError) as ctx:
            load_production_contract(meta_file)
        self.assertIn("ungültiger produktionsvertrag", str(ctx.exception).lower())

    def test_load_production_contract_valid_metadata_succeeds(self) -> None:
        valid_meta = {
            "model_files": {
                "text_encoder.bin": {
                    "inputs": {"tokens": {"shape": [1, 77], "dtype": "int32"}},
                    "outputs": {"text_embedding": {"shape": [1, 77, 1024], "dtype": "uint16", "quantization_parameters": {"scale": 0.01, "zero_point": 100}}}
                },
                "unet.bin": {
                    "inputs": {
                        "latent": {"shape": [1, 64, 64, 4], "dtype": "uint16", "quantization_parameters": {"scale": 0.02, "zero_point": 200}},
                        "timestep": {"shape": [1, 1], "dtype": "uint16", "quantization_parameters": {"scale": 0.03, "zero_point": 300}},
                        "text_emb": {"shape": [1, 77, 1024], "dtype": "uint16", "quantization_parameters": {"scale": 0.04, "zero_point": 400}}
                    },
                    "outputs": {"output_latent": {"shape": [1, 64, 64, 4], "dtype": "uint16", "quantization_parameters": {"scale": 0.05, "zero_point": 500}}}
                },
                "vae.bin": {
                    "inputs": {"latent": {"shape": [1, 64, 64, 4], "dtype": "uint16", "quantization_parameters": {"scale": 0.06, "zero_point": 600}}},
                    "outputs": {"image": {"shape": [1, 512, 512, 3], "dtype": "uint16", "quantization_parameters": {"scale": 0.07, "zero_point": 700}}}
                }
            }
        }
        meta_file = self.root / "metadata.json"
        meta_file.write_text(json.dumps(valid_meta), encoding="utf-8")
        contract = load_production_contract(meta_file)
        self.assertEqual(contract["text_encoder"]["scale"], 0.01)
        self.assertEqual(contract["unet"]["latent_zero_point"], 200)
        self.assertEqual(contract["vae"]["output_shape"], [1, 512, 512, 3])

    def test_check_and_hash_output_valid_succeeds(self) -> None:
        arr1 = np.arange(10, dtype=np.uint16).reshape((1, 10))
        arr2 = np.arange(10, dtype=np.uint16).reshape((1, 10))
        h = check_and_hash_output("TestComp", arr1, arr2, [1, 10], "uint16")
        self.assertTrue(isinstance(h, str))
        self.assertEqual(len(h), 32)  # md5 hex string length

    def test_check_and_hash_output_shape_mismatch_raises_error(self) -> None:
        arr1 = np.arange(10, dtype=np.uint16).reshape((1, 10))
        arr2 = np.arange(10, dtype=np.uint16).reshape((1, 10))
        with self.assertRaises(ValueError) as ctx:
            check_and_hash_output("TestComp", arr1, arr2, [2, 5], "uint16")
        self.assertIn("Form-Fehler", str(ctx.exception))

    def test_check_and_hash_output_dtype_mismatch_raises_error(self) -> None:
        arr1 = np.arange(10, dtype=np.uint16).reshape((1, 10))
        arr2 = np.arange(10, dtype=np.uint16).reshape((1, 10))
        with self.assertRaises(ValueError) as ctx:
            check_and_hash_output("TestComp", arr1, arr2, [1, 10], "int32")
        self.assertIn("Datentyp-Fehler", str(ctx.exception))

    def test_check_and_hash_output_nondeterministic_raises_error(self) -> None:
        arr1 = np.arange(10, dtype=np.uint16).reshape((1, 10))
        arr2 = np.arange(10, dtype=np.uint16).reshape((1, 10))
        arr2[0, 0] = 99
        with self.assertRaises(ValueError) as ctx:
            check_and_hash_output("TestComp", arr1, arr2, [1, 10], "uint16")
        self.assertIn("Determinismus-Fehler", str(ctx.exception))

    def test_check_and_hash_output_constant_raises_error(self) -> None:
        arr1 = np.ones((1, 10), dtype=np.uint16)
        arr2 = np.ones((1, 10), dtype=np.uint16)
        with self.assertRaises(ValueError) as ctx:
            check_and_hash_output("TestComp", arr1, arr2, [1, 10], "uint16")
        self.assertIn("Ausgabe ist konstant", str(ctx.exception))

    def test_check_and_hash_output_all_zeros_raises_error(self) -> None:
        arr1 = np.zeros((1, 10), dtype=np.uint16)
        arr2 = np.zeros((1, 10), dtype=np.uint16)
        with self.assertRaises(ValueError) as ctx:
            check_and_hash_output("TestComp", arr1, arr2, [1, 10], "uint16")
        self.assertIn("Ausgabe ist komplett null", str(ctx.exception))

    def test_check_and_hash_output_contains_nans_raises_error(self) -> None:
        arr1 = np.array([[1.0, float("nan")]], dtype=np.float32)
        arr2 = np.array([[1.0, float("nan")]], dtype=np.float32)
        with self.assertRaises(ValueError) as ctx:
            check_and_hash_output("TestComp", arr1, arr2, [1, 2], "float32")
        self.assertIn("Ausgabe enthält NaNs", str(ctx.exception))


class _StrictSession:
    def get_providers(self) -> list[str]:
        return ["QNNExecutionProvider"]


class QnnQualificationGateIntegrationTests(unittest.TestCase):
    @patch("engine.qnn_package_qualification.Path.is_file")
    @patch("engine.qnn_package_qualification.open")
    def test_qualification_gate_qualified_with_valid_report(self, mock_open, mock_is_file) -> None:
        from engine.qnn_package_qualification import QnnPackageQualifier, QualificationStatus
        
        # Make all file existence checks pass
        mock_is_file.return_value = True
        package = Path(__file__).resolve().parents[1] / "models" / "stable_diffusion_v2_1"
        
        mock_report_json = {
            "success": True,
            "qualification_status": "QUALIFIED",
            "package_id": "stable_diffusion_v2_1_qnn",
            "package_path": str(package.resolve()),
            "session_verification": {
                "success": True,
                "components": {
                    "text_encoder": {"runs_ms": [10.0, 12.0], "hash": "h1", "providers": ["QNNExecutionProvider"]},
                    "unet": {"runs_ms": [20.0, 22.0], "hash": "h2", "providers": ["QNNExecutionProvider"]},
                    "vae": {"runs_ms": [30.0, 32.0], "hash": "h3", "providers": ["QNNExecutionProvider"]}
                },
                "evidence": {
                    "cpu_fallback_disabled": True
                }
            },
            "headless_generation": {
                "success": True,
                "image_path": "output/img.png",
                "image_hash": "imghash",
                "metadata": {
                    "cpu_fallback": False
                }
            },
            "memory_assessment": {
                "cpu_fallback_status": "DISABLED"
            }
        }
        
        # Mock file reading only when opening the probe report, otherwise call builtins open
        import builtins
        orig_open = builtins.open
        def open_side_effect(file_path, *args, **kwargs):
            if "qnn_execution_probe_report.json" in str(file_path):
                mock_file = MagicMock()
                mock_file.__enter__.return_value = mock_file
                mock_file.read.return_value = json.dumps(mock_report_json)
                return mock_file
            return orig_open(file_path, *args, **kwargs)
        mock_open.side_effect = open_side_effect
        
        # Create a real qualifier with a dummy loader
        qualifier = QnnPackageQualifier(strict_loader=lambda _path, _name: _StrictSession())
        res = qualifier.qualify(package, strict=True, probe_report="C:/SnapdragonAI/temp/r006/qnn_execution_probe_report.json")
        self.assertEqual(res["qualification_status"], QualificationStatus.QUALIFIED.value)
        self.assertTrue(res["evidence"]["qnn_execution_performed"])
        self.assertTrue(res["evidence"]["htp_inference_proven"])

    def test_qualification_gate_conditionally_qualified_without_report(self) -> None:
        from engine.qnn_package_qualification import QnnPackageQualifier, QualificationStatus
        qualifier = QnnPackageQualifier(strict_loader=lambda _path, _name: _StrictSession())
        package = Path(__file__).resolve().parents[1] / "models" / "stable_diffusion_v2_1"
        
        # Scenario A: probe_report is None
        res_none = qualifier.qualify(package, strict=True, probe_report=None)
        self.assertEqual(res_none["qualification_status"], QualificationStatus.CONDITIONALLY_QUALIFIED.value)
        
        # Scenario B: probe_report is not None but file does not exist
        res_missing = qualifier.qualify(package, strict=True, probe_report="nonexistent_report.json")
        self.assertEqual(res_missing["qualification_status"], QualificationStatus.CONDITIONALLY_QUALIFIED.value)

    @patch("engine.qnn_package_qualification.Path.is_file")
    @patch("engine.qnn_package_qualification.open")
    def test_qualification_gate_conditionally_qualified_with_mismatching_report(self, mock_open, mock_is_file) -> None:
        from engine.qnn_package_qualification import QnnPackageQualifier, QualificationStatus
        
        mock_is_file.return_value = True
        package = Path(__file__).resolve().parents[1] / "models" / "stable_diffusion_v2_1"
        
        # Wrong package_id or package_path
        mock_report_json = {
            "success": True,
            "qualification_status": "QUALIFIED",
            "package_id": "wrong_id_qnn",
            "package_path": str(package.resolve()),
            "session_verification": {
                "success": True,
                "components": {
                    "text_encoder": {"runs_ms": [10.0, 12.0], "hash": "h1", "providers": ["QNNExecutionProvider"]},
                    "unet": {"runs_ms": [20.0, 22.0], "hash": "h2", "providers": ["QNNExecutionProvider"]},
                    "vae": {"runs_ms": [30.0, 32.0], "hash": "h3", "providers": ["QNNExecutionProvider"]}
                },
                "evidence": {
                    "cpu_fallback_disabled": True
                }
            },
            "headless_generation": {
                "success": True,
                "image_path": "output/img.png",
                "image_hash": "imghash",
                "metadata": {
                    "cpu_fallback": False
                }
            },
            "memory_assessment": {
                "cpu_fallback_status": "DISABLED"
            }
        }
        
        import builtins
        orig_open = builtins.open
        def open_side_effect(file_path, *args, **kwargs):
            if "qnn_execution_probe_report.json" in str(file_path):
                mock_file = MagicMock()
                mock_file.__enter__.return_value = mock_file
                mock_file.read.return_value = json.dumps(mock_report_json)
                return mock_file
            return orig_open(file_path, *args, **kwargs)
        mock_open.side_effect = open_side_effect
        
        qualifier = QnnPackageQualifier(strict_loader=lambda _path, _name: _StrictSession())
        res = qualifier.qualify(package, strict=True, probe_report="C:/SnapdragonAI/temp/r006/qnn_execution_probe_report.json")
        self.assertEqual(res["qualification_status"], QualificationStatus.CONDITIONALLY_QUALIFIED.value)

    @patch("engine.qnn_package_qualification.Path.is_file")
    @patch("engine.qnn_package_qualification.open")
    def test_qualification_gate_conditionally_qualified_with_incomplete_report(self, mock_open, mock_is_file) -> None:
        from engine.qnn_package_qualification import QnnPackageQualifier, QualificationStatus
        
        mock_is_file.return_value = True
        package = Path(__file__).resolve().parents[1] / "models" / "stable_diffusion_v2_1"
        
        # Missing UNet in components verification
        mock_report_json = {
            "success": True,
            "qualification_status": "QUALIFIED",
            "package_id": "stable_diffusion_v2_1_qnn",
            "package_path": str(package.resolve()),
            "session_verification": {
                "success": True,
                "components": {
                    "text_encoder": {"runs_ms": [10.0, 12.0], "hash": "h1", "providers": ["QNNExecutionProvider"]},
                    "vae": {"runs_ms": [30.0, 32.0], "hash": "h3", "providers": ["QNNExecutionProvider"]}
                },
                "evidence": {
                    "cpu_fallback_disabled": True
                }
            },
            "headless_generation": {
                "success": True,
                "image_path": "output/img.png",
                "image_hash": "imghash",
                "metadata": {
                    "cpu_fallback": False
                }
            },
            "memory_assessment": {
                "cpu_fallback_status": "DISABLED"
            }
        }
        
        import builtins
        orig_open = builtins.open
        def open_side_effect(file_path, *args, **kwargs):
            if "qnn_execution_probe_report.json" in str(file_path):
                mock_file = MagicMock()
                mock_file.__enter__.return_value = mock_file
                mock_file.read.return_value = json.dumps(mock_report_json)
                return mock_file
            return orig_open(file_path, *args, **kwargs)
        mock_open.side_effect = open_side_effect
        
        qualifier = QnnPackageQualifier(strict_loader=lambda _path, _name: _StrictSession())
        res = qualifier.qualify(package, strict=True, probe_report="C:/SnapdragonAI/temp/r006/qnn_execution_probe_report.json")
        self.assertEqual(res["qualification_status"], QualificationStatus.CONDITIONALLY_QUALIFIED.value)


if __name__ == "__main__":
    unittest.main()
