import sys
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile

# Add project path to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from controllers.package_status import PackageStatus
from controllers.model_repository import ModelRepository
from engine.release_config import RELEASE
from widgets.phoenix.views.prompt_view import PhoenixPromptView


class TestRC2AFixes(unittest.TestCase):
    """Focused tests for the three release candidate 2A fixes."""

    def test_fix1_sd35_validation_absent_invalid_ready(self):
        """Verify the 3 scenarios of SD3.5 installation state verification."""
        repo = ModelRepository()

        # Mock MODELS_DIR to point to a temporary test directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            sd35_dir = temp_path / "stable_diffusion_v3_5_qai"

            # 1. ABSENT TEST: Folder does not exist
            with patch("config.MODELS_DIR", temp_path):
                status = repo.get_package_status("stable_diffusion_v3_5_qai")
                self.assertEqual(status, PackageStatus.NOT_INSTALLED)

            # 1b. ABSENT TEST: Folder exists but is empty
            sd35_dir.mkdir(parents=True, exist_ok=True)
            with patch("config.MODELS_DIR", temp_path):
                status = repo.get_package_status("stable_diffusion_v3_5_qai")
                self.assertEqual(status, PackageStatus.NOT_INSTALLED)

            # 2. INVALID TEST: Folder exists and has files, but validation fails
            dummy_file = sd35_dir / "some_artifact.bin"
            dummy_file.write_bytes(b"dummy_data")

            # Mock validate_installation to return invalid
            with patch("config.MODELS_DIR", temp_path), \
                 patch.object(repo.registry, "validate_installation") as mock_validate:
                mock_result = MagicMock()
                mock_result.valid = False
                mock_validate.return_value = mock_result

                status = repo.get_package_status("stable_diffusion_v3_5_qai")
                self.assertEqual(status, PackageStatus.INVALID)

            # 3. READY TEST: Folder exists and validation succeeds
            with patch("config.MODELS_DIR", temp_path), \
                 patch.object(repo.registry, "validate_installation") as mock_validate:
                mock_result = MagicMock()
                mock_result.valid = True
                mock_validate.return_value = mock_result

                status = repo.get_package_status("stable_diffusion_v3_5_qai")
                # When validation succeeds, it checks package.json; since it doesn't exist, it falls back to INSTALLED
                self.assertEqual(status, PackageStatus.INSTALLED)

    def test_fix2_version_unification_rc2a(self):
        """Verify that the central release version is exactly '2.0 RC2A'."""
        self.assertEqual(RELEASE.display_version, "2.0 RC2A")
        self.assertEqual(RELEASE.package_version, "2.0.0-rc.2a")

    def test_fix3_phoenix_boost_close_behavior(self):
        """Verify that Qwen installation success closes the active Boost preview window."""
        # Create a mock PromptView
        prompt_view = MagicMock(spec=PhoenixPromptView)

        class MockBoostPopup:
            def __init__(self):
                self.destroyed = False

            def winfo_exists(self):
                return not self.destroyed

            def destroy(self):
                self.destroyed = True

        popup = MockBoostPopup()
        prompt_view._boost_popup = popup

        # Call the actual success callback logic
        with patch("engine.ollama_status.OllamaStatusService.invalidate_cache"), \
             patch("engine.ollama_status.OllamaStatusService.detect"):
            PhoenixPromptView._on_qwen_installed_success(prompt_view)

        # Verify the boost popup was destroyed and reference cleared
        self.assertTrue(popup.destroyed)
        self.assertIsNone(prompt_view._boost_popup)


if __name__ == "__main__":
    unittest.main()
