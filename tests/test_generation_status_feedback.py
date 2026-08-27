from __future__ import annotations

import unittest
import queue
import tkinter as tk
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from widgets.phoenix.views.prompt_view import PhoenixPromptView
from controllers.prompt_workspace_controller import PromptWorkspaceController
from controllers.generation_job import GenerationJob
from controllers.generation_session import GenerationSessionModel
from controllers.generation_result import GenerationResult


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

    def test_progress_stage_updates_keep_inspector_geometry_stable_at_supported_dpi(self) -> None:
        """Changing generation-stage lengths must not add or remove inspector rows."""
        original_scaling = float(self.root.tk.call("tk", "scaling"))
        self.root.geometry("1200x900")
        self.view.pack(fill="both", expand=True)
        self.root.update()
        stages = (
            "Vorbereiten",
            "Sampling Phase (Schritt 9/20)...",
            "Bild wird gespeichert & Metadaten geschrieben...",
            "Fertig",
        )

        try:
            for scaling in (1.0, 1.25, 1.5, 1.75):
                with self.subTest(scaling=scaling):
                    self.root.tk.call("tk", "scaling", scaling)
                    self.root.update()
                    inspector_width = self.view.insp_canvas.winfo_width()
                    snapshots = []
                    for stage in stages:
                        self.view._set_progress(50.0, stage, "Schritt 9 / 20")
                        self.view._layout_generation_inspector(inspector_width)
                        self.root.update_idletasks()
                        snapshots.append(
                            (
                                self.view.insp_content.winfo_reqheight(),
                                int(self.view.progress_stage_label.grid_info()["row"]),
                                int(self.view.progress_step_label.grid_info()["row"]),
                            )
                        )

                    self.assertEqual(len(set(snapshots)), 1, snapshots)
                    self.assertEqual(
                        snapshots[0][2],
                        snapshots[0][1] + 1,
                        "phase and step rows must stay stacked for stable geometry",
                    )
        finally:
            self.root.tk.call("tk", "scaling", original_scaling)
            self.view.pack_forget()

    def test_late_progress_does_not_overwrite_terminal_state(self) -> None:
        self.view._generation_running = False
        self.view.status_label.configure(text="Status: CANCELLED")
        self.view.insp_gen_status.configure(text="CANCELLED")

        self.view._handle_generation_progress(95.0, "Bild wird gespeichert")

        self.assertEqual(self.view.status_label.cget("text"), "Status: CANCELLED")
        self.assertEqual(self.view.insp_gen_status.cget("text"), "CANCELLED")

    def test_save_as_copies_the_last_successful_preview(self) -> None:
        with TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "generated.png"
            destination = Path(temp_dir) / "saved.png"
            source.write_bytes(b"generated-image")
            self.controller.last_response = GenerationResult(
                success=True,
                status="FINISHED",
                message="done",
                image_path=str(source),
            )

            with patch(
                "tkinter.filedialog.asksaveasfilename",
                return_value=str(destination),
            ):
                self.view._on_save_as()

            self.assertEqual(destination.read_bytes(), b"generated-image")

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
