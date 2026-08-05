from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from controllers.generation_job import GenerationJob
from controllers.generation_session import GenerationSessionModel
from engine.sd15_qnn_backend import StableDiffusion15QnnBackend
from engine.sd21_qnn_backend import StableDiffusion21QnnBackend
from engine.controlnet_canny_backend import ControlNetCannyQnnBackend
import gui_v2

class FrozenQnnWorkerFixTests(unittest.TestCase):

    def test_sd15_cmd_frozen_correct(self):
        backend = StableDiffusion15QnnBackend()
        session = GenerationSessionModel(model_name="stable_diffusion_v1_5_qnn")
        job = GenerationJob(session=session)
        
        with patch("sys.frozen", True, create=True), \
             patch("sys.executable", "SnapdragonAIStudio.exe"), \
             patch("subprocess.Popen") as mock_popen:
            
            # Mock process
            mock_proc = MagicMock()
            mock_proc.stdout.readline.return_value = ""
            mock_proc.poll.return_value = 0
            mock_popen.return_value = mock_proc
            
            # Mock output file check to exit early
            with patch("pathlib.Path.exists", return_value=True), \
                 patch("builtins.open", unittest.mock.mock_open(read_data='{"success": true}')):
                backend.generate(job)
            
            # Verify command spawned
            called_cmd = mock_popen.call_args[0][0]
            self.assertEqual(called_cmd[0], "SnapdragonAIStudio.exe")
            self.assertEqual(called_cmd[1], "--qnn-worker")
            self.assertEqual(called_cmd[2], "sd15")

    def test_sd21_cmd_frozen_correct(self):
        backend = StableDiffusion21QnnBackend()
        session = GenerationSessionModel(model_name="stable_diffusion_v2_1_qnn")
        job = GenerationJob(session=session)
        
        with patch("sys.frozen", True, create=True), \
             patch("sys.executable", "SnapdragonAIStudio.exe"), \
             patch("subprocess.Popen") as mock_popen:
            
            # Mock process
            mock_proc = MagicMock()
            mock_proc.stdout.readline.return_value = ""
            mock_proc.poll.return_value = 0
            mock_popen.return_value = mock_proc
            
            with patch("pathlib.Path.exists", return_value=True), \
                 patch("builtins.open", unittest.mock.mock_open(read_data='{"success": true}')):
                backend.generate(job)
            
            called_cmd = mock_popen.call_args[0][0]
            self.assertEqual(called_cmd[0], "SnapdragonAIStudio.exe")
            self.assertEqual(called_cmd[1], "--qnn-worker")
            self.assertEqual(called_cmd[2], "sd21")

    def test_controlnet_cmd_frozen_correct(self):
        backend = ControlNetCannyQnnBackend()
        session = GenerationSessionModel(model_name="controlnet_canny_qnn")
        job = GenerationJob(session=session)
        
        with patch("sys.frozen", True, create=True), \
             patch("sys.executable", "SnapdragonAIStudio.exe"), \
             patch("subprocess.Popen") as mock_popen:
            
            # Mock process
            mock_proc = MagicMock()
            mock_proc.stdout.readline.return_value = ""
            mock_proc.poll.return_value = 0
            mock_popen.return_value = mock_proc
            
            with patch("pathlib.Path.exists", return_value=True), \
                 patch("builtins.open", unittest.mock.mock_open(read_data='{"success": true}')):
                backend.generate(job)
            
            called_cmd = mock_popen.call_args[0][0]
            self.assertEqual(called_cmd[0], "SnapdragonAIStudio.exe")
            self.assertEqual(called_cmd[1], "--qnn-worker")
            self.assertEqual(called_cmd[2], "controlnet-canny")

    def test_gui_worker_mode_runs_physical_backend(self):
        # Test that --qnn-worker flag runs backend, doesn't start GUI, and returns correct exit code
        with patch("sys.argv", ["gui_v2.py", "--qnn-worker", "sd15", "input.json", "output.json"]), \
             patch("builtins.open", unittest.mock.mock_open(read_data='{"prompt": "test"}')), \
             patch("json.load", return_value={"prompt": "test"}), \
             patch("json.dump") as mock_dump, \
             patch("engine.sd15_qnn_backend.StableDiffusion15QnnBackend._execute_generation_physical") as mock_physical, \
             patch("gui_v2.SnapdragonAIStudioV2") as mock_gui:
            
            mock_physical.return_value = {"success": True, "message": "Success"}
            
            exit_code = gui_v2.main()
            
            # Verify exit_code is 0 (success)
            self.assertEqual(exit_code, 0)
            # Verify GUI was NOT instantiated
            mock_gui.assert_not_called()
            # Verify physical execution called
            mock_physical.assert_called_once_with({"prompt": "test"})
            # Verify output json written
            self.assertTrue(mock_dump.called)

    def test_gui_worker_mode_returns_1_on_failure(self):
        with patch("sys.argv", ["gui_v2.py", "--qnn-worker", "sd15", "input.json", "output.json"]), \
             patch("builtins.open", unittest.mock.mock_open(read_data='{"prompt": "test"}')), \
             patch("json.load", return_value={"prompt": "test"}), \
             patch("json.dump") as mock_dump, \
             patch("engine.sd15_qnn_backend.StableDiffusion15QnnBackend._execute_generation_physical") as mock_physical:
            
            mock_physical.return_value = {"success": False, "message": "Failed"}
            
            exit_code = gui_v2.main()
            
            self.assertEqual(exit_code, 1)
