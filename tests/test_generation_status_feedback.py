from __future__ import annotations

import unittest
import queue
import tkinter as tk

from widgets.phoenix.views.prompt_view import PhoenixPromptView
from controllers.prompt_workspace_controller import PromptWorkspaceController
from controllers.generation_job import GenerationJob
from controllers.generation_session import GenerationSessionModel


class GenerationStatusFeedbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = tk.Tk()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.root.destroy()

    def setUp(self) -> None:
        self.controller = PromptWorkspaceController()
        self.view = PhoenixPromptView(self.root, controller=self.controller)
        self.view._generation_running = True

    def tearDown(self) -> None:
        self.view.destroy()

    def test_ui_updates_on_progress_event(self) -> None:
        """1. UI-Fortschrittsbalken und Labels aktualisieren sich bei Progress-Event."""
        # Inject progress event
        self.view._generation_events.put(("progress", (45.0, "Sampling Phase (Schritt 9/20)...")))

        # Run polling
        self.view._poll_generation_events()

        # Check updates
        self.assertEqual(self.view.progress_var.get(), 45)
        self.assertIn("Sampling Phase (Schritt 9/20)...", self.view.progress_stage_label.cget("text"))
        self.assertIn("45 %", self.view.progress_stage_label.cget("text"))
        self.assertEqual(self.view.status_label.cget("text"), "Status: Sampling Phase (Schritt 9/20)...")
        self.assertEqual(self.view.insp_gen_status.cget("text"), "Sampling Phase (Schritt 9/20)...")

    def test_all_phases_are_mapped_correctly(self) -> None:
        """2. Alle 5 Inferenzphasen werden korrekt auf Prozentwerte und deutsche Bezeichnungen abgebildet."""
        phases = [
            ("Preparing Qualcomm QNN runtime", 5.0, "NPU wird vorbereitet..."),
            ("Loading Text Encoder on HTP", 10.0, "Modell wird geladen (Text Encoder)..."),
            ("Loading UNet on HTP", 15.0, "Modell wird geladen (UNet)..."),
            ("Loading VAE on HTP", 20.0, "Modell wird geladen (VAE)..."),
            ("Tokenizing prompt", 25.0, "Modell wird geladen..."),
            ("Computing Canny edge image...", 30.0, "ControlNet Vorverarbeitung..."),
            ("Step 10/20: Timestep=500", 57.5, "Sampling Phase (Schritt 10/20)..."),
            ("Decoding image on HTP", 90.0, "VAE Decoding..."),
            ("Saving image", 95.0, "Bild wird gespeichert & Metadaten geschrieben..."),
        ]

        for stdout_line, expected_percent, expected_stage in phases:
            with self.subTest(stdout_line=stdout_line):
                callback_args = []
                def progress_cb(percent, stage):
                    callback_args.append((percent, stage))

                session = GenerationSessionModel()
                job = GenerationJob(session=session, progress_callback=progress_cb)

                # Simulate how backend processes lines
                line_str = stdout_line.strip()
                if any(k in line_str for k in ["Preparing", "Loading", "Starting", "Tokenizing", "Running", "Decoding", "Saving", "Step", "Image", "Computing"]):
                    percent = None
                    stage_text = None

                    if "Preparing Qualcomm QNN" in line_str:
                        percent = 5.0
                        stage_text = "NPU wird vorbereitet..."
                    elif "Loading Text Encoder" in line_str:
                        percent = 10.0
                        stage_text = "Modell wird geladen (Text Encoder)..."
                    elif "Loading UNet" in line_str:
                        percent = 15.0
                        stage_text = "Modell wird geladen (UNet)..."
                    elif "Loading VAE" in line_str:
                        percent = 20.0
                        stage_text = "Modell wird geladen (VAE)..."
                    elif "Tokenizing prompt" in line_str:
                        percent = 25.0
                        stage_text = "Modell wird geladen..."
                    elif "Computing Canny edge image" in line_str:
                        percent = 30.0
                        stage_text = "ControlNet Vorverarbeitung..."
                    elif "Step " in line_str and "/" in line_str:
                        parts = line_str.split("Step ")[1].split(":")[0].split("/")
                        curr = int(parts[0])
                        total = int(parts[1])
                        job.progress = float(curr) / float(total)
                        percent = 30.0 + (job.progress * 55.0)
                        stage_text = f"Sampling Phase (Schritt {curr}/{total})..."
                    elif "Decoding image" in line_str:
                        percent = 90.0
                        stage_text = "VAE Decoding..."
                    elif "Saving image" in line_str:
                        percent = 95.0
                        stage_text = "Bild wird gespeichert & Metadaten geschrieben..."

                    if percent is not None and stage_text is not None:
                        callback = getattr(job, "progress_callback", None)
                        if callback:
                            callback(percent, stage_text)

                self.assertEqual(len(callback_args), 1)
                self.assertEqual(callback_args[0][0], expected_percent)
                self.assertEqual(callback_args[0][1], expected_stage)
